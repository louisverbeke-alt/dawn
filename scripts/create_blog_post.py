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

ARTICLE_TITLE  = "What No One Tells You About the Menopause Experience — And How to Feel Strong Through It"
ARTICLE_HANDLE = "menopause-experience-symptoms-what-to-expect"
ARTICLE_AUTHOR = "GuideCraft"
ARTICLE_TAGS   = "menopause, perimenopause, women over 40, strength training, women's wellness, menopause symptoms"
SEO_TITLE      = "What No One Tells You About the Menopause Experience"
SEO_DESCRIPTION = (
    "Going through menopause and not sure what to expect? Discover common symptoms, "
    "energy shifts, and simple steps to feel strong and like yourself again."
)

ARTICLE_BODY_HTML = """
<p>If you have recently found yourself wondering why you feel so different — exhausted some days, wide awake at 3am on others, or just not quite like yourself — you are not imagining it. The menopause experience is real, and for many women it arrives quietly before they even realise what is happening. You do not have to figure this out alone, and you do not have to simply push through.</p>

<h2>Why the Menopause Experience Feels So Unexpected</h2>

<p>Most women grow up hearing very little about menopause. When it arrives — often in your 40s or early 50s — it can feel like your body has changed the rules without warning you first.</p>

<p>The truth is, menopause is a natural life stage, not a breakdown. Your body is going through a significant hormonal shift, and every system notices it. Sleep, energy, mood, metabolism, and joints are all connected to the hormones that are gradually changing.</p>

<p>Perimenopause — the years leading up to your final period — is usually where symptoms first appear. This phase can last anywhere from a few years to over a decade. Knowing that it has a name, and has support, can make it feel far less frightening.</p>

<h2>The Most Common Menopause Symptoms Women Describe</h2>

<p>No two women experience menopause exactly the same way. Some sail through with mild changes. Others find it genuinely disruptive. Both experiences are valid.</p>

<p>The most frequently reported menopause symptoms include:</p>

<ul>
<li>Hot flashes and night sweats — sudden waves of heat that can strike at any time</li>
<li>Sleep problems — difficulty falling asleep, waking frequently, or feeling unrefreshed</li>
<li>Mood changes — irritability, low mood, anxiety, or feeling emotionally flat</li>
<li>Brain fog — forgetting words, struggling to concentrate, feeling mentally slower</li>
<li>Joint aches and stiffness — especially in the morning</li>
<li>Changes in weight and body shape — particularly around the midsection</li>
<li>Low energy — a bone-deep tiredness that rest does not always fix</li>
</ul>

<p>If you recognise yourself in that list, you are far from alone. Always talk to your doctor about symptoms that are affecting your daily life — they have more options available than ever before.</p>

<h2>What Menopause Does to Your Energy and Sleep</h2>

<p>One of the things women mention most is how much perimenopause and menopause disrupts sleep. Night sweats can wake you repeatedly. Hormonal shifts can make your brain feel alert at midnight and foggy by noon.</p>

<p>Poor sleep then affects everything else — your patience, your mood, your motivation to move. It is a cycle that can feel hard to break.</p>

<p>A few things many women find helpful:</p>

<ul>
<li>Keeping your bedroom cool and well-ventilated at night</li>
<li>Reducing caffeine and alcohol, especially after midday</li>
<li>Creating a gentle, consistent wind-down routine before bed</li>
<li>Getting morning light, which helps regulate your body clock</li>
</ul>

<p>These are not miracle fixes. They are small, honest shifts that build a steadier foundation over time.</p>

<h2>How Strength Training Supports You Through Menopause</h2>

<p>Here is something that surprises many women: strength training is one of the most practical choices you can make during menopause.</p>

<p>As oestrogen levels decline, your body loses muscle mass more quickly and bone density becomes more important. Building and maintaining muscle helps protect your bones, supports your metabolism, lifts your mood, and gives you back a real sense of control in your body.</p>

<p>You do not need to become a gym regular or lift heavy weights. Resistance-based movement — using your bodyweight, light dumbbells, or resistance bands — done consistently two to three times a week is enough to make a meaningful difference to how you feel.</p>

<p>Start exactly where you are, not where you think you should be. The best workout is always the one you will actually do.</p>

<h2>Simple Daily Habits That Support Your Body Right Now</h2>

<p>Your daily habits have more impact than most people realise during menopause.</p>

<p>Eat enough protein. Protein protects muscle mass, keeps energy steady, and helps you feel satisfied after meals. Include a source — eggs, fish, chicken, beans, or Greek yoghurt — at every meal.</p>

<p>Stay hydrated. Hormonal changes affect how your body regulates temperature and fluid. Drinking enough water throughout the day supports your energy, skin, and focus.</p>

<p>Manage stress where you can. High cortisol can make menopause symptoms feel worse. Even ten minutes of quiet — a walk, deep breathing, or time without your phone — helps your nervous system settle.</p>

<p>Talk to other women. Connecting with others who understand what you are going through is genuinely supportive. You are not the only one navigating this season.</p>

<h2>You Are Not Losing Yourself — You Are Changing</h2>

<p>The menopause experience is not always easy, and it is okay to say that. But it is also not the end of energy, vitality, or feeling good in your body. Many women describe the years after menopause as a time when they feel clearer, more confident, and more grounded than ever before.</p>

<p>You get to decide how you move through this season. With the right information and a little practical support, you can do it feeling strong.</p>

<h2>Get Practical Support</h2>

<p>If you want practical, step-by-step support for exactly this, <a href="https://guidecrafted.com/products/the-menopause-strength-blueprint">The Menopause Strength Blueprint</a> was created for women navigating perimenopause, menopause, and life after 40. It covers strength training, nutrition, bone health, energy, and daily habits designed to help you feel stronger and more in control — without overwhelm.</p>

<p>👉 <a href="https://guidecrafted.com/products/the-menopause-strength-blueprint"><strong>Get The Menopause Strength Blueprint here</strong></a></p>
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


def get_access_token(force_reauth: bool = False):
    if not force_reauth:
        token = try_client_credentials()
        if token:
            print("  Auth: client_credentials  ✓")
            return token
        if TOKEN_CACHE_FILE.exists():
            cached = TOKEN_CACHE_FILE.read_text().strip()
            if cached:
                print("  Auth: cached token  ✓")
                return cached
    else:
        print("  Auth: --reauth flag set, clearing cache and running OAuth flow…")
        if TOKEN_CACHE_FILE.exists():
            TOKEN_CACHE_FILE.unlink()
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
    force_reauth = "--reauth" in sys.argv

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

    token = get_access_token(force_reauth=force_reauth)
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
        # Prefer Wellness Blog, then News, then any blog
        blog = next(
            (b for b in blogs if b["title"].lower() == "wellness blog"),
            next(
                (b for b in blogs if b["title"].lower() in ("news", "blog")),
                blogs[0]
            )
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
        print(f"  URL: https://guidecrafted.com/blogs/{blog_handle}/{a['handle']}")
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
            "tags":       ARTICLE_TAGS,
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

    live_url = f"https://guidecrafted.com/blogs/{blog_handle}/{a['handle']}"

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
