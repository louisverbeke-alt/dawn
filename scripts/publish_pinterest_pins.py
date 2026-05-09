#!/usr/bin/env python3
"""
GuideCraft — Pinterest Pin Publisher
Authenticates via Pinterest OAuth and publishes a batch of pins to a board.
Run:         python3 scripts/publish_pinterest_pins.py
Re-auth:     python3 scripts/publish_pinterest_pins.py --reauth
"""

import os
import sys
import json
import base64
import secrets
import threading
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

try:
    from dotenv import load_dotenv
    import requests
except ImportError:
    print("ERROR: pip3 install requests python-dotenv")
    sys.exit(1)

# ── Credentials ───────────────────────────────────────────────────────────────

ENV_FILE         = Path(__file__).parent.parent / ".env"
TOKEN_CACHE_FILE = Path(__file__).parent.parent / ".pinterest_token"

load_dotenv(ENV_FILE)

APP_ID     = os.environ.get("PINTEREST_APP_ID", "").strip()
APP_SECRET = os.environ.get("PINTEREST_APP_SECRET", "").strip()

OAUTH_PORT     = 3456
OAUTH_REDIRECT = f"http://localhost:{OAUTH_PORT}/callback"
OAUTH_SCOPES   = "pins:read,pins:write,boards:read,boards:write,user_accounts:read"

# ── Board ─────────────────────────────────────────────────────────────────────
# Script will find this board if it exists, or create it if not.

BOARD_NAME = "Menopause & Women's Wellness"

# ── Pins ──────────────────────────────────────────────────────────────────────
# image_url: must be a publicly accessible image URL (ideal size: 1000x1500 px).
# Leave image_url as "" to skip that pin — fill it in and re-run when ready.

PINS = [
    {
        "title": "Feeling Tired and Out of Shape During Menopause? This Helps.",
        "description": (
            "Menopause changes everything — your energy, your body, your motivation. "
            "The Menopause Strength Blueprint is a practical PDF guide designed to help "
            "women over 40 build strength, feel more like themselves again, and take back "
            "control of their health. No gym required. Download it today at guidecrafted.com"
        ),
        "link": "https://guidecrafted.com/products/the-menopause-strength-blueprint",
        "image_url": "",
    },
    {
        "title": "Menopause Fitness Guide for Women Over 40 — Strength Training PDF",
        "description": (
            "Looking for a simple, realistic fitness guide made for women going through "
            "menopause? The Menopause Strength Blueprint covers strength training, nutrition "
            "basics, and daily habits — all written in plain language for real women with "
            "real lives. Grab your copy at guidecrafted.com"
        ),
        "link": "https://guidecrafted.com/products/the-menopause-strength-blueprint",
        "image_url": "",
    },
    {
        "title": "You're Not Lazy. Your Body Is Changing. Here's What Actually Helps.",
        "description": (
            "If you've been pushing yourself but not seeing results, menopause might be the "
            "reason — not a lack of effort. The Menopause Strength Blueprint is a no-nonsense "
            "PDF guide that explains what's happening in your body and gives you a practical "
            "plan to feel stronger and more energised. guidecrafted.com"
        ),
        "link": "https://guidecrafted.com/products/the-menopause-strength-blueprint",
        "image_url": "",
    },
    {
        "title": "5 Things Every Woman Should Know About Strength Training in Menopause",
        "description": (
            "Strength training during menopause looks different — and that's OK. Our "
            "downloadable Menopause Strength Blueprint walks you through exactly how to move, "
            "eat, and recover in a way that works with your body, not against it. Simple steps. "
            "Real results. Download at guidecrafted.com"
        ),
        "link": "https://guidecrafted.com/products/the-menopause-strength-blueprint",
        "image_url": "",
    },
    {
        "title": "Strong After 40: A PDF Guide Built for Women in Menopause",
        "description": (
            "Menopause is not the end of feeling strong — it's a reset. The Menopause "
            "Strength Blueprint is a practical, downloadable guide for women who want to "
            "build real strength, support their body through the transition, and feel "
            "confident in their skin again. Get your copy at guidecrafted.com"
        ),
        "link": "https://guidecrafted.com/products/the-menopause-strength-blueprint",
        "image_url": "",
    },
]

# ── Auth ──────────────────────────────────────────────────────────────────────

def _basic_auth_header():
    encoded = base64.b64encode(f"{APP_ID}:{APP_SECRET}".encode()).decode()
    return f"Basic {encoded}"


