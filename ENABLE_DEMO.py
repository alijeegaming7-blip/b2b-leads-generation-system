#!/usr/bin/env python3
"""
ENABLE DEMO MODE
================
Run this to give a client a trial demo with blurred contacts.

Usage:
    python ENABLE_DEMO.py
    python ENABLE_DEMO.py --buy-link "https://wa.me/923001234567?text=Buy+Prospex" --price "$500" --name "Your Name"

Then share:  http://YOUR_SERVER_IP:3000
"""
import json, argparse, os

CONFIG = os.path.join(os.path.dirname(__file__), "apps", "api-python", "demo_config.json")

parser = argparse.ArgumentParser()
parser.add_argument("--buy-link", default="", help="WhatsApp or payment link for buy button")
parser.add_argument("--price",    default="$500", help="Price shown on buy button")
parser.add_argument("--name",     default="", help="Your name/business name")
args = parser.parse_args()

# Read existing config
try:
    with open(CONFIG) as f:
        cfg = json.load(f)
except Exception:
    cfg = {}

# Update
cfg["demo_mode"] = True
if args.buy_link: cfg["demo_buy_link"]    = args.buy_link
if args.price:    cfg["demo_price"]       = args.price
if args.name:     cfg["demo_contact_name"]= args.name

with open(CONFIG, "w") as f:
    json.dump(cfg, f, indent=2)

print("=" * 55)
print("  ✅  DEMO MODE ENABLED")
print("=" * 55)
print(f"  Buy link : {cfg.get('demo_buy_link','(not set)')}")
print(f"  Price    : {cfg.get('demo_price','')}")
print(f"  Seller   : {cfg.get('demo_contact_name','')}")
print()
print("  What the client sees:")
print("  • Real leads from Google Maps ✓")
print("  • Phone numbers BLURRED ✗")
print("  • Emails BLURRED ✗")
print("  • Social media HIDDEN ✗")
print("  • All other connectors LOCKED ✗")
print("  • Purple banner + Buy button at top ✓")
print()
print("  Share this link:  http://localhost:3000")
print("  (or your server IP if hosted)")
print()
print("  To revert:  python DISABLE_DEMO.py")
print("=" * 55)
