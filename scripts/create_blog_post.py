#!/usr/bin/env python3
"""
GuideCraft — Shopify Blog Post Creator
Inspects existing blog structure, then creates one SEO-optimised article
via the Shopify Admin REST API. Uses the cached OAuth token from the
previous auth flow. Never prints secrets.
"""

import os
import sys
import json
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
TOKEN_CACHE_FILE = Path(__file__).parent.parent / ".shopify_token"

load_dotenv(ENV_FILE)

SHOP        = os.environ.get("SHOPIFY_SHOP", "").strip()
CLIENT_ID   = os.environ.get("SHOPIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()
API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "").strip()

if SHOP and not SHOP.endswith(".myshopify.com"):
    SHOP = SHOP + ".myshopify.com"

OAUTH_PORT     = 3456
OAUTH_REDIRECT = f"http://localhost:{OAUTH_PORT}/callback"
OAUTH_SCOPES   = "write_content,read_content,write_products,read_products"

# ── Blog post content ─────────────────────────────────────────────────────────

ARTICLE_TITLE  = "Practical Wellness Guides for Real Women: Simple Support for Health, Fitness & Everyday Life"
ARTICLE_HANDLE = "practical-wellness-guides-for-women"
ARTICLE_AUTHOR = "GuideCraft"
SEO_TITLE      = "Practical Wellness Guides for Women & Moms | GuideCraft"
SEO_DESCRIPTION = (
    "Discover practical downloadable wellness guides for women and moms. "
    "GuideCraft offers simple PDF guides for health, fitness, menopause, "
    "nutrition, and real-life self-improvement."
)

ARTICLE_BODY_HTML = """
<p>If you're a woman in your 30s, 40s, 50s, or 60s, you already know the feeling: you open your browser to search for something simple — like how to eat better or manage the discomfort of changing hormones — and suddenly you're drowning in conflicting advice, expensive programmes, and articles that leave you more confused than when you started.</p>

<p>You're not looking for a complete lifestyle overhaul. You're looking for something practical. Something that works in your actual life — between the school run, the work meetings, the appointments, and the quiet moments you finally get to yourself.</p>

<p>That's what GuideCraft is built for.</p>

<h2>Why Wellness Information Can Feel So Overwhelming</h2>

<p>The internet is full of wellness content. But most of it falls into one of two camps: either it's so basic it tells you nothing new, or it's so complex that following it feels like a part-time job.</p>

<p>Real wellness — the kind that actually fits into your life — is neither of those things. It's clear, actionable, and written for women who have other things going on. You don't need another 300-page book or a 12-week programme with a weekly live call. You need a guide you can open, read, and use.</p>

<h2>Menopause and Hormonal Changes: Getting the Information You Deserve</h2>

<p>For many women between 40 and 60, navigating perimenopause and menopause brings a new set of questions. Sleep changes. Energy shifts. Body composition feels different. And finding straightforward, reassuring information — without scaremongering or oversimplified advice — can be surprisingly hard.</p>

<p>A good wellness guide won't diagnose or prescribe. But it can explain what's commonly experienced, what lifestyle factors are worth exploring, and what questions might be worth raising with your healthcare provider. That kind of clarity matters — and it shouldn't be hard to find.</p>

<h2>Fitness That Fits Your Real Life</h2>

<p>Fitness content is often aimed at people with unlimited time, unlimited energy, and a burning desire to spend it at the gym. Most women over 30 don't fit that description — and they shouldn't have to.</p>

<p>Sustainable fitness habits look different for everyone. For some women, it's building consistency with short daily movement. For others, it's understanding how to make strength work alongside a demanding schedule. The best fitness guidance meets you where you are — not where a personal trainer assumes you should be.</p>

<p>Practical guides focused on fitness for real women tend to start from that premise. Not "how to get results fast," but "how to build habits that actually last."</p>

<h2>Nutrition: Simple, Sustainable, and Free from Fads</h2>

<p>Nutrition advice online tends to swing between extremes. Keto. Intermittent fasting. "Eat this, never eat that." It's exhausting — and for most women, none of it sticks long-term.</p>

<p>What tends to be more useful is simpler than any trend: understanding the basics of nourishing your body, getting enough protein and variety, and building habits around food that feel sustainable rather than punishing. No miracle foods. No calorie obsession. Just clear, evidence-informed guidance you can apply to your actual meals, in your actual kitchen.</p>

<h2>Why a Good PDF Guide Can Be More Useful Than Hours of Searching</h2>

<p>There's a reason a well-written guide — even a short one — can be more useful than an evening of Googling. A guide is curated. Someone has already done the work of filtering out the noise, organising the information, and presenting it in a way that makes sense.</p>

<p>GuideCraft PDF guides are designed with exactly that in mind. Each one is concise, clearly structured, and written in plain English — so you can pick it up, understand it, and actually use it. No jargon. No filler. Just practical information, presented in a way that respects your time and intelligence.</p>

<p>Because they're digital downloads, there's no waiting. You can be reading within minutes of purchase, and you'll have your guide to return to whenever you need it — on your phone, tablet, or laptop.</p>

<h2>Where to Start</h2>

<p>GuideCraft guides cover a range of topics relevant to women navigating health and wellness in their 30s, 40s, 50s, and beyond — from menopause support to fitness, nutrition, and everyday self-improvement.</p>

<p>If you're not sure where to begin, the best place is simply to <a href="/collections/all">browse all available guides</a> and see what speaks to where you are right now. There's no pressure and no subscription — just practical resources you download and keep.</p>

<p>Wellness doesn't have to be complicated. Sometimes, the most helpful thing you can do is find one good guide — and start there.</p>
""".strip()