def _oauth_flow():
    state = secrets.token_urlsafe(16)
    auth_url = (
        "https://www.pinterest.com/oauth/"
        f"?client_id={APP_ID}"
        f"&redirect_uri={urllib.parse.quote(OAUTH_REDIRECT, safe='')}"
        f"&response_type=code"
        f"&scope={urllib.parse.quote(OAUTH_SCOPES)}"
        f"&state={state}"
    )

    received: dict = {}
    ready = threading.Event()

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            received.update(dict(urllib.parse.parse_qsl(
                urllib.parse.urlparse(self.path).query)))
            body = b"<html><body><h2>Authorised. You can close this tab.</h2></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            ready.set()
        def log_message(self, *_): pass

    server = HTTPServer(("127.0.0.1", OAUTH_PORT), _Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    print(f"\n  Opening browser for Pinterest authorisation…")
    print(f"  If it doesn't open automatically, visit:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    if not ready.wait(timeout=120):
        print("ERROR: Timed out waiting for OAuth callback.")
        sys.exit(1)
    if received.get("state") != state:
        print("ERROR: State mismatch — aborting.")
        sys.exit(1)

    code = received.get("code")
    resp = requests.post(
        "https://api.pinterest.com/v5/oauth/token",
        headers={
            "Authorization": _basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OAUTH_REDIRECT,
        },
        timeout=15,
    )
    if resp.status_code != 200 or "access_token" not in resp.json():
        print(f"ERROR: Token exchange failed — {resp.status_code}\n{resp.text[:400]}")
        sys.exit(1)

    data = resp.json()
    TOKEN_CACHE_FILE.write_text(json.dumps(data))
    print("  Token cached for future runs.")
    return data["access_token"]


def get_access_token(force_reauth=False):
    if not force_reauth and TOKEN_CACHE_FILE.exists():
        try:
            data = json.loads(TOKEN_CACHE_FILE.read_text())
            token = data.get("access_token", "")
            if token:
                print("  Auth: cached token  ✓")
                return token
        except Exception:
            pass
    if force_reauth:
        print("  Auth: --reauth flag set, clearing cache…")
        TOKEN_CACHE_FILE.unlink(missing_ok=True)
    print("  Auth: launching OAuth flow…")
    return _oauth_flow()

# ── API helper ────────────────────────────────────────────────────────────────

def api(method, path, token, payload=None, params=None):
    url = f"https://api.pinterest.com/v5{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.request(method, url, headers=headers,
                            json=payload, params=params, timeout=30)
    if resp.status_code == 401:
        TOKEN_CACHE_FILE.unlink(missing_ok=True)
        print("ERROR: 401 — token rejected. Cache cleared. Re-run to re-authorise.")
        sys.exit(1)
    if resp.status_code not in (200, 201):
        print(f"ERROR: HTTP {resp.status_code}\n{resp.text[:600]}")
        sys.exit(1)
    return resp.json()

# ── Board helpers ─────────────────────────────────────────────────────────────

def get_or_create_board(token, name):
    data = api("GET", "/boards", token, params={"page_size": 100})
    for board in data.get("items", []):
        if board["name"].lower() == name.lower():
            print(f"  Found existing board: '{board['name']}' (id={board['id']})")
            return board["id"]
    print(f"  Board '{name}' not found — creating…")
    board = api("POST", "/boards", token, {"name": name, "privacy": "PUBLIC"})
    print(f"  Created board: '{board['name']}' (id={board['id']})")
    return board["id"]

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    force_reauth = "--reauth" in sys.argv

    print("=" * 62)
    print("  GuideCraft — Pinterest Pin Publisher")
    print("=" * 62)
    print()

    if not APP_ID or not APP_SECRET:
        print("ERROR: Missing PINTEREST_APP_ID or PINTEREST_APP_SECRET in .env")
        print()
        print("  Add these two lines to your .env file:")
        print("  PINTEREST_APP_ID=your_app_id_here")
        print("  PINTEREST_APP_SECRET=your_app_secret_here")
        print()
        print("  Get them from: https://developers.pinterest.com/apps/")
        sys.exit(1)

    masked = APP_ID[:6] + "…" if len(APP_ID) > 6 else "***"
    print(f"  PINTEREST_APP_ID = {masked}")
    print()

    token = get_access_token(force_reauth=force_reauth)
    print()

    print("── Getting board… " + "─" * 44)
    board_id = get_or_create_board(token, BOARD_NAME)
    print()

    publishable = [p for p in PINS if p["image_url"]]
    skippable   = [p for p in PINS if not p["image_url"]]

    if not publishable:
        print("  No pins have an image_url set — nothing to publish.")
        print()
        print("  Add a public image URL to each pin's image_url field")
        print("  in this script, then re-run.")
        print()
        print("  Ideal image size: 1000 x 1500 px (vertical)")
        sys.exit(0)

    print(f"── Publishing {len(publishable)} pin(s)… " + "─" * 35)
    published = 0
    for i, pin in enumerate(PINS, 1):
        if not pin["image_url"]:
            print(f"  Pin {i}: SKIPPED — no image_url")
            continue

        payload = {
            "board_id": board_id,
            "title": pin["title"],
            "description": pin["description"],
            "link": pin["link"],
            "media_source": {
                "source_type": "image_url",
                "url": pin["image_url"],
            },
        }
        result = api("POST", "/pins", token, payload)
        short_title = pin["title"][:55] + ("…" if len(pin["title"]) > 55 else "")
        print(f"  Pin {i}: published  id={result['id']}")
        print(f"         '{short_title}'")
        published += 1

    print()
    print("=" * 62)
    print(f"  Done.  Published: {published}  Skipped (no image): {len(skippable)}")
    print("=" * 62)

    if skippable:
        print()
        print(f"  {len(skippable)} pin(s) were skipped because image_url is empty.")
        print("  Add public image URLs to the PINS list in this script")
        print("  and re-run — already-published pins won't be duplicated")
        print("  (Pinterest deduplication is handled on your end by tracking")
        print("   which pins you've already published).")


if __name__ == "__main__":
    main()
