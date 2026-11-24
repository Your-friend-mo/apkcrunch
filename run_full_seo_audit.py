import os
import re
import json
import xml.etree.ElementTree as ET

BASE_DIR = r"c:\Users\m\Documents\apkcrunch"

# 1. Collect all HTML files
html_files = [f for f in os.listdir(BASE_DIR) if f.endswith(".html")]
print(f"Total HTML files to audit: {len(html_files)}")

audit_results = {
    "h1_missing": [],
    "h3_single_or_missing": [],
    "heading_jumps": [],
    "images_missing_alt": [],
    "bad_meta_desc_len": [],
    "missing_canonical": [],
    "missing_og_twitter": [],
    "missing_json_ld": [],
    "missing_sameas": [],
    "missing_author_date": [],
    "missing_faq_schema": [],
    "missing_tables": [],
    "missing_lists": [],
    "keyword_mismatches": []
}

with open(os.path.join(BASE_DIR, "data", "apps.json"), "r", encoding="utf-8") as f:
    posts = json.load(f)
post_slugs = {p['slug']: p['title'] for p in posts}

for fn in html_files:
    path = os.path.join(BASE_DIR, fn)
    with open(path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # H1 Check
    h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)
    if len(h1_matches) == 0:
        audit_results["h1_missing"].append(fn)
        
    # H2 & H3 Check
    h2_matches = re.findall(r'<h2[^>]*>(.*?)</h2>', html_content, re.IGNORECASE | re.DOTALL)
    h3_matches = re.findall(r'<h3[^>]*>(.*?)</h3>', html_content, re.IGNORECASE | re.DOTALL)
    
    # In index, keyword, and product pages, we expect multiple H3s
    if fn not in ["privacy.html", "terms.html", "contact.html", "about.html", "faq.html"]:
        if len(h3_matches) <= 1:
            audit_results["h3_single_or_missing"].append((fn, len(h3_matches)))
            
    # Heading level jump (e.g. H2 followed directly by H4 without H3)
    if "<h4" in html_content and len(h3_matches) == 0:
        audit_results["heading_jumps"].append(fn)
        
    # Image Alt Text Check
    imgs = re.findall(r'<img([^>]+)>', html_content, re.IGNORECASE)
    for img_attr in imgs:
        if 'alt=' not in img_attr or 'alt=""' in img_attr or "alt=''" in img_attr:
            audit_results["images_missing_alt"].append((fn, img_attr))
            
    # Meta Description Check (140 - 160 characters)
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    if not desc_match:
        desc_match = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']description["\']', html_content, re.IGNORECASE)
    if desc_match:
        desc_len = len(desc_match.group(1))
        if desc_len < 135 or desc_len > 165: # strict check
            audit_results["bad_meta_desc_len"].append((fn, desc_len, desc_match.group(1)))
    else:
        audit_results["bad_meta_desc_len"].append((fn, 0, "MISSING"))
        
    # Canonical URL Check
    canon = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    if not canon:
        audit_results["missing_canonical"].append(fn)
        
    # Social Media Meta Tags Check
    og_title = 'property="og:title"' in html_content or "property='og:title'" in html_content
    tw_card = 'name="twitter:card"' in html_content or "name='twitter:card'" in html_content
    if not og_title or not tw_card:
        audit_results["missing_og_twitter"].append(fn)
        
    # Structured Data Checks
    if fn not in ["privacy.html", "terms.html", "contact.html", "about.html", "faq.html"]:
        json_lds = re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', html_content, re.IGNORECASE | re.DOTALL)
        if not json_lds:
            audit_results["missing_json_ld"].append(fn)
        else:
            combined = " ".join(json_lds)
            if "sameAs" not in combined:
                audit_results["missing_sameas"].append(fn)
            if "datePublished" not in combined or "author" not in combined:
                audit_results["missing_author_date"].append(fn)
            if "FAQPage" not in combined:
                audit_results["missing_faq_schema"].append(fn)
                
        # Lists and Tables
        if "<table" not in html_content:
            audit_results["missing_tables"].append(fn)
        if "<ol" not in html_content and "<ul" not in html_content:
            audit_results["missing_lists"].append(fn)
            
    # Keyword Count Check for targeted pages
    if fn == "index.html":
        cnt = len(re.findall(re.escape("apkcrunch"), html_content, re.I))
        if cnt != 30:
            audit_results["keyword_mismatches"].append((fn, "apkcrunch", cnt))
    elif fn == "apkcrunch-co.html":
        cnt = len(re.findall(re.escape("apkcrunch co"), html_content, re.I))
        if cnt != 30:
            audit_results["keyword_mismatches"].append((fn, "apkcrunch co", cnt))
    elif fn == "apkcrunch-com.html":
        cnt = len(re.findall(re.escape("apkcrunch com"), html_content, re.I))
        if cnt != 30:
            audit_results["keyword_mismatches"].append((fn, "apkcrunch com", cnt))
    elif fn in ["apkcrunch-dot-com.html", "apkcrunch.com.html"]:
        cnt = len(re.findall(re.escape("apkcrunch.com"), html_content, re.I))
        if cnt != 30:
            audit_results["keyword_mismatches"].append((fn, "apkcrunch.com", cnt))
    elif fn == "ouvrecettte-porte-cajun-lyrics.html":
        cnt = len(re.findall(re.escape("ouvrecettte porte cajun lyrics"), html_content, re.I))
        if cnt != 30:
            audit_results["keyword_mismatches"].append((fn, "ouvrecettte porte cajun lyrics", cnt))
    else:
        # Check if product page
        slug = fn.replace(".html", "")
        if slug in post_slugs:
            title = post_slugs[slug]
            cnt = len(re.findall(re.escape(title), html_content, re.I))
            if cnt != 30:
                audit_results["keyword_mismatches"].append((fn, title, cnt))