# ── Auth ──────────────────────────────────────────────────────────────────────

def try_client_credentials():
    resp = requests.post(
        f"https://{SHOP}/admin/oauth/access_token",
        json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
              "grant_type": "client_credentials"},
        timeout=15,
    )
    if resp.status_code == 200:
        data = resp.json()
        if "access_token" in data:
            return data["access_token"]
    # 4xx = not supported / not installed — fall through to code flow
    return None


def oauth_authorization_code_flow():
    state = secrets.token_urlsafe(16)
    auth_url = (
        f"https://{SHOP}/admin/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&scope={urllib.parse.quote(OAUTH_SCOPES)}"
        f"&redirect_uri={urllib.parse.quote(OAUTH_REDIRECT, safe='')}"
        f"&state={state}"
        f"&grant_options[]=offline"
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

    print(f"\n  Opening browser for Shopify authorisation…")
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
        f"https://{SHOP}/admin/oauth/access_token",
        json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code},
        timeout=15,
    )
    if resp.status_code != 200 or "access_token" not in resp.json():
        print(f"ERROR: Token exchange failed — {resp.status_code}")
        sys.exit(1)

    token = resp.json()["access_token"]
    TOKEN_CACHE_FILE.write_text(token)
    print("  Token cached for future runs.")
    return token


def get_access_token():
    token = try_client_credentials()
    if token:
        print("  Auth: client_credentials  ✓")
        return token
    if TOKEN_CACHE_FILE.exists():
        cached = TOKEN_CACHE_FILE.read_text().strip()
        if cached:
            print("  Auth: cached token  ✓")
            return cached
    print("  Auth: launching OAuth flow…")
    return oauth_authorization_code_flow()

# ── REST helper ───────────────────────────────────────────────────────────────

