import os
import re
import json
import xml.etree.ElementTree as ET

BASE_DIR = r"c:\Users\m\Documents\apkcrunch"
APPS_PATH = os.path.join(BASE_DIR, "data", "apps.json")

with open(APPS_PATH, "r", encoding="utf-8") as f:
    posts = json.load(f)

print(f"Loaded {len(posts)} posts for verification.")

# 1. Verify Homepage
with open(os.path.join(BASE_DIR, "index.html"), "r", encoding="utf-8") as f:
    home_html = f.read()
cnt = len(re.findall(re.escape("apkcrunch"), home_html, re.IGNORECASE))
print(f"index.html: 'apkcrunch' count = {cnt}")
assert cnt == 30, f"index.html failed: expected 30, got {cnt}"

# 2. Verify Keyword Landing Pages
KEYWORD_CHECKS = [
    ("apkcrunch-co.html", "apkcrunch co"),
    ("apkcrunch-com.html", "apkcrunch com"),
    ("apkcrunch-dot-com.html", "apkcrunch.com"),
    ("ouvrecettte-porte-cajun-lyrics.html", "ouvrecettte porte cajun lyrics"),
]

for fn, kw in KEYWORD_CHECKS:
    path = os.path.join(BASE_DIR, fn)
    assert os.path.exists(path), f"Missing file: {fn}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    cnt = len(re.findall(re.escape(kw), content, re.IGNORECASE))
    print(f"{fn}: '{kw}' count = {cnt}")
    assert cnt == 30, f"{fn} failed: expected 30, got {cnt}"

# 3. Verify All 13 Product Pages
for p in posts:
    fn = f"{p['slug']}.html"
    kw = p['title']
    path = os.path.join(BASE_DIR, fn)
    assert os.path.exists(path), f"Missing product page: {fn}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    cnt = len(re.findall(re.escape(kw), content, re.IGNORECASE))
    print(f"{fn}: '{kw[:30]}...' count = {cnt}")
    assert cnt == 30, f"{fn} failed: expected 30, got {cnt}"

# 4. Verify Sitemap
sitemap_path = os.path.join(BASE_DIR, "sitemap.xml")
assert os.path.exists(sitemap_path), "sitemap.xml missing"
tree = ET.parse(sitemap_path)
root = tree.getroot()
locs = [elem.text for elem in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
print(f"sitemap.xml has {len(locs)} URLs.")
assert len(locs) >= 18, f"Sitemap has too few URLs: {len(locs)}"

# 5. Verify Downloads & Locker
assert os.path.exists(os.path.join(BASE_DIR, "downloads", "app.apk")), "downloads/app.apk missing"
assert os.path.exists(os.path.join(BASE_DIR, "downloads", "apkcrunch.apk")), "downloads/apkcrunch.apk missing"
assert os.path.exists(os.path.join(BASE_DIR, "js", "locker.js")), "js/locker.js missing"
assert os.path.exists(os.path.join(BASE_DIR, "js", "offers.json")), "js/offers.json missing"
assert os.path.exists(os.path.join(BASE_DIR, "css", "locker.css")), "css/locker.css missing"

print("\n==========================================")
print("ALL SEO CHECKS PASSED PERFECTLY (100% OK)")
print("==========================================")
