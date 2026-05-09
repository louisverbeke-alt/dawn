#!/usr/bin/env python3
"""
GuideCraft — Shopify Product SEO Updater
Authenticates via Dev Dashboard (Partners) app credentials using the
OAuth client_credentials grant. Falls back to the authorization code
flow (one-time browser prompt) if the store does not permit client
credentials, and caches the resulting token in .shopify_token.

Security: CLIENT_SECRET and access tokens are never printed.
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

OAUTH_PORT        = 3456
OAUTH_REDIRECT    = f"http://localhost:{OAUTH_PORT}/callback"
OAUTH_SCOPES      = "write_products,read_products"

# ── SEO target values ─────────────────────────────────────────────────────────

PRODUCT_TITLE = "The GLP-1 Companion: Nutrition & Muscle Retention Guide"
NEW_SEO_TITLE = "GLP-1 Nutrition & Muscle Retention Guide | GuideCraft"
NEW_SEO_DESC  = (
    "Practical PDF guide for women on GLP-1 medication. Covers nutrition strategies, "
    "protein intake, and how to protect muscle while losing weight. Instant download."
)
NEW_ALT_TEXT  = (
    "The GLP-1 Companion nutrition and muscle retention guide cover "
    "— downloadable PDF for women | GuideCraft"
)

# ── GraphQL ───────────────────────────────────────────────────────────────────

QUERY_PRODUCT = """
query GetProduct($query: String!) {
  products(first: 5, query: $query) {
    edges {
      node {
        id
        title
        seo { title description }
        images(first: 1) {
          edges {
            node { id altText url }
          }
        }
      }
    }
  }
}
"""

MUTATION_UPDATE_SEO = """
mutation UpdateProductSeo($id: ID!, $seoTitle: String!, $seoDescription: String!) {
  productUpdate(input: {
    id: $id
    seo: { title: $seoTitle description: $seoDescription }
  }) {
    product {
      id
      seo { title description }
    }
    userErrors { field message }
  }
}
"""

MUTATION_UPDATE_IMAGE_ALT = """
mutation UpdateImageAlt($productId: ID!, $imageId: ID!, $altText: String!) {
  productImageUpdate(productId: $productId, image: { id: $imageId, altText: $altText }) {
    image { id altText }
    userErrors { field message }
  }
}
"""

# ── Auth: client credentials ──────────────────────────────────────────────────

def try_client_credentials():
    """
    Attempt the OAuth client_credentials grant.
    Returns an access token string on success, None if the store/app
    combination does not permit this grant type.
    Exits on any unexpected error.
    """
    resp = requests.post(
        f"https://{SHOP}/admin/oauth/access_token",
        json={
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type":    "client_credentials",
        },
        timeout=15,
    )

    if resp.status_code == 200:
        data = resp.json()
        if "access_token" in data:
            print("  Auth method: client_credentials  ✓")
            return data["access_token"]

    # Shopify returns HTML (not JSON) for most OAuth errors at this endpoint.
    # Extract the error slug from the <title> tag when present.
    body_text = resp.text
    html_error = ""
    if "<title>" in body_text:
        try:
            html_error = body_text.split("<title>")[1].split("</title>")[0].strip()
        except Exception:
            pass

    # Parse JSON error body when available (some Shopify responses are JSON)
    try:
        err_body = resp.json()
        error_code = err_body.get("error", "")
    except Exception:
        error_code = ""

    # Any 4xx response means client_credentials is not usable here.
    # Common reasons: app not yet installed on this store (app_not_installed),
    # grant type not supported, or store/app permissions mismatch.
    if resp.status_code in (400, 401, 403):
        reason = html_error or error_code or f"HTTP {resp.status_code}"
        print(f"  client_credentials not available: {reason}")
        if "app_not_installed" in (html_error + error_code):
            print(
                "  The app has not been installed on this store yet.\n"
                "  The OAuth authorization code flow below will install it\n"
                "  and issue a permanent offline access token."
            )
        print("  Falling back to OAuth authorization code flow (one-time browser prompt)…")
        return None

    if error_code == "shop_not_permitted":
        print("  shop_not_permitted: store/app combination not allowed for this grant.")
        print("  Falling back to OAuth authorization code flow…")
        return None

    # Truly unexpected — surface without leaking secrets
    print(f"ERROR: Unexpected response from token endpoint (HTTP {resp.status_code}).")
    print(f"  {html_error or body_text[:300]}")
    sys.exit(1)


# ── Auth: authorization code flow ────────────────────────────────────────────

def oauth_authorization_code_flow() -> str:
    """
    Opens a browser for the Shopify OAuth consent screen, spins up a
    one-shot local HTTP server to receive the redirect, exchanges the
    code for an offline access token, and caches it in .shopify_token.
    """
    state = secrets.token_urlsafe(16)

    auth_url = (
        f"https://{SHOP}/admin/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&scope={urllib.parse.quote(OAUTH_SCOPES)}"
        f"&redirect_uri={urllib.parse.quote(OAUTH_REDIRECT, safe='')}"
        f"&state={state}"
        f"&grant_options[]=offline"        # request a permanent offline token
    )

    received: dict = {}
    ready = threading.Event()

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            received.update(params)
            body = b"<html><body><h2>Authorised. You can close this tab.</h2></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            ready.set()

        def log_message(self, *_):
            pass  # silence request logs

    server = HTTPServer(("127.0.0.1", OAUTH_PORT), _Handler)
    t = threading.Thread(target=server.handle_request, daemon=True)
    t.start()

    print(f"\n  Opening browser for Shopify authorisation…")
    print(f"  If the browser does not open, visit:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    if not ready.wait(timeout=120):
        print("ERROR: Timed out waiting for OAuth callback (120 s).")
        sys.exit(1)

    if received.get("state") != state:
        print("ERROR: OAuth state mismatch — possible CSRF. Aborting.")
        sys.exit(1)

    code = received.get("code")
    if not code:
        print(f"ERROR: No code in OAuth callback. Params received: {list(received.keys())}")
        sys.exit(1)

    # Exchange code for token
    resp = requests.post(
        f"https://{SHOP}/admin/oauth/access_token",
        json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code},
        timeout=15,
    )

    if resp.status_code != 200:
        print(f"ERROR: Token exchange failed (HTTP {resp.status_code}).")
        sys.exit(1)

    data = resp.json()
    if "access_token" not in data:
        print("ERROR: Token exchange response contained no access_token.")
        sys.exit(1)

    token = data["access_token"]
    TOKEN_CACHE_FILE.write_text(token)
    print("  Auth method: authorization code flow  ✓")
    print(f"  Token cached to {TOKEN_CACHE_FILE.name} for future runs.")
    return token


# ── Auth: orchestrator ────────────────────────────────────────────────────────

def get_access_token() -> str:
    """
    1. Try client_credentials (no browser needed).
    2. If not permitted, check the local token cache (.shopify_token).
    3. If no valid cache, run the authorization code flow (browser, one-time).
    """
    print("Acquiring access token…")

    # Attempt 1 — client credentials
    token = try_client_credentials()
    if token:
        return token

    # Attempt 2 — cached token from a previous authorization code flow
    if TOKEN_CACHE_FILE.exists():
        cached = TOKEN_CACHE_FILE.read_text().strip()
        if cached:
            print("  Auth method: cached token from previous OAuth flow  ✓")
            return cached

    # Attempt 3 — full browser OAuth flow
    print("  No cached token found.")
    return oauth_authorization_code_flow()


# ── GraphQL helper ────────────────────────────────────────────────────────────

def graphql(token: str, query: str, variables: dict = None) -> dict:
    resp = requests.post(
        f"https://{SHOP}/admin/api/{API_VERSION}/graphql.json",
        headers={
            "Content-Type":           "application/json",
            "X-Shopify-Access-Token": token,
        },
        json={"query": query, **({"variables": variables} if variables else {})},
        timeout=30,
    )

    if resp.status_code == 401:
        # Cached token may have been revoked — delete it and tell the user
        if TOKEN_CACHE_FILE.exists():
            TOKEN_CACHE_FILE.unlink()
        print(
            "ERROR: 401 Unauthorized — the access token was rejected.\n"
            "  If a cached token existed it has been deleted.\n"
            "  Re-run the script to re-authorise."
        )
        sys.exit(1)

    if resp.status_code != 200:
        print(f"ERROR: HTTP {resp.status_code}\n{resp.text}")
        sys.exit(1)

    data = resp.json()
    if "errors" in data:
        print(f"GraphQL errors:\n{json.dumps(data['errors'], indent=2)}")
        sys.exit(1)

    return data


def check_user_errors(errors: list, label: str):
    if errors:
        print(f"ERROR in {label}:")
        for e in errors:
            print(f"  field={e['field']}  message={e['message']}")
        sys.exit(1)


# ── Env validation ────────────────────────────────────────────────────────────

def check_env():
    missing = [
        name for name, val in [
            ("SHOPIFY_SHOP",        SHOP),
            ("SHOPIFY_CLIENT_ID",   CLIENT_ID),
            ("SHOPIFY_CLIENT_SECRET", CLIENT_SECRET),
            ("SHOPIFY_API_VERSION", API_VERSION),
        ] if not val
    ]
    if missing:
        print(f"ERROR: Missing env variables: {', '.join(missing)}")
        print(f"  Edit {ENV_FILE} and add the missing values.")
        sys.exit(1)

    masked_id = CLIENT_ID[:6] + "…" if len(CLIENT_ID) > 6 else "***"
    print(f"  SHOPIFY_SHOP        = {SHOP}")
    print(f"  SHOPIFY_CLIENT_ID   = {masked_id}")
    print(f"  SHOPIFY_API_VERSION = {API_VERSION}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("  GuideCraft — Shopify Product SEO Updater")
    print("=" * 62)
    print()

    check_env()
    token = get_access_token()
    print()

    gql = lambda q, v=None: graphql(token, q, v)

    # ── 1. Find product ──────────────────────────────────────────
    print(f"Searching for:  {PRODUCT_TITLE!r}")
    result = gql(QUERY_PRODUCT, {"query": f'title:"{PRODUCT_TITLE}"'})
    edges  = result["data"]["products"]["edges"]

    if not edges:
        print("\nERROR: No products found with that title.")
        print("Check the exact title in Shopify Admin → Products.")
        sys.exit(1)

    if len(edges) > 1:
        print(f"\nERROR: {len(edges)} products matched — expected 1. Found:")
        for e in edges:
            print(f"  · {e['node']['title']}")
        sys.exit(1)

    p          = edges[0]["node"]
    product_id = p["id"]
    img_edges  = p["images"]["edges"]
    image      = img_edges[0]["node"] if img_edges else None

    # ── 2. Show current state ────────────────────────────────────
    print()
    print("── Current state " + "─" * 45)
    print(f"  Product ID        {product_id}")
    print(f"  Product title     {p['title']}")
    print(f"  SEO title         {p['seo']['title'] or '(not set)'}")
    print(f"  Meta description  {p['seo']['description'] or '(not set)'}")
    print(f"  Image alt text    {image['altText'] or '(not set)' if image else '(no image)'}")
    print()

    # ── 3. Update SEO title + meta description ───────────────────
    print("── Updating SEO title and meta description… " + "─" * 17)
    seo_res = gql(MUTATION_UPDATE_SEO, {
        "id":             product_id,
        "seoTitle":       NEW_SEO_TITLE,
        "seoDescription": NEW_SEO_DESC,
    })
    check_user_errors(seo_res["data"]["productUpdate"]["userErrors"], "productUpdate")
    print("  OK")

    # ── 4. Update image alt text ─────────────────────────────────
    if image:
        print("── Updating image alt text… " + "─" * 33)
        alt_res = gql(MUTATION_UPDATE_IMAGE_ALT, {
            "productId": product_id,
            "imageId":   image["id"],
            "altText":   NEW_ALT_TEXT,
        })
        check_user_errors(alt_res["data"]["productImageUpdate"]["userErrors"], "productImageUpdate")
        print("  OK")
    else:
        print("── Skipping alt text — no image found on this product.")

    # ── 5. Re-fetch and confirm ──────────────────────────────────
    print()
    print("── Confirming saved values " + "─" * 35)
    confirm   = gql(QUERY_PRODUCT, {"query": f'title:"{PRODUCT_TITLE}"'})
    node      = confirm["data"]["products"]["edges"][0]["node"]
    img_conf  = node["images"]["edges"][0]["node"] if node["images"]["edges"] else None

    print(f"  Product ID        {node['id']}")
    print(f"  Product title     {node['title']}")
    print(f"  SEO title         {node['seo']['title'] or '(empty)'}")
    print(f"  Meta description  {node['seo']['description'] or '(empty)'}")
    print(f"  Image alt text    {img_conf['altText'] or '(empty)' if img_conf else '(no image)'}")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