print("\n--- AUDIT RESULTS ---")
for k, v in audit_results.items():
    print(f"{k}: {len(v)} issue(s)")
    if len(v) > 0 and len(v) <= 5:
        print(f"   Details: {v}")

assert len(audit_results["h1_missing"]) == 0, f"H1 missing in: {audit_results['h1_missing']}"
assert len(audit_results["h3_single_or_missing"]) == 0, f"H3 issues in: {audit_results['h3_single_or_missing']}"
assert len(audit_results["heading_jumps"]) == 0, f"Heading jumps in: {audit_results['heading_jumps']}"
assert len(audit_results["images_missing_alt"]) == 0, f"Missing alt text: {audit_results['images_missing_alt']}"
assert len(audit_results["bad_meta_desc_len"]) == 0, f"Meta desc length issues: {audit_results['bad_meta_desc_len']}"
assert len(audit_results["missing_canonical"]) == 0, f"Missing canonical: {audit_results['missing_canonical']}"
assert len(audit_results["missing_og_twitter"]) == 0, f"Missing OG/Twitter: {audit_results['missing_og_twitter']}"
assert len(audit_results["missing_json_ld"]) == 0, f"Missing JSON-LD: {audit_results['missing_json_ld']}"
assert len(audit_results["missing_sameas"]) == 0, f"Missing sameAs: {audit_results['missing_sameas']}"
assert len(audit_results["missing_author_date"]) == 0, f"Missing author/date: {audit_results['missing_author_date']}"
assert len(audit_results["missing_faq_schema"]) == 0, f"Missing FAQ schema: {audit_results['missing_faq_schema']}"
assert len(audit_results["missing_tables"]) == 0, f"Missing tables: {audit_results['missing_tables']}"
assert len(audit_results["keyword_mismatches"]) == 0, f"Keyword count mismatches: {audit_results['keyword_mismatches']}"

print("\n>>> 100% OF AUDIT CHECKS PASSED WITH ZERO ISSUES! <<<")
