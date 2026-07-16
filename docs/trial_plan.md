# SPC 2.0 — 14-Day Pilot Trial Plan

## Overview

The pilot runs one SPC 2.0 device on one pool for 14 calendar days. The goal is to generate enough data to evaluate whether the GREEN/YELLOW/RED dispatch signal is accurate, actionable, and worth deploying at scale.

The pilot is not a production rollout. Dispatch decisions during the pilot are still made by the technician based on their own observation. The SPC 2.0 signal is recorded and compared against the technician's observation after the fact.

---

## Objectives

1. Validate that sensor readings are accurate and stable under real field conditions.
2. Validate that the GREEN/YELLOW/RED heuristic produces the correct dispatch classification for observed conditions.
3. Measure false positive rate (RED/YELLOW when technician finds the pool healthy) and false negative rate (GREEN when the pool has a problem).
4. Identify thresholds that need site-specific tuning.
5. Collect baseline data for one pool to establish normal operating ranges.
6. Confirm uptime and connectivity reliability (target: >95% data completeness over 14 days).

---

## Go / No-Go Criteria Before Trial Start

All of the following must be met before the 14-day clock starts:

- [ ] Bench acceptance test: all 17 tests PASS
- [ ] Field installation checklist: all items checked
- [ ] 24-hour soak complete with no data gaps and GREEN status as expected
- [ ] Supabase `readings_1min` receiving data continuously
- [ ] Site owner briefed
- [ ] Technician observer identified and briefed on logging procedure (see Daily Check-In below)

---

## Pilot Site Selection Criteria

The ideal pilot pool for initial validation:
- A pool the technician visits at least twice per week (more data correlation opportunities)
- A pool with a known, stable, healthy system (establishes GREEN baseline)
- A pool that has had at least one filter service or pump issue in the past 6 months (realistic chance of catching a YELLOW or RED during the trial)
- Located within reasonable distance for daily check-in during the first week

---

## Data Collection

### Automated (continuous)
- `readings_1min` table: one row per minute, ~20,000 rows over 14 days
- `route_status_current`: updated each minute with current dispatch status
- `status_events`: records status transitions (GREEN→YELLOW, YELLOW→RED, etc.)

### Manual (technician observation log)
At every site visit and once per day if no visit, the assigned technician records:

| Field | Notes |
|-------|-------|
| Date and time | |
| SPC 2.0 dispatch status at time of visit | Read from Supabase or logger log |
| Technician's own assessment (Healthy / Needs Attention / Problem) | Independent of SPC 2.0 |
| Observations | Pressure gauge readings, flow feel, filter condition, water level |
| Action taken | None / Backwash / Vacuum / Chemical / Other |
| Did the SPC 2.0 status match the observed condition? | Yes / No / Partial |
| If no: what was different? | Free text |

Template is in `docs/trial_plan.md` Appendix A.

---

## Daily Check-In Process

**Week 1 (Days 1–7): Daily remote review**
- Kevin or assigned staff reviews Supabase dashboard every morning
- Checks: data continuity (no gaps), status distribution (all GREEN expected on a healthy pool), any anomalies
- Notes any status changes and correlates with known pool conditions

**Week 2 (Days 8–14): Every-other-day review**
- Same process, reduced frequency if Week 1 is stable

**On any RED alert:**
- Notify the technician immediately
- Technician visits within 4 hours and records independent observation
- Document outcome in the false-positive/negative log (see below)

---

## Threshold Tuning Approach

Default thresholds are set for a generic 50,000-gallon commercial pool. The pilot pool will likely require tuning. The process:

1. Run the pilot for 3 full days without touching thresholds.
2. Review `flow_gpm_avg` distribution. The normal band (`normal_flow_gpm_min` to `normal_flow_gpm_max`) should contain >95% of pump-on readings.
3. If the flow readings cluster outside the default band (280–380 GPM), adjust `normal_flow_gpm_min`, `normal_flow_gpm_max`, and `required_flow_gpm` in `device_configs` to match the actual pump curve for this site.
4. Review `filter_dp_psi_avg` trend over the first 7 days. If the clean baseline DP is not near 5 PSI, adjust `filter_clean_dp_psi` accordingly.
5. Document every threshold change in the trial log with the reason and the before/after values.

---

## False Positive / False Negative Log

Maintain this log for every case where SPC 2.0 status diverged from technician observation.

| Date | SPC Status | Technician Finding | Classification | Probable Cause | Threshold Adjustment Made |
|------|-----------|-------------------|----------------|---------------|--------------------------|
| | | | FP / FN / TP / TN | | |

Definitions:
- **True Positive (TP):** SPC said RED/YELLOW, technician confirmed problem. 
- **True Negative (TN):** SPC said GREEN, technician confirmed healthy.
- **False Positive (FP):** SPC said RED/YELLOW, pool was fine. Counts against dispatch credibility.
- **False Negative (FN):** SPC said GREEN, pool had a problem. The most dangerous outcome.

---

## Exit Criteria

The pilot is considered successful if, over days 4–14 (after initial threshold tuning):
- Data completeness >= 95% (no more than 72 minutes of missing data per day)
- True Positive + True Negative rate >= 80% of correlated events
- Zero false negatives for RED-class conditions (no missed pump failures or no-flow events)
- False positive rate < 20% (no more than 1-in-5 YELLOW/RED alerts is a false alarm)

If exit criteria are not met, the pilot extends by 7 days with revised thresholds.

---

## Pilot Report Template Outline

The pilot report is produced at day 14 and covers:

1. **Executive Summary** — pass/fail against exit criteria, recommendation for scale-up or further tuning
2. **Data Completeness** — uptime %, gaps, causes
3. **Status Distribution** — % time in GREEN/YELLOW/RED
4. **Threshold Tuning Log** — all changes made and rationale
5. **Correlated Events Table** — every technician visit with TP/TN/FP/FN classification
6. **False Positive/Negative Analysis** — root causes and proposed fixes
7. **Recommended Changes** — threshold adjustments, heuristic logic changes, hardware changes
8. **Go / No-Go for Fleet Deployment** — recommendation with conditions

---

## Appendix A: Daily Technician Observation Form

```
Date: ___________     Time: ___________
Site: ___________     Device ID: ___________

SPC 2.0 Status at time of visit: [GREEN / YELLOW / RED]
SPC 2.0 Reason code: ___________

Technician's independent assessment:
  Pool circulating normally?          [ ] Yes  [ ] No
  Visible flow/suction issues?        [ ] Yes  [ ] No — describe: ___________
  Filter pressure reading (gauge):    ___ PSI inlet  ___ PSI outlet
  Water level: [ ] Normal  [ ] Low  [ ] Very Low
  Pump sound: [ ] Normal  [ ] Cavitating  [ ] Other: ___________
  Chemical / clarity: [ ] Normal  [ ] Issue: ___________

Action taken: ___________

SPC 2.0 status match?  [ ] Yes (TP/TN)  [ ] No — classification: [ ] FP  [ ] FN
If no, describe discrepancy: ___________

Signature: ___________
```
