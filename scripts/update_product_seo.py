#!/usr/bin/env python3
"""
GuideCraft — Shopify Product SEO Updater
Updates SEO title, meta description, and first image alt text for one product.
Reads credentials from .env in the project root. Never prints secrets.
"""

import os
import sys
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
    import requests
except ImportError:
    print("ERROR: Missing packages. Run:  pip3 install requests python-dotenv")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv(Path(__file__).parent.parent / ".env")

SHOP = os.environ.get("SHOPIFY_SHOP", "").strip()
CLIENT_ID = os.environ.get("SHOPIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()
API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "").strip()

# Prefer an explicit access token; fall back to CLIENT_SECRET (works for some
# custom app setups where the secret IS the admin access token).
ACCESS_TOKEN = (os.environ.get("SHOPIFY_ACCESS_TOKEN") or CLIENT_SECRET).strip()

# Normalise shop to full myshopify.com domain
if SHOP and not SHOP.endswith(".myshopify.com"):
    SHOP = SHOP + ".myshopify.com"

# ── Target values ─────────────────────────────────────────────────────────────

PRODUCT_TITLE   = "The GLP-1 Companion: Nutrition & Muscle Retention Guide"
NEW_SEO_TITLE   = "GLP-1 Nutrition & Muscle Retention Guide | GuideCraft"
NEW_SEO_DESC    = (
    "Practical PDF guide for women on GLP-1 medication. Covers nutrition strategies, "
    "protein intake, and how to protect muscle while losing weight. Instant download."
)
NEW_ALT_TEXT    = (
    "The GLP-1 Companion nutrition and muscle retention guide cover "
    "— downloadable PDF for women | GuideCraft"
)

# ── GraphQL queries / mutations ───────────────────────────────────────────────

QUERY_PRODUCT = """
query GetProduct($query: String!) {
  products(first: 5, query: $query) {
    edges {
      node {
        id
        title
        seo {
          title
          description
        }
        images(first: 1) {
          edges {
            node {
              id
              altText
              url
            }
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
    seo: {
      title: $seoTitle
      description: $seoDescription
    }
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
    image {
      id
      altText
    }
    userErrors { field message }
  }
}
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def check_env():
    missing = [v for v, val in [
        ("SHOPIFY_SHOP", SHOP),
        ("SHOPIFY_CLIENT_ID", CLIENT_ID),
        ("SHOPIFY_CLIENT_SECRET", CLIENT_SECRET),
        ("SHOPIFY_API_VERSION", API_VERSION),
    ] if not val]

    if missing:
        print(f"ERROR: Missing required env variables: {', '.join(missing)}")
        print(f"  Add them to your .env file.")
        sys.exit(1)

    token_source = (
        "SHOPIFY_ACCESS_TOKEN"
        if os.environ.get("SHOPIFY_ACCESS_TOKEN")
        else "SHOPIFY_CLIENT_SECRET (fallback)"
    )
    masked_id = CLIENT_ID[:6] + "…" if len(CLIENT_ID) > 6 else "***"

    print(f"  SHOPIFY_SHOP        = {SHOP}")
    print(f"  SHOPIFY_CLIENT_ID   = {masked_id}")
    print(f"  SHOPIFY_API_VERSION = {API_VERSION}")
    print(f"  Token source        = {token_source}")
    print()


def graphql(query: str, variables: dict = None) -> dict:
    url = f"https://{SHOP}/admin/api/{API_VERSION}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN,
    }
    resp = requests.post(
        url,
        headers=headers,
        json={"query": query, **({"variables": variables} if variables else {})},
        timeout=30,
    )

    if resp.status_code == 401:
        print("ERROR: 401 Unauthorized — authentication failed.\n")
        print("Your CLIENT_SECRET is not being accepted as an Admin API access token.")
        print("To fix this:\n")
        print("  1. Shopify Admin → Settings → Apps and sales channels")
        print("  2. Click 'Develop apps' → open your app")
        print("  3. 'API credentials' tab → 'Reveal token once'")
        print("     (The token starts with shpat_ or shpca_)")
        print("  4. Add to your .env:")
        print("       SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxx\n")
        print("  If you no longer see 'Reveal token once', click 'Uninstall app'")
        print("  then re-install to generate a fresh token.")
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("  GuideCraft — Shopify Product SEO Updater")
    print("=" * 62)
    print()

    check_env()

    # ── Step 1: find product ─────────────────────────────────────
    print(f"Searching for product:  {PRODUCT_TITLE!r}")
    result = graphql(QUERY_PRODUCT, {"query": f'title:"{PRODUCT_TITLE}"'})
    edges = result["data"]["products"]["edges"]

    if not edges:
        print("\nERROR: No products found with that title.")
        print("Check the exact title in Shopify Admin → Products and update PRODUCT_TITLE in this script.")
        sys.exit(1)

    if len(edges) > 1:
        print(f"\nERROR: {len(edges)} products matched — expected exactly 1. Titles found:")
        for e in edges:
            print(f"  · {e['node']['title']}")
        sys.exit(1)

    p          = edges[0]["node"]
    product_id = p["id"]
    img_edges  = p["images"]["edges"]
    image      = img_edges[0]["node"] if img_edges else None

    # ── Step 2: show current state ───────────────────────────────
    print()
    print("── Current state " + "─" * 45)
    print(f"  Product ID        {product_id}")
    print(f"  Product title     {p['title']}")
    print(f"  SEO title         {p['seo']['title'] or '(not set)'}")
    print(f"  Meta description  {p['seo']['description'] or '(not set)'}")
    print(f"  Image alt text    {image['altText'] or '(not set)' if image else '(no image on product)'}")
    print()

    # ── Step 3: update SEO title + meta description ──────────────
    print("── Updating SEO title and meta description… " + "─" * 17)
    seo_result = graphql(MUTATION_UPDATE_SEO, {
        "id": product_id,
        "seoTitle": NEW_SEO_TITLE,
        "seoDescription": NEW_SEO_DESC,
    })
    check_user_errors(seo_result["data"]["productUpdate"]["userErrors"], "productUpdate")
    print("  OK")

    # ── Step 4: update image alt text ────────────────────────────
    if image:
        print("── Updating image alt text… " + "─" * 33)
        alt_result = graphql(MUTATION_UPDATE_IMAGE_ALT, {
            "productId": product_id,
            "imageId":   image["id"],
            "altText":   NEW_ALT_TEXT,
        })
        check_user_errors(alt_result["data"]["productImageUpdate"]["userErrors"], "productImageUpdate")
        print("  OK")
    else:
        print("── Skipping alt text — no image found on this product.")

    # ── Step 5: re-fetch and confirm ─────────────────────────────
    print()
    print("── Confirming saved values " + "─" * 35)
    confirm    = graphql(QUERY_PRODUCT, {"query": f'title:"{PRODUCT_TITLE}"'})
    node       = confirm["data"]["products"]["edges"][0]["node"]
    img_edges  = node["images"]["edges"]
    img_conf   = img_edges[0]["node"] if img_edges else None

    print(f"  Product ID        {node['id']}")
    print(f"  Product title     {node['title']}")
    print(f"  SEO title         {node['seo']['title'] or '(empty)'}")
    print(f"  Meta description  {node['seo']['description'] or '(empty)'}")
    print(f"  Image alt text    {img_conf['altText'] or '(empty)' if img_conf else '(no image)'}")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