def rest(method, path, token, payload=None):
    url = f"https://{SHOP}/admin/api/{API_VERSION}{path}"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": token,
    }
    resp = requests.request(method, url, headers=headers,
                            json=payload, timeout=30)
    if resp.status_code == 401:
        if TOKEN_CACHE_FILE.exists():
            TOKEN_CACHE_FILE.unlink()
        print("ERROR: 401 — token rejected. Cache cleared. Re-run to re-authorise.")
        sys.exit(1)
    if resp.status_code == 403:
        body = resp.text
        if "read_content" in body or "write_content" in body or "content scope" in body.lower():
            print("ERROR: 403 — missing content scopes.\n")
            print("  The app needs 'read_content' and 'write_content' added to its")
            print("  Admin API scopes in the Shopify Partners Dashboard:\n")
            print("  Partners Dashboard → Your App → Configuration → Admin API scopes")
            print("  → add read_content and write_content → Save")
            print("\n  Then re-run this script — no reinstall needed.")
        else:
            print(f"ERROR: 403 Forbidden\n  {body[:400]}")
        sys.exit(1)
    if resp.status_code not in (200, 201):
        print(f"ERROR: HTTP {resp.status_code}\n{resp.text[:600]}")
        sys.exit(1)
    return resp.json()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("  GuideCraft — Shopify Blog Post Creator")
    print("=" * 62)
    print()

    # Env check
    missing = [n for n, v in [("SHOPIFY_SHOP", SHOP), ("SHOPIFY_CLIENT_ID", CLIENT_ID),
                               ("SHOPIFY_CLIENT_SECRET", CLIENT_SECRET),
                               ("SHOPIFY_API_VERSION", API_VERSION)] if not v]
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    masked = CLIENT_ID[:6] + "…" if len(CLIENT_ID) > 6 else "***"
    print(f"  SHOPIFY_SHOP        = {SHOP}")
    print(f"  SHOPIFY_CLIENT_ID   = {masked}")
    print(f"  SHOPIFY_API_VERSION = {API_VERSION}")
    print()

    token = get_access_token()
    print()

    # ── 1. Inspect blog structure ────────────────────────────────
    print("── Inspecting blog structure… " + "─" * 31)
    blogs_data = rest("GET", "/blogs.json", token)
    blogs = blogs_data.get("blogs", [])

    if not blogs:
        print("  No blogs found. Creating a 'News' blog first…")
        new_blog = rest("POST", "/blogs.json", token,
                        {"blog": {"title": "News", "commentable": "no"}})
        blog = new_blog["blog"]
        print(f"  Created blog: '{blog['title']}' (id={blog['id']})")
    else:
        # Prefer a blog named 'News' or 'Blog'; fall back to the first one
        blog = next(
            (b for b in blogs if b["title"].lower() in ("news", "blog", "wellness")),
            blogs[0]
        )
        print(f"  Found {len(blogs)} blog(s). Using: '{blog['title']}' (id={blog['id']})")

    blog_id     = blog["id"]
    blog_handle = blog["handle"]
    print()

    # ── 2. Check for duplicate handle ────────────────────────────
    print("── Checking for existing article with same handle… " + "─" * 9)
    existing = rest("GET", f"/blogs/{blog_id}/articles.json?handle={ARTICLE_HANDLE}", token)
    articles = existing.get("articles", [])
    if articles:
        a = articles[0]
        print(f"  Article already exists: id={a['id']}  handle={a['handle']}")
        print(f"  URL: https://{SHOP}/blogs/{blog_handle}/{a['handle']}")
        print("  Nothing to do — article already published.")
        return
    print("  No duplicate found. Proceeding…")
    print()

    # ── 3. Create the article ────────────────────────────────────
    print("── Creating blog post… " + "─" * 38)
    payload = {
        "article": {
            "title":      ARTICLE_TITLE,
            "author":     ARTICLE_AUTHOR,
            "body_html":  ARTICLE_BODY_HTML,
            "handle":     ARTICLE_HANDLE,
            "published":  True,
            "metafields": [
                {
                    "key":       "title_tag",
                    "value":     SEO_TITLE,
                    "namespace": "global",
                    "type":      "single_line_text_field",
                },
                {
                    "key":       "description_tag",
                    "value":     SEO_DESCRIPTION,
                    "namespace": "global",
                    "type":      "single_line_text_field",
                },
            ],
        }
    }

    result  = rest("POST", f"/blogs/{blog_id}/articles.json", token, payload)
    article = result["article"]
    art_id  = article["id"]
    art_handle = article["handle"]

    print(f"  Article created:  id={art_id}")
    print()

    # ── 4. Confirm ───────────────────────────────────────────────
    print("── Confirming published article… " + "─" * 28)
    confirm  = rest("GET", f"/blogs/{blog_id}/articles/{art_id}.json", token)
    a        = confirm["article"]

    live_url = f"https://{SHOP}/blogs/{blog_handle}/{a['handle']}"

    print(f"  Title:      {a['title']}")
    print(f"  Handle:     {a['handle']}")
    print(f"  Author:     {a['author']}")
    print(f"  Published:  {a['published_at']}")
    print(f"  Blog:       {blog['title']}")
    print(f"  URL:        {live_url}")
    print()
    print("Done.")
    print()
    print("=" * 62)
    print(f"  Live URL: {live_url}")
    print("=" * 62)


if __name__ == "__main__":
    main()
