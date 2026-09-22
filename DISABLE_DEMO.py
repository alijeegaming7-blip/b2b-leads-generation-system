#!/usr/bin/env python3
"""
DISABLE DEMO MODE — Restore full system
=======================================
Run this after client buys OR to switch back to full mode.

Usage:
    python DISABLE_DEMO.py
"""
import json, os

CONFIG = os.path.join(os.path.dirname(__file__), "apps", "api-python", "demo_config.json")

try:
    with open(CONFIG) as f:
        cfg = json.load(f)
except Exception:
    cfg = {}

cfg["demo_mode"] = False

with open(CONFIG, "w") as f:
    json.dump(cfg, f, indent=2)

print("=" * 55)
print("  ✅  FULL MODE RESTORED")
print("=" * 55)
print()
print("  All features unlocked:")
print("  • Phone numbers visible ✓")
print("  • Emails visible ✓")
print("  • Social media visible ✓")
print("  • All connectors available ✓")
print("  • Demo banner removed ✓")
print()
print("  No restart needed — change is instant.")
print("=" * 55)
