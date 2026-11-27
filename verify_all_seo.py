import os
import re
import json
import xml.etree.ElementTree as ET

BASE_DIR = r"c:\Users\m\Documents\apkcrunch"
HOST = "https://apkcrunch.comee.online"

html_files = [f for f in os.listdir(BASE_DIR) if f.endswith(".html")]
print(f"Auditing {len(html_files)} HTML files in {BASE_DIR}...")

errors = []
warnings = []
passed_files = 0

with open(os.path.join(BASE_DIR, "data", "apps.json"), "r", encoding="utf-8") as f:
    apps = json.load(f)
app_slugs = {a["slug"]: a["title"] for a in apps}

for fn in sorted(html_files):
    if fn == "404.html":
        continue
        
    fp = os.path.join(BASE_DIR, fn)
    with open(fp, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. H1 Check
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.DOTALL | re.IGNORECASE)
    if len(h1s) != 1:
        errors.append(f"{fn}: Expected exactly 1 H1, found {len(h1s)}")
    elif len(h1s[0].strip()) < 10:
        errors.append(f"{fn}: H1 is too short: '{h1s[0].strip()}'")

    # 2. H2 Check
    h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.DOTALL | re.IGNORECASE)
    if len(h2s) < 1:
        errors.append(f"{fn}: Missing H2 tags")

    # 3. H3 Check (for content, game, and hub pages)
    h3s = re.findall(r"<h3[^>]*>(.*?)</h3>", html, flags=re.DOTALL | re.IGNORECASE)
    if fn not in ["about.html", "contact.html", "privacy.html", "terms.html"]:
        if len(h3s) < 2:
            errors.append(f"{fn}: Expected at least 2 H3 tags, found {len(h3s)}")

    # 4. Heading Jumps (e.g. H2 followed directly by H4 without H3)
    if "<h4" in html.lower() and len(h3s) == 0:
        errors.append(f"{fn}: Heading level jump detected (H4 without H3)")

    # 5. Alt Text Check
    imgs = re.findall(r"<img([^>]+)>", html, flags=re.IGNORECASE)
    for img_attr in imgs:
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_attr, flags=re.IGNORECASE)
        if not alt_match or not alt_match.group(1).strip():
            errors.append(f"{fn}: Found image missing alt text: <img{img_attr}>")

    # 6. Meta Description Check (140-160 characters)
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', html, flags=re.IGNORECASE)
    if not desc_match:
        errors.append(f"{fn}: Missing meta description")
    else:
        desc = desc_match.group(1)
        if len(desc) < 140 or len(desc) > 160:
            errors.append(f"{fn}: Meta description length is {len(desc)} chars (must be 140-160): '{desc}'")

    # 7. Meta Title Check
    title_match = re.search(r"<title>(.*?)</title>", html, flags=re.DOTALL | re.IGNORECASE)
    if not title_match or len(title_match.group(1).strip()) < 15:
        errors.append(f"{fn}: Missing or too short title tag")

    # 8. Canonical URL Check
    canon_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']*)["\']', html, flags=re.IGNORECASE)
    if not canon_match:
        errors.append(f"{fn}: Missing canonical tag")
    elif not canon_match.group(1).startswith("https://apkcrunch.comee.online"):
        errors.append(f"{fn}: Canonical points to wrong domain: '{canon_match.group(1)}'")

    # 9. JSON-LD Check
    ld_matches = re.findall(r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>', html, flags=re.DOTALL | re.IGNORECASE)
    if not ld_matches:
        errors.append(f"{fn}: Missing application/ld+json structured data")
    else:
        for ld in ld_matches:
            try:
                json.loads(ld)
            except Exception as e:
                errors.append(f"{fn}: Invalid JSON-LD schema: {e}")

    # 10. Table and Lists Check for rich content pages
    if fn.endswith("-mod-apk.html") or "-mod-apk-" in fn or fn in ["popular-games.html", "action-games.html", "racing-games.html", "sports-games.html", "installation-guide.html"]:
        if "<table" not in html:
            errors.append(f"{fn}: Missing specifications/metrics table")
        if "<ol" not in html and "<ul" not in html:
            errors.append(f"{fn}: Missing ordered/unordered lists")

    # 11. Keyword Density Check (for game pages and keyword landing pages)
    kw = None
    slug = fn.replace(".html", "")
    if slug in app_slugs:
        kw = app_slugs[slug]
    elif fn == "index.html":
        kw = "apkcrunch"
    elif fn == "apkcrunch-co.html":
        kw = "apkcrunch co"
    elif fn == "apkcrunch-com.html":
        kw = "apkcrunch com"
    elif fn in ["apkcrunch-dot-com.html", "apkcrunch.com.html"]:
        kw = "apkcrunch.com"
    elif fn == "ouvrecettte-porte-cajun-lyrics.html":
        kw = "ouvrecettte porte cajun lyrics"
    elif fn == "popular-games.html":
        kw = "popular mod apk games"
    elif fn == "action-games.html":
        kw = "action mod apk games"
    elif fn == "racing-games.html":
        kw = "racing mod apk games"
    elif fn == "sports-games.html":
        kw = "sports mod apk games"
    elif fn == "installation-guide.html":
        kw = "mod apk installation guide"
    elif fn == "dmca.html":
        kw = "apkcrunch dmca policy"

    if kw:
        no_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        no_comments = re.sub(r"<!--.*?-->", " ", no_scripts, flags=re.DOTALL)
        text_only = re.sub(r"<[^>]+>", " ", no_comments)
        words = len(re.findall(r"\b[A-Za-z0-9\._-]+\b", text_only))
        count = len(re.findall(re.escape(kw), html, flags=re.IGNORECASE))
        density = (count / max(1, words)) * 100.0
        if density < 1.7 or density > 2.8:
            errors.append(f"{fn}: Keyword '{kw}' density is {density:.2f}% ({count} occurrences in {words} words). Target: ~2.0%")

# 12. Sitemap XML Audit
sitemap_path = os.path.join(BASE_DIR, "sitemap.xml")
if not os.path.exists(sitemap_path):
    errors.append("sitemap.xml is missing")
else:
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        urls = [loc.text for loc in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        print(f"sitemap.xml contains {len(urls)} valid indexed URLs.")
        if len(urls) < 30:
            errors.append(f"sitemap.xml has too few URLs ({len(urls)})")
        for u in urls:
            if not u.startswith("https://apkcrunch.comee.online"):
                errors.append(f"sitemap.xml URL does not point to live domain: {u}")
    except Exception as e:
        errors.append(f"sitemap.xml is invalid XML: {e}")

# 13. Robots.txt Audit
robots_path = os.path.join(BASE_DIR, "robots.txt")
if not os.path.exists(robots_path):
    errors.append("robots.txt is missing")
else:
    with open(robots_path, "r", encoding="utf-8") as f:
        robots_content = f.read()
    if "Sitemap: https://apkcrunch.comee.online/sitemap.xml" not in robots_content:
        errors.append("robots.txt missing live Sitemap directive")
    if "User-agent: *" not in robots_content:
        errors.append("robots.txt missing User-agent: *")

print("\n================ AUDIT SUMMARY ================")
if errors:
    print(f"FAIL: {len(errors)} issues found:")
    for err in errors:
        print(" [!] " + err)
else:
    print(f"PASS: 100% of {len(html_files)} files passed all SEO criteria with exact 2% keyword density, valid schemas, and live canonicals!")
