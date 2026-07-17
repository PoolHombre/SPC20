import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "x-device-id, x-device-token, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  // --- Auth ---
  const deviceId = req.headers.get("x-device-id");
  const deviceToken = req.headers.get("x-device-token");

  if (!deviceId || !deviceToken) {
    return new Response(JSON.stringify({ error: "missing device credentials" }), {
      status: 401,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  // Validate device token (compare hash)
  const { data: device, error: deviceErr } = await supabase
    .from("devices")
    .select("id, pool_id, active, device_token_hash")
    .eq("id", deviceId)
    .single();

  if (deviceErr || !device || !device.active) {
    return new Response(JSON.stringify({ error: "device not found or inactive" }), {
      status: 403,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  // Hash the submitted token and compare
  const encoder = new TextEncoder();
  const tokenBytes = encoder.encode(deviceToken);
  const hashBuffer = await crypto.subtle.digest("SHA-256", tokenBytes);
  const hashHex = Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  if (hashHex !== device.device_token_hash) {
    return new Response(JSON.stringify({ error: "invalid token" }), {
      status: 403,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  // --- Parse payload ---
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: "invalid JSON" }), {
      status: 400,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  // --- Upsert reading ---
  const reading = {
    device_id: deviceId,
    observed_at: body.observed_at,
    pump_running: body.pump_running,
    p1_suction_psi_avg: body.p1_suction_psi_avg,
    p1_suction_psi_min: body.p1_suction_psi_min,
    p1_suction_psi_max: body.p1_suction_psi_max,
    p2_filter_inlet_psi_avg: body.p2_filter_inlet_psi_avg,
    p2_filter_inlet_psi_min: body.p2_filter_inlet_psi_min,
    p2_filter_inlet_psi_max: body.p2_filter_inlet_psi_max,
    p3_filter_outlet_psi_avg: body.p3_filter_outlet_psi_avg,
    p3_filter_outlet_psi_min: body.p3_filter_outlet_psi_min,
    p3_filter_outlet_psi_max: body.p3_filter_outlet_psi_max,
    filter_dp_psi_avg: body.filter_dp_psi_avg,
    flow_gpm_avg: body.flow_gpm_avg,
    flow_gpm_min: body.flow_gpm_min,
    flow_gpm_max: body.flow_gpm_max,
    flow_gpm_stddev: body.flow_gpm_stddev,
    samples: body.samples,
    raw: { raw_ma: body.raw_ma, quality: body.quality },
    trial_phase: body.trial_phase ?? null,
    trial_run_id: body.trial_run_id ?? null,
    filter_dp_psi_raw: body.filter_dp_psi_raw ?? null,
    filter_dp_psi_corrected: body.filter_dp_psi_corrected ?? null,
    flow_near_zero_count: body.flow_near_zero_count ?? null,
  };

  const { error: insertErr } = await supabase
    .from("readings_1min")
    .upsert(reading, { onConflict: "device_id,observed_at" });

  if (insertErr) {
    console.error("Insert error:", insertErr);
    return new Response(JSON.stringify({ error: "db insert failed", detail: insertErr.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  // --- Evaluate route status ---
  // Fetch device config for heuristic thresholds
  const { data: cfg } = await supabase
    .from("device_configs")
    .select("*")
    .eq("device_id", deviceId)
    .single();

  // required_flow_gpm lives on the pool, not device_configs —
  // device_configs.flow_min_gpm is the sensor range minimum (0), not a dispatch threshold
  const { data: pool } = await supabase
    .from("pools")
    .select("required_flow_gpm")
    .eq("id", device.pool_id)
    .single();

  const status = evaluateStatus(body, cfg, pool);

  await supabase.from("route_status_current").upsert({
    pool_id: device.pool_id,
    device_id: deviceId,
    dispatch_status: status.status,
    dispatch_action: status.action,
    reason: status.reason,
    summary: status.summary,
    confidence: status.confidence,
    evidence: status.evidence,
    updated_at: new Date().toISOString(),
  }, { onConflict: "pool_id" });

  return new Response(JSON.stringify({ ok: true, status: status.status }), {
    status: 200,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
});

// Simplified heuristic mirror of Python heuristics.py
function evaluateStatus(body: Record<string, unknown>, cfg: Record<string, unknown> | null, pool: Record<string, unknown> | null) {
  const pump = body.pump_running as boolean;
  const flowAvg = (body.flow_gpm_avg as number) ?? 0;
  const flowStddev = (body.flow_gpm_stddev as number) ?? 0;
  const p2 = (body.p2_filter_inlet_psi_avg as number) ?? 0;
  const p3 = (body.p3_filter_outlet_psi_avg as number) ?? 0;
  const dp = (body.filter_dp_psi_avg as number) ?? 0;
  const quality = (body as Record<string, unknown>).quality as Record<string, string> ?? {};

  const reqFlow = Number(pool?.required_flow_gpm) || 300;
  const lowFlowPct = (cfg?.low_flow_red_threshold_percent as number) ?? 20;
  const svcDp = (cfg?.filter_service_dp_psi as number) ?? 12;
  const cleanDp = (cfg?.filter_clean_dp_psi as number) ?? 5;
  const normalMin = reqFlow * 0.9;

  const minFlow = reqFlow * (lowFlowPct / 100);
  const faulted = Object.entries(quality).filter(([, q]) => q !== "GOOD").map(([k]) => k);

  if (faulted.length > 0 && pump) {
    return { status: "RED", action: "SEND_NOW", reason: "SENSOR_FAULT_CANNOT_VERIFY_CIRCULATION", summary: `Sensor fault: ${faulted.join(", ")}`, confidence: 1, evidence: { faulted } };
  }
  if (pump && p2 > 0 && p3 >= p2) {
    return { status: "RED", action: "SEND_NOW", reason: "INVALID_PRESSURE_RELATIONSHIP", summary: `P3 (${p3}) >= P2 (${p2})`, confidence: 1, evidence: { p2, p3 } };
  }
  if (pump && flowAvg < minFlow) {
    if (flowStddev > 10 || (flowAvg > 0 && flowStddev / Math.max(flowAvg, 0.1) > 0.3)) {
      return { status: "RED", action: "SEND_NOW", reason: "LOW_WATER_LOSING_PRIME", summary: `Pulsing flow avg=${flowAvg.toFixed(0)} GPM`, confidence: 1, evidence: { flowAvg, flowStddev } };
    }
    return { status: "RED", action: "SEND_NOW", reason: "NO_FLOW_PUMP_ON", summary: `No flow: avg=${flowAvg.toFixed(0)} GPM`, confidence: 1, evidence: { flowAvg } };
  }
  if (dp >= svcDp) {
    return { status: "YELLOW", action: "ROUTE_TODAY", reason: "FILTER_SERVICE_WITHIN_24_HOURS", summary: `Filter DP=${dp.toFixed(1)} PSI at service threshold`, confidence: 1, evidence: { dp } };
  }
  if (dp >= cleanDp * 1.5) {
    return { status: "YELLOW", action: "ROUTE_TODAY", reason: "FILTER_LOADING_HIGH", summary: `Filter DP=${dp.toFixed(1)} PSI elevated`, confidence: 0.9, evidence: { dp } };
  }
  if (pump && flowAvg < normalMin) {
    return { status: "YELLOW", action: "ROUTE_TODAY", reason: "FLOW_TREND_DECLINING", summary: `Flow ${flowAvg.toFixed(0)} GPM below normal minimum`, confidence: 0.8, evidence: { flowAvg } };
  }
  return { status: "GREEN", action: "NO_VISIT", reason: "ALL_NORMAL", summary: "All parameters normal. No visit needed.", confidence: 1, evidence: { flowAvg, dp } };
}
