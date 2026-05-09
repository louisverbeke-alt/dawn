#!/usr/bin/env python3
"""
GuideCraft — Full Product SEO & Description Updater
Updates all three products: SEO, descriptions, titles, handles, tags, alt text.
"""

import os, sys, json
from pathlib import Path

try:
    from dotenv import load_dotenv
    import requests
except ImportError:
    sys.exit("ERROR: pip3 install requests python-dotenv")

ENV_FILE         = Path(__file__).parent.parent / ".env"
TOKEN_CACHE_FILE = Path(__file__).parent.parent / ".shopify_token"

load_dotenv(ENV_FILE)
SHOP        = os.environ.get("SHOPIFY_SHOP", "").strip()
CLIENT_ID   = os.environ.get("SHOPIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()
API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2026-04").strip()

if SHOP and not SHOP.endswith(".myshopify.com"):
    SHOP += ".myshopify.com"

# ── Product data ───────────────────────────────────────────────────────────────

PRODUCTS = [
    {
        "search_id": "gid://shopify/Product/10497155465558",
        "new_title": "The Menopause Strength Blueprint",
        "new_handle": "the-menopause-strength-blueprint",
        "new_vendor": "GuideCrafted.com",
        "new_product_type": "PDF Guide",
        "new_tags": [
            "menopause", "perimenopause", "postmenopause", "strength training",
            "women over 40", "muscle health", "bone density", "nutrition",
            "fitness for women", "digital download", "PDF guide", "wellness"
        ],
        "new_seo_title": "Menopause Strength Training Guide for Women | GuideCraft",
        "new_seo_desc": (
            "Practical strength training and nutrition PDF guide for women 40–60. "
            "Build muscle, support bones, and feel stronger through menopause. Instant download."
        ),
        "new_alt_text": (
            "The Menopause Strength Blueprint PDF guide cover "
            "— strength training and nutrition for women over 40 | GuideCraft"
        ),
        "new_description": """\
<p><strong>The Menopause Strength Blueprint</strong> is a practical PDF guide for women aged 40–60 who want to feel stronger, protect their muscle mass, and support their bone health — without complicated programmes or unrealistic expectations. Whether you are new to strength training, returning after a break, or looking for a more menopause-specific approach, this guide gives you a clear, supportive path forward.</p>

<p><strong>What's Inside</strong></p>
<ul>
<li>A plain-English explanation of how menopause affects muscle, bone density, recovery, and fat distribution</li>
<li>Evidence-based strength training principles adapted for perimenopause, menopause, and postmenopause</li>
<li>A practical 3-day strength training blueprint you can follow at home or in the gym</li>
<li>Protein-first nutrition targets and a high-protein example day menu</li>
<li>Bone-supportive food and supplement guidance</li>
<li>Common mistakes women make after 40 — and how to avoid them</li>
<li>A simple 7-day action plan to help you start right away</li>
</ul>

<p><strong>Perfect For</strong></p>
<ul>
<li>Women aged 40–60 going through perimenopause, menopause, or postmenopause</li>
<li>Anyone who wants to protect muscle mass and bone strength as they age</li>
<li>Women looking for practical, structured guidance they can follow at their own pace</li>
<li>Anyone frustrated by generic fitness advice that does not account for hormonal changes</li>
</ul>

<p><strong>Why You'll Like It</strong></p>
<ul>
<li>Written in clear, friendly language — no confusing fitness jargon</li>
<li>Practical steps you can take right away, without a gym membership or equipment</li>
<li>Covers both training and nutrition together so you get the full picture</li>
<li>Structured and easy to follow, even on low-energy days</li>
<li>Designed specifically for women in their 40s, 50s, and 60s — not a one-size-fits-all approach</li>
</ul>

<p><strong>Digital Delivery</strong></p>
<p>This is a downloadable PDF guide. After purchase, you will receive an instant download link by email. No physical item will be shipped. You can read it on your phone, tablet, or computer, or print it at home.</p>

<p><strong>Disclaimer:</strong> This guide is for educational purposes only and is not a substitute for professional medical advice. Always consult a qualified healthcare provider before starting a new training or nutrition plan, especially if you have a medical condition, injury, or are taking medication.</p>""",
    },
    {
        "search_id": "gid://shopify/Product/10499989930326",
        "new_title": "The Gentle Parenting Script Deck",
        "new_handle": "the-gentle-parenting-script-deck",
        "new_vendor": "GuideCrafted.com",
        "new_product_type": "PDF Guide",
        "new_tags": [
            "parenting", "gentle parenting", "toddler", "toddler tantrums",
            "calm parenting", "parenting scripts", "moms", "digital download",
            "PDF guide", "child behaviour", "positive parenting"
        ],
        "new_seo_title": "Gentle Parenting Scripts for Toddlers | GuideCraft",
        "new_seo_desc": (
            "Word-for-word calming scripts for the 20 most common toddler triggers. "
            "Stay calm and connected — downloadable PDF for parents. Instant download."
        ),
        "new_alt_text": (
            "The Gentle Parenting Script Deck PDF guide cover "
            "— word-for-word scripts for toddler tantrums | GuideCraft"
        ),
        "new_description": """\
<p><strong>The Gentle Parenting Script Deck</strong> is a practical PDF guide for parents of toddlers who want to stay calm, connected, and in control — even in the most challenging moments. Packed with word-for-word scripts for the 20 most common toddler triggers, this guide takes the guesswork out of what to say when it matters most.</p>

<p><strong>What's Inside</strong></p>
<ul>
<li>Word-for-word calming scripts for 20 of the most common toddler triggers — including tantrums, hitting, bedtime resistance, and refusals</li>
<li>Simple language you can use in the moment without having to think or improvise</li>
<li>A brief guide to the gentle parenting principles behind each script</li>
<li>Tips for staying regulated as a parent when emotions run high</li>
<li>Scripts that validate your child's feelings while holding firm, clear limits</li>
</ul>

<p><strong>Perfect For</strong></p>
<ul>
<li>Parents of toddlers aged 1–5 who feel overwhelmed during meltdowns</li>
<li>Moms who want to respond more calmly but do not always know what to say</li>
<li>Caregivers looking for a practical, compassionate approach to toddler behaviour</li>
<li>Anyone who wants to strengthen the parent-child connection during difficult moments</li>
</ul>

<p><strong>Why You'll Like It</strong></p>
<ul>
<li>No theory overload — just simple, ready-to-use scripts you can pick up and apply today</li>
<li>Written in warm, respectful language that feels natural to say out loud</li>
<li>Short enough to read in one sitting and easy to return to whenever you need it</li>
<li>Helps you feel more confident and prepared before the next tough moment arrives</li>
</ul>

<p><strong>Digital Delivery</strong></p>
<p>This is a downloadable PDF guide. After purchase, you will receive an instant download link by email. No physical item will be shipped. You can save it to your phone for easy access, or print it out and keep it somewhere handy at home.</p>""",
    },
    {
        "search_id": "gid://shopify/Product/10508302778710",
        "new_title": "The GLP-1 Companion: Nutrition & Muscle Retention Guide",
        "new_handle": "the-glp-1-companion-nutrition-muscle-retention-guide",
        "new_vendor": "GuideCrafted.com",
        "new_product_type": "PDF Guide",
        "new_tags": [
            "GLP-1", "Ozempic", "Wegovy", "Mounjaro", "weight loss medication",
            "muscle retention", "nutrition", "high protein", "women's health",
            "digital download", "PDF guide", "wellness"
        ],
        "new_seo_title": "GLP-1 Nutrition & Muscle Retention Guide | GuideCraft",
        "new_seo_desc": (
            "Practical PDF guide for women on GLP-1 medication. Covers nutrition strategies, "
            "protein intake, and how to protect muscle while losing weight. Instant download."
        ),
        "new_alt_text": (
            "The GLP-1 Companion nutrition and muscle retention guide cover "
            "— downloadable PDF for women | GuideCraft"
        ),
        "new_description": """\
<p><strong>The GLP-1 Companion</strong> is a practical PDF guide for women using GLP-1 weight loss medications — such as Ozempic, Wegovy, or Mounjaro — who want to protect their muscle, eat in a way that feels manageable, and make the most of their progress. This guide helps you nourish your body smartly during this stage, without restrictive diets or overwhelming advice.</p>

<p><strong>What's Inside</strong></p>
<ul>
<li>A clear explanation of how GLP-1 medications affect appetite, digestion, and muscle retention</li>
<li>High-protein nutrition strategies to help protect muscle while losing weight</li>
<li>Practical meal mapping for low-appetite days, including small, nutrient-dense meal ideas</li>
<li>Tips for managing common side effects such as nausea and food aversions</li>
<li>A daily protein target guide with easy food sources and example menus</li>
<li>Supplement considerations to fill common nutritional gaps on a reduced-calorie intake</li>
<li>A simple tracking framework to keep your nutrition on track week by week</li>
</ul>

<p><strong>Perfect For</strong></p>
<ul>
<li>Women currently using GLP-1 medications such as Ozempic, Wegovy, or Mounjaro</li>
<li>Anyone looking to maintain muscle and energy while reducing calorie intake</li>
<li>Women who struggle to eat enough protein when appetite is low</li>
<li>Anyone who wants clear, practical nutritional guidance to complement their treatment</li>
</ul>

<p><strong>Why You'll Like It</strong></p>
<ul>
<li>Written specifically for women on GLP-1 medications — not generic diet advice</li>
<li>Practical strategies you can apply immediately, even on low-appetite days</li>
<li>Clear, friendly language — no overwhelming nutrition science or calorie obsession</li>
<li>Helps you feel confident that you are nourishing your body well during your treatment</li>
</ul>

<p><strong>Digital Delivery</strong></p>
<p>This is a downloadable PDF guide. After purchase, you will receive an instant download link by email. No physical item will be shipped. You can read it on your phone, tablet, or computer, or print it at home for easy reference.</p>

<p><strong>Disclaimer:</strong> This guide is for educational purposes only and is not a substitute for professional medical or nutritional advice. GLP-1 medications should only be used under the supervision of a qualified healthcare provider. Always consult your doctor or dietitian before making changes to your nutrition plan.</p>""",
    },
    {
        "search_id": "gid://shopify/Product/10511173845334",
        "new_title": "The Anxious-Avoidant Trap: A 30-Day Attachment Reset",
        "new_handle": "the-anxious-avoidant-trap",
        "new_vendor": "GuideCrafted.com",
        "new_product_type": "PDF Guide",
        "new_tags": [
            "anxious attachment", "avoidant attachment", "anxious-avoidant",
            "attachment theory", "attachment workbook", "CBT",
            "cognitive behavioral therapy", "relationships", "relationship patterns",
            "30-day plan", "emotional healing", "digital download",
            "PDF guide", "women's mental health", "self-help"
        ],
        "new_seo_title": "Anxious-Avoidant Attachment Reset Workbook | GuideCraft",
        "new_seo_desc": (
            "Break the anxious-avoidant push-pull cycle with this 18-page CBT workbook. "
            "30-day plan, real-world scripts, daily tracker. Instant download."
        ),
        "new_alt_text": (
            "The Anxious-Avoidant Trap: A 30-Day Attachment Reset PDF workbook cover "
            "— CBT exercises for the push-pull relationship cycle | GuideCraft"
        ),
        "new_description": """\
<p><strong>The Anxious-Avoidant Trap: A 30-Day Attachment Reset</strong> is an 18-page CBT workbook for anyone who understands the push-pull cycle — and is still stuck in it. Built around cognitive behavioural exercises designed specifically for this dynamic, it gives you practical tools that interrupt the pattern at the moment it starts, not after the damage is done. You work through it over 30 structured days, whether your partner picks it up or not.</p>

<p><strong>What's Inside</strong></p>
<ul>
<li>A plain-language breakdown of why the anxious-avoidant cycle is so hard to exit — and why insight alone is not enough</li>
<li>A self-assessment to identify your dominant pattern: anxious-leaning, avoidant-leaning, or both</li>
<li>The 5-Step Reset Framework: a sequence of CBT-based moves to use before, during, and after a trigger fires</li>
<li>A week-by-week 30-day plan with daily structure and focus questions</li>
<li>Five real-world scripts for the moments your brain goes blank — when you want to pursue, when you want to disappear, mid-conflict, and after a rupture</li>
<li>A printable CBT Thought Record worksheet</li>
<li>A 30-day daily tracker organised by phase</li>
<li>A troubleshooting section for the three walls everyone hits</li>
<li>A sourced references page</li>
</ul>

<p><strong>Perfect For</strong></p>
<ul>
<li>Anyone who recognises the anxious-avoidant dynamic in their relationship and wants practical tools to change it</li>
<li>People working on their own — no couples homework, no assuming your partner is on board</li>
<li>Those who have read about attachment theory but find that knowledge alone has not changed their behaviour</li>
<li>Anyone who wants a structured, day-by-day approach rather than open-ended self-reflection</li>
</ul>

<p><strong>Why You'll Like It</strong></p>
<ul>
<li>Grounded in CBT — not just theory or journaling prompts, but exercises that change behaviour in the moment</li>
<li>Designed to work solo — you do not need your partner's cooperation to make progress</li>
<li>Structured and specific: 30 days, clear phases, and a daily tracker so you always know where you are</li>
<li>Includes ready-to-use scripts for high-pressure moments when you cannot think clearly</li>
<li>Print-friendly format — easy to work through on paper, which supports the reflective nature of the exercises</li>
</ul>

<p><strong>Digital Delivery</strong></p>
<p>This is a downloadable PDF workbook, 18 pages, print-friendly. After purchase, you will receive an instant download link by email. No physical item will be shipped. You can print it at home or work through it on your device.</p>

<p><strong>Disclaimer:</strong> This guide is for educational and self-development purposes only. It is not a substitute for professional therapy, counselling, or mental health support. If you are experiencing significant emotional distress or relationship difficulties, please seek support from a qualified mental health professional.</p>""",
    },
]

# ── GraphQL mutations ──────────────────────────────────────────────────────────

MUTATION_UPDATE_PRODUCT = """
mutation UpdateProduct(
  $id: ID!,
  $title: String!,
  $handle: String!,
  $vendor: String!,
  $productType: String!,
  $tags: [String!]!,
  $seoTitle: String!,
  $seoDescription: String!,
  $descriptionHtml: String!
) {
  productUpdate(input: {
    id: $id
    title: $title
    handle: $handle
    vendor: $vendor
    productType: $productType
    tags: $tags
    seo: { title: $seoTitle description: $seoDescription }
    descriptionHtml: $descriptionHtml
  }) {
    product {
      id title handle
      seo { title description }
      tags
    }
    userErrors { field message }
  }
}
"""

MUTATION_UPDATE_IMAGE_ALT = """
mutation UpdateImageAlt($productId: ID!, $media: [UpdateMediaInput!]!) {
  productUpdateMedia(productId: $productId, media: $media) {
    media {
      ... on MediaImage {
        id
        image { altText }
      }
    }
    mediaUserErrors { code field message }
    userErrors { field message }
  }
}
"""

QUERY_PRODUCT_BY_ID = """
query GetProduct($id: ID!) {
  product(id: $id) {
    id title handle status vendor productType tags
    seo { title description }
    media(first: 3) {
      edges {
        node {
          id
          ... on MediaImage {
            image { altText url }
          }
        }
      }
    }
  }
}
"""

# ── Auth ───────────────────────────────────────────────────────────────────────

def get_token():
    if TOKEN_CACHE_FILE.exists():
        t = TOKEN_CACHE_FILE.read_text().strip()
        if t:
            return t
    resp = requests.post(
        f"https://{SHOP}/admin/oauth/access_token",
        json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
        timeout=15,
    )
    if resp.status_code == 200:
        data = resp.json()
        if "access_token" in data:
            return data["access_token"]
    sys.exit("No valid token. Run scripts/update_product_seo.py first to complete OAuth.")

# ── API helper ─────────────────────────────────────────────────────────────────

def gql(token, query, variables=None):
    resp = requests.post(
        f"https://{SHOP}/admin/api/{API_VERSION}/graphql.json",
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token},
        json={"query": query, **({"variables": variables} if variables else {})},
        timeout=30,
    )
    if resp.status_code == 401:
        TOKEN_CACHE_FILE.unlink(missing_ok=True)
        sys.exit("401 Unauthorized — cached token deleted. Re-run update_product_seo.py to re-auth.")
    if resp.status_code != 200:
        sys.exit(f"HTTP {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    if "errors" in data:
        sys.exit(f"GraphQL error:\n{json.dumps(data['errors'], indent=2)}")
    return data

def check_errors(errors, label):
    if errors:
        print(f"  ERROR in {label}:")
        for e in errors:
            print(f"    field={e['field']}  message={e['message']}")
        return False
    return True

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 64)
    print("  GuideCraft — Full Product SEO & Description Updater")
    print("=" * 64)
    print()

    token = get_token()
    g = lambda q, v=None: gql(token, q, v)

    report = []

    for prod in PRODUCTS:
        pid = prod["search_id"]
        print(f"\n── Product: {prod['new_title']}")
        print(f"   ID: {pid}")

        # Fetch current state
        current = g(QUERY_PRODUCT_BY_ID, {"id": pid})["data"]["product"]
        if not current:
            print(f"   SKIP — product not found.")
            report.append({"title": prod["new_title"], "status": "SKIPPED — not found"})
            continue

        img_edges = current["media"]["edges"]
        image = img_edges[0]["node"] if img_edges else None

        print(f"   Current title:  {current['title']}")
        print(f"   Current handle: {current['handle']}")
        print(f"   Current SEO:    {current['seo']['title'] or '(none)'}")

        # Update product (title, handle, tags, SEO, description)
        print("   Updating product…", end=" ", flush=True)
        res = g(MUTATION_UPDATE_PRODUCT, {
            "id":              pid,
            "title":           prod["new_title"],
            "handle":          prod["new_handle"],
            "vendor":          prod["new_vendor"],
            "productType":     prod["new_product_type"],
            "tags":            prod["new_tags"],
            "seoTitle":        prod["new_seo_title"],
            "seoDescription":  prod["new_seo_desc"],
            "descriptionHtml": prod["new_description"],
        })
        ok = check_errors(res["data"]["productUpdate"]["userErrors"], "productUpdate")
        if ok:
            print("OK")

        changed_fields = ["title", "handle", "vendor", "productType", "tags",
                          "SEO title", "SEO meta description", "description"]

        # Update image alt text
        if image:
            print("   Updating image alt text…", end=" ", flush=True)
            alt_res = g(MUTATION_UPDATE_IMAGE_ALT, {
                "productId": pid,
                "media":     [{"id": image["id"], "alt": prod["new_alt_text"]}],
            })
            update_result = alt_res["data"]["productUpdateMedia"]
            ok_alt = check_errors(update_result.get("userErrors", []), "productUpdateMedia") and \
                     check_errors(update_result.get("mediaUserErrors", []), "productUpdateMedia(media)")
            if ok_alt:
                print("OK")
                changed_fields.append("image alt text")
        else:
            print("   Skipping alt text — no image on this product.")

        report.append({
            "title":   prod["new_title"],
            "status":  "UPDATED",
            "changed": changed_fields,
        })

    # ── Final report ───────────────────────────────────────────────────────────
    print("\n\n" + "=" * 64)
    print("  REPORT")
    print("=" * 64)

    for item in report:
        print(f"\n  {item['title']}")
        print(f"  Status: {item['status']}")
        if "changed" in item:
            for f in item["changed"]:
                print(f"    ✓ {f}")

    print()
    print("SEO issues to fix manually:")
    print("  1. Add product images to products that are missing them.")
    print("  2. Consider creating collections: Menopause & Fitness, Parenting, Weight Loss Support.")
    print("  3. Add Google Search Console to monitor indexing once the store goes live.")
    print("  4. The live theme (Flora) may also need its product templates reviewed.")
    print()
    print("Done.")

if __name__ == "__main__":
    main()
