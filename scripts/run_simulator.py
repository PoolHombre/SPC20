#!/usr/bin/env python3
"""Run the SPC 2.0 logger in simulator mode against the real Supabase endpoint.

Usage:
    SIM_SCENARIO=green python scripts/run_simulator.py
    SIM_SCENARIO=red_loss_of_prime python scripts/run_simulator.py

Scenarios: green | yellow_filter | red_loss_of_prime | red_no_flow |
           fault_under | fault_over | invalid_p3_p2
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("SENSOR_ADAPTER", "simulator")

from src.logger import run

if __name__ == "__main__":
    run()
