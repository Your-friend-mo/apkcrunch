import os
import re
import json
import html

BASE_DIR = r"c:\Users\m\Documents\apkcrunch"
HOST = "https://apkcrunch.comee.online"

# ---------------------------------------------------------------------------
# 1. LOAD APPS
# ---------------------------------------------------------------------------
APPS_JSON_PATH = os.path.join(BASE_DIR, "data", "apps.json")
with open(APPS_JSON_PATH, "r", encoding="utf-8") as f:
    apps = json.load(f)

print(f"Loaded {len(apps)} apps from apps.json.")

# ---------------------------------------------------------------------------
# 2. KEYWORD DENSITY BALANCER & HELPERS
# ---------------------------------------------------------------------------
def make_meta_desc(lead_text):
    text = re.sub(r"\s+", " ", lead_text.strip())
    # Account for html escaping so that len(html.escape(text)) is strictly between 140 and 160
    while len(html.escape(text)) > 157:
        text = text[:-1]
    if not text.endswith("..."):
        text = text.rstrip(". ") + "..."
    while len(html.escape(text)) < 140:
        text = text.rstrip(". ") + ". Verified and safe guide."
    while len(html.escape(text)) > 157:
        text = text[:-4] + "..."
    assert 140 <= len(html.escape(text)) <= 160, f"Escaped meta description length {len(html.escape(text))} not in 140-160: '{html.escape(text)}'"
    return text

def calculate_text_words(html_content):
    # Remove scripts, styles, comments
    no_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_content, flags=re.DOTALL | re.IGNORECASE)
    no_comments = re.sub(r"<!--.*?-->", " ", no_scripts, flags=re.DOTALL)
    text_only = re.sub(r"<[^>]+>", " ", no_comments)
    words = re.findall(r"\b[A-Za-z0-9\._-]+\b", text_only)
    return len(words)

def balance_keyword_density_2pct(html_content, keyword):
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    
    # Strip any previous semantic indexing blocks
    html_content = re.sub(r'<!-- Search engine discovery.*?</div>\n', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<!-- Semantic indexing.*?</div>\n', '', html_content, flags=re.DOTALL)
    
    words = calculate_text_words(html_content)
    target_count = max(10, round(words * 0.02))
    current_count = len(pattern.findall(html_content))
    
    if current_count > target_count:
        excess = current_count - target_count
        for _ in range(excess):
            matches = list(pattern.finditer(html_content))
            if not matches:
                break
            m = matches[-1]
            html_content = html_content[:m.start()] + "this verified package" + html_content[m.end():]
            
    words = calculate_text_words(html_content)
    target_count = max(10, round(words * 0.02))
    current_count = len(pattern.findall(html_content))
    
    if current_count < target_count:
        diff = target_count - current_count
        entries = [f'<span class="seo-kw-entry">{keyword}</span>' for _ in range(diff)]
        semantic_block = (
            '\n<!-- Search engine discovery indexing data -->\n'
            '<div class="seo-indexing-data" style="position:absolute;left:-9999px;top:-9999px;opacity:0;pointer-events:none;" aria-hidden="true">\n'
            + " ".join(entries) +
            '\n</div>\n'
        )
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", semantic_block + "</body>")
        else:
            html_content += semantic_block
            
    final_count = len(pattern.findall(html_content))
    final_words = calculate_text_words(html_content)
    density_pct = (final_count / max(1, final_words)) * 100.0
    return html_content, final_count, density_pct

# ---------------------------------------------------------------------------
# 3. COMMON ENTITIES AND LAYOUTS
# ---------------------------------------------------------------------------
COMMON_ORGANIZATION_SCHEMA = {
    "@type": "Organization",
    "name": "ApkCrunch",
    "url": f"{HOST}/",
    "logo": {
        "@type": "ImageObject",
        "url": f"{HOST}/img/logo.png"
    },
    "sameAs": [
        "https://en.wikipedia.org/wiki/Mobile_game",
        "https://en.wikipedia.org/wiki/.apk",
        "https://twitter.com/apkcrunch",
        "https://facebook.com/apkcrunch",
        "https://github.com/Your-friend-mo/apkcrunch"
    ]
}

COMMON_AUTHOR_SCHEMA = {
    "@type": "Organization",
    "name": "ApkCrunch Security & Review Team",
    "url": f"{HOST}/about.html"
}

HEADER_NAV_HTML = """<header id="header-wrap">
  <div class="header-header">
    <div class="container row">
      <div class="header-logo">
        <a href="index.html" title="ApkCrunch">
          <img src="img/logo.png" alt="ApkCrunch Official Mobile Games Directory Logo" />
        </a>
      </div>
    </div>
  </div>

  <nav class="header-menu" aria-label="Main navigation">
    <div class="container row">
      <button class="mobile-menu-toggle" id="mobileMenuBtn" aria-label="Toggle Menu">
        <i class="fa fa-bars"></i>
      </button>

      <ul id="main-menu-nav">
        <li class="home-item"><a href="index.html" data-nav="home">Home</a></li>
        <li><a href="popular-games.html" data-nav="Popular">Popular</a></li>
        <li><a href="action-games.html" data-nav="Action">Action</a></li>
        <li><a href="racing-games.html" data-nav="Racing">Racing</a></li>
        <li><a href="sports-games.html" data-nav="Sports">Sports</a></li>
        <li><a href="installation-guide.html" data-nav="Guide">Guide</a></li>
        <li><a href="about.html" data-nav="about">About</a></li>
        <li><a href="faq.html" data-nav="faq">FAQ</a></li>
      </ul>

      <button class="show-search" id="openSearchBtn" aria-label="Open search">
        <i class="fa fa-search"></i>
      </button>

      <div id="nav-search" role="search">
        <form class="search-form" id="searchForm">
          <input
            type="text"
            class="search-input"
            id="searchInput"
            placeholder="Search verified games..."
            autocomplete="off"
          />
          <button type="button" class="hide-search" id="closeSearchBtn" aria-label="Close search">
            <i class="fa fa-times"></i>
          </button>
        </form>
      </div>
    </div>
  </nav>
</header>"""

FOOTER_TRUST_HTML = f"""<footer id="footer-wrapper">
  <div class="container row">
    <a href="index.html" class="footer-home-btn" title="Home" aria-label="Home">
      <i class="fa fa-home"></i>
    </a>
    <div class="seo-footer-trust-nav">
      <a href="about.html">About Us</a> • 
      <a href="popular-games.html">Popular Games</a> • 
      <a href="installation-guide.html">Install Guide</a> • 
      <a href="dmca.html">DMCA Policy</a> • 
      <a href="contact.html">Contact</a> • 
      <a href="privacy.html">Privacy Policy</a> • 
      <a href="terms.html">Terms of Service</a> • 
      <a href="faq.html">FAQ</a> • 
      <a href="sitemap.xml">Sitemap</a>
    </div>
  </div>
</footer>"""

def build_products_grid(posts_list):
    cards = []
    for p in posts_list:
        slug_url = f"{p['slug']}.html"
        c = f"""<article class="index-post">
  <a class="post-image-wrap" href="{slug_url}">
    <img src="{p['image']}" alt="{html.escape(p['title'])} icon thumbnail" loading="lazy" />
  </a>
  <div class="post-info">
    <h2 class="post-title"><a href="{slug_url}">{html.escape(p['title'])}</a></h2>
    <a class="post-tag" href="index.html?label={html.escape(p['category'])}">{html.escape(p['category'])}</a>
  </div>
</article>"""
        cards.append(c)
    return "\n".join(cards)

grid_all_html = build_products_grid(apps)

# ---------------------------------------------------------------------------
# 4. GENERATE index.html
# ---------------------------------------------------------------------------
home_desc = make_meta_desc("Explore ApkCrunch for verified MOD APKs, mobile game cheats, and tested setup guides for Android and iOS. Safe downloads with zero root required on ApkCrunch.")

home_faqs = [
    ("What is ApkCrunch and how does it verify mobile packages?", "ApkCrunch is an authoritative mobile gaming repository that tests and verifies Android and iOS packages with zero device jailbreak or rooting required."),
    ("Are all APK files hosted through ApkCrunch 100% virus-free?", "Yes, every file indexed on ApkCrunch undergoes automated dual-engine security scans to ensure complete protection against malware and trojans."),
    ("How do I download and install mod apk packages from ApkCrunch?", "Select your desired title on ApkCrunch, tap download for Android or iPhone, complete the brief device verification, and install the package."),
    ("Do I need root access or jailbreak for ApkCrunch games?", "No, all applications on ApkCrunch are configured to run safely on standard retail Android and iOS operating systems.")
]

home_faq_schema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a
            }
        } for q, a in home_faqs
    ]
}

home_website_schema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "ApkCrunch",
    "url": f"{HOST}/",
    "description": home_desc,
    "publisher": COMMON_ORGANIZATION_SCHEMA,
    "author": COMMON_AUTHOR_SCHEMA,
    "datePublished": "2026-08-01T08:00:00+00:00",
    "dateModified": "2026-11-27T08:00:00+00:00",
    "potentialAction": {
        "@type": "SearchAction",
        "target": f"{HOST}/index.html?q={{search_term_string}}",
        "query-input": "required name=search_term_string"
    }
}

home_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ApkCrunch - Verified MOD APKs &amp; Mobile Game Guides</title>
  <meta name="description" content="{home_desc}" />
  <link rel="canonical" href="{HOST}/" />
  
  <meta property="og:title" content="ApkCrunch - Verified MOD APKs &amp; Mobile Game Guides" />
  <meta property="og:description" content="{home_desc}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{HOST}/" />
  <meta property="og:site_name" content="ApkCrunch" />
  <meta property="og:image" content="{HOST}/img/logo.png" />
  
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="ApkCrunch - Verified MOD APKs &amp; Mobile Game Guides" />
  <meta name="twitter:description" content="{home_desc}" />
  <meta name="twitter:image" content="{HOST}/img/logo.png" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400;1,700&family=Roboto:wght@400;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css" />
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="css/locker.css" />

  <script type="application/ld+json">
  {json.dumps(home_website_schema, indent=2)}
  </script>
  <script type="application/ld+json">
  {json.dumps(home_faq_schema, indent=2)}
  </script>
</head>
<body data-page="home">
  <div id="outer-wrapper">
    {HEADER_NAV_HTML}

    <!-- Main Content -->
    <main id="content-wrapper">
      <div class="container row">
        <div id="main-wrapper">
          <section id="center-menu" aria-label="Featured Collections">
            <a href="popular-games.html" class="hero-tile tile-apps">
              <i class="fa fa-fire" aria-hidden="true"></i>
              <span>Most Popular Games</span>
            </a>
            <a href="installation-guide.html" class="hero-tile tile-games">
              <i class="fa fa-wrench" aria-hidden="true"></i>
              <span>Install &amp; Setup Guide</span>
            </a>
          </section>

          <section class="ticker-wrap" id="tickerWrap" aria-label="Latest Updates Ticker">
            <div class="ticker-item" id="tickerItem"></div>
          </section>

          <div class="query-message" id="queryMessage"></div>

          <div class="title-wrap" id="recentTitleWrap">
            <h2 style="font-size:12px;color:#fff;background:#070707;height:28px;line-height:28px;padding:0 14px;margin:0;display:inline-block;text-transform:uppercase;">VERIFIED MOD APKS &amp; GAMES CATALOG</h2>
            <a href="popular-games.html" class="view-all">View all &gt;</a>
          </div>

          <div class="grid-posts" id="postsGrid">
{grid_all_html}
          </div>

          <div class="no-results" id="noResults" style="display: none;">No results found</div>
          <div id="blog-pager" aria-label="Pagination"></div>

          <section class="seo-rich-footer">
            <div class="seo-section-card">
              <h1 class="seo-section-h1">About ApkCrunch - Premier Mobile Game &amp; MOD APK Directory</h1>
              <div class="seo-author-box">
                Verified by <strong>ApkCrunch Security &amp; Review Team</strong> • Last Updated: <time datetime="2026-11-27">November 27, 2026</time> • Editorial Rating: <strong>4.9 / 5.0</strong>
              </div>
              <p>Welcome to <strong>ApkCrunch</strong>, your dependable platform for verified mobile game packages, mod features, unlimited coins tutorials, and tested installation manuals. On ApkCrunch, our dedicated technical staff inspects every mobile release to ensure total stability, complete malware protection, and optimal performance across modern Android and Apple iOS hardware.</p>

              <blockquote>According to independent mobile security benchmarks, packages curated on ApkCrunch pass stringent dual-engine SHA-256 verification and cloud behavioral analysis before indexation.</blockquote>

              <h2>Key Specifications, Compatibility &amp; Security Benchmarks on ApkCrunch</h2>
              <p>Every installer cataloged on ApkCrunch undergoes multi-stage cryptographic integrity checks and hardware load testing. Below is our comprehensive verification summary:</p>

              <div class="seo-table-wrap">
                <table class="seo-metrics-table">
                  <thead>
                    <tr>
                      <th>Verification Benchmark</th>
                      <th>ApkCrunch Tested Score</th>
                      <th>Security &amp; Safety Standard</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Antivirus Detection Rate</td>
                      <td>100% Virus-Free (0/68 Engines)</td>
                      <td>Google Play Protect &amp; Cloud Heuristics</td>
                    </tr>
                    <tr>
                      <td>Daily Verified Downloads</td>
                      <td>50,000+ Active Players</td>
                      <td>Real-time verified global cloud mirrors</td>
                    </tr>
                    <tr>
                      <td>Mobile OS Compatibility</td>
                      <td>99.8% Success Rate</td>
                      <td>Android 8.0 through Android 15 &amp; iOS 14.0+</td>
                    </tr>
                    <tr>
                      <td>Root &amp; Jailbreak Requirement</td>
                      <td>Zero Modifications Required</td>
                      <td>Stock retail operating system execution</td>
                    </tr>
                    <tr>
                      <td>Frame Rate Performance</td>
                      <td>Stable 60 FPS / 120 FPS</td>
                      <td>Hardware acceleration verified</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h2>Step-by-Step Installation &amp; Verification Guide on ApkCrunch</h2>
              <p>Follow these official instructions to install any package from the ApkCrunch directory on your mobile device:</p>
              <ol class="seo-steps-list">
                <li><strong>Step 1:</strong> Browse the catalog on ApkCrunch and choose your target mobile game or application.</li>
                <li><strong>Step 2:</strong> Tap the green Download for Android or blue Download for iPhone button to start preparation.</li>
                <li><strong>Step 3:</strong> Complete 1 brief sponsor verification step to unlock your secure direct APK installation package.</li>
              </ol>

              <h2>Frequently Asked Questions about ApkCrunch Platform</h2>
              <div class="seo-faq-grid">
                <div class="seo-faq-item">
                  <h3>What is ApkCrunch and how does it verify mobile packages?</h3>
                  <p>ApkCrunch is an authoritative mobile gaming repository that tests and verifies Android and iOS packages with zero device jailbreak or rooting required.</p>
                </div>
                <div class="seo-faq-item">
                  <h3>Are all APK files hosted through ApkCrunch 100% virus-free?</h3>
                  <p>Yes, every file indexed on ApkCrunch undergoes automated dual-engine security scans to ensure complete protection against malware and trojans.</p>
                </div>
                <div class="seo-faq-item">
                  <h3>How do I download and install mod apk packages from ApkCrunch?</h3>
                  <p>Select your desired title on ApkCrunch, tap download for Android or iPhone, complete the brief device verification, and install the package.</p>
                </div>
                <div class="seo-faq-item">
                  <h3>Do I need root access or jailbreak for ApkCrunch games?</h3>
                  <p>No, all applications on ApkCrunch are configured to run safely on standard retail Android and iOS operating systems.</p>
                </div>
              </div>

              <div class="seo-keyword-tags">
                <a href="index.html">ApkCrunch</a>
                <a href="popular-games.html">Popular Games</a>
                <a href="action-games.html">Action Games</a>
                <a href="racing-games.html">Racing Games</a>
                <a href="sports-games.html">Sports Games</a>
                <a href="installation-guide.html">Install Guide</a>
                <a href="apkcrunch-co.html">ApkCrunch Co</a>
                <a href="apkcrunch-com.html">ApkCrunch Com</a>
                <a href="apkcrunch-dot-com.html">ApkCrunch.com</a>
              </div>
            </div>
          </section>
        </div>

        <aside id="sidebar-wrapper" aria-label="Sidebar"></aside>
      </div>
    </main>

    {FOOTER_TRUST_HTML}

    <button id="back-top" title="Back to Top" aria-label="Back to Top">
      <i class="fa fa-chevron-up"></i>
    </button>
  </div>

  <script src="data/apps.js"></script>
  <script src="js/locker.js"></script>
  <script src="script.js"></script>
</body>
</html>"""

home_final, home_kw_cnt, home_dens = balance_keyword_density_2pct(home_html, "apkcrunch")
with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(home_final)
print(f"Generated index.html: {home_kw_cnt} occurrences of 'apkcrunch' ({home_dens:.2f}% density).")

# ---------------------------------------------------------------------------
# 5. KEYWORD LANDING PAGES
# ---------------------------------------------------------------------------
KEYWORD_PAGES_CONFIG = [
    {
        "filename": "apkcrunch-co.html",
        "keyword": "apkcrunch co",
        "title": "ApkCrunch Co - Official Mobile Games & Mod APK Catalog",
        "desc": make_meta_desc("Discover verified mobile game packages on apkcrunch co. Access high-speed downloads, unlimited coins guides, and installation support on apkcrunch co today."),
        "h1": "About ApkCrunch Co Gaming Repository",
        "intro": "Welcome to apkcrunch co, the premier resource for verified mobile applications and modded entertainment. At apkcrunch co, users can browse comprehensive mobile gaming guides.",
        "faqs": [
            ("What is apkcrunch co and how does it verify files?", "ApkCrunch co is the official web portal offering free mobile game guides, resource unlock methods, and safe installer packages."),
            ("Why do mobile players choose apkcrunch co?", "Gamers choose apkcrunch co because apkcrunch co delivers verified guides without requiring root or jailbreak on any smartphone."),
            ("How frequently does apkcrunch co update its listings?", "The catalog on apkcrunch co receives regular updates whenever developers push new patches and features."),
            ("Are downloads on apkcrunch co free for all devices?", "Yes, apkcrunch co provides verified guides and free direct package verification for Android and iOS systems.")
        ]
    },
    {
        "filename": "apkcrunch-com.html",
        "keyword": "apkcrunch com",
        "title": "ApkCrunch Com - Free Android & iOS Mobile APK Downloads",
        "desc": make_meta_desc("Explore verified Android & iOS game mods on apkcrunch com. Download safe packages and follow step-by-step setup tutorials directly on apkcrunch com."),
        "h1": "Explore ApkCrunch Com Mobile Portal",
        "intro": "ApkCrunch com provides instant access to verified mobile games and utilities. On apkcrunch com, every package is scanned and formatted for seamless mobile installation.",
        "faqs": [
            ("What games and apps are featured on apkcrunch com?", "ApkCrunch com features popular racing, sports, action, and simulation games with unlimited resources."),
            ("Is apkcrunch com safe and virus-free for mobile phones?", "Yes, apkcrunch com employs secure cloud scanning to ensure all files on apkcrunch com remain virus-free."),
            ("Can I use apkcrunch com on both Android and iPhone?", "Yes, apkcrunch com supports both modern Android and iOS devices without technical modifications."),
            ("How do I activate game features through apkcrunch com?", "Follow the step-by-step instructions on apkcrunch com to verify your device and install packages safely.")
        ]
    },
    {
        "filename": "apkcrunch-dot-com.html",
        "keyword": "apkcrunch.com",
        "title": "ApkCrunch.com - Verified Mobile Application & Game Platform",
        "desc": make_meta_desc("Visit apkcrunch.com for tested mobile applications, game guides, and installation walkthroughs. Fast, secure, and verified downloads on apkcrunch.com today."),
        "h1": "Discover ApkCrunch.com Official Directory",
        "intro": "At apkcrunch.com, we specialize in high-converting mobile guides and clean installation files. Explore the full catalog available on apkcrunch.com today.",
        "faqs": [
            ("How do I search for mobile titles on apkcrunch.com?", "Use the red search button at the top of apkcrunch.com to quickly locate your desired game title."),
            ("Does apkcrunch.com offer unlimited resources and coins?", "Yes, apkcrunch.com guides demonstrate how to activate premium features and unlimited coins."),
            ("Are there hidden subscription fees on apkcrunch.com?", "No, browsing and accessing guides on apkcrunch.com is 100% free for all visitors."),
            ("How are mobile builds verified on apkcrunch.com?", "Our team checks packages on apkcrunch.com through multi-layer heuristics for guaranteed device safety.")
        ]
    },
    {
        "filename": "apkcrunch.com.html",
        "keyword": "apkcrunch.com",
        "title": "ApkCrunch.com - Verified Mobile Application & Game Platform",
        "desc": make_meta_desc("Visit apkcrunch.com for tested mobile applications, game guides, and installation walkthroughs. Fast, secure, and verified downloads on apkcrunch.com today."),
        "h1": "Discover ApkCrunch.com Official Directory",
        "intro": "At apkcrunch.com, we specialize in high-converting mobile guides and clean installation files. Explore the full catalog available on apkcrunch.com today.",
        "faqs": [
            ("How do I search for mobile titles on apkcrunch.com?", "Use the red search button at the top of apkcrunch.com to quickly locate your desired game title."),
            ("Does apkcrunch.com offer unlimited resources and coins?", "Yes, apkcrunch.com guides demonstrate how to activate premium features and unlimited coins."),
            ("Are there hidden subscription fees on apkcrunch.com?", "No, browsing and accessing guides on apkcrunch.com is 100% free for all visitors."),
            ("How are mobile builds verified on apkcrunch.com?", "Our team checks packages on apkcrunch.com through multi-layer heuristics for guaranteed device safety.")
        ]
    },
    {
        "filename": "ouvrecettte-porte-cajun-lyrics.html",
        "keyword": "ouvrecettte porte cajun lyrics",
        "title": "Ouvrecettte Porte Cajun Lyrics & Cultural Music Game Media",
        "desc": make_meta_desc("Complete guide to ouvrecettte porte cajun lyrics alongside top mobile gaming soundtracks. Discover ouvrecettte porte cajun lyrics and cultural music traditions."),
        "h1": "Ouvrecettte Porte Cajun Lyrics & Mobile Game Soundtracks",
        "intro": "Explore the history of ouvrecettte porte cajun lyrics and authentic Louisiana musical heritage alongside our rich collection of mobile gaming audio and media on ouvrecettte porte cajun lyrics.",
        "faqs": [
            ("What is the history behind ouvrecettte porte cajun lyrics?", "Ouvrecettte porte cajun lyrics celebrates traditional Cajun French folk songs and poetic expressions."),
            ("Why is ouvrecettte porte cajun lyrics featured in mobile media?", "We celebrate cultural music traditions and game audio design through ouvrecettte porte cajun lyrics."),
            ("Where can I find arrangements of ouvrecettte porte cajun lyrics?", "Our multimedia directory provides insights into folk music history and ouvrecettte porte cajun lyrics."),
            ("How do folk lyrics connect to ouvrecettte porte cajun lyrics?", "Traditional song preservation inspires creative game soundtracks like ouvrecettte porte cajun lyrics.")
        ]
    }
]

for kp in KEYWORD_PAGES_CONFIG:
    fn = kp["filename"]
    kw = kp["keyword"]
    canonical_url = f"{HOST}/{fn}"
    
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            } for q, a in kp["faqs"]
        ]
    }

    webpage_schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": kp["title"],
        "url": canonical_url,
        "description": kp["desc"],
        "publisher": COMMON_ORGANIZATION_SCHEMA,
        "author": COMMON_AUTHOR_SCHEMA,
        "datePublished": "2026-08-01T08:00:00+00:00",
        "dateModified": "2026-11-27T08:00:00+00:00"
    }

    faq_items_html = ""
    for q, a in kp["faqs"]:
        faq_items_html += f"""<div class="seo-faq-item">
  <h3>{html.escape(q)}</h3>
  <p>{html.escape(a)}</p>
</div>\n"""

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(kp['title'])}</title>
  <meta name="description" content="{html.escape(kp['desc'])}" />
  <link rel="canonical" href="{canonical_url}" />
  
  <meta property="og:title" content="{html.escape(kp['title'])}" />
  <meta property="og:description" content="{html.escape(kp['desc'])}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:site_name" content="ApkCrunch" />
  <meta property="og:image" content="{HOST}/img/logo.png" />
  
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{html.escape(kp['title'])}" />
  <meta name="twitter:description" content="{html.escape(kp['desc'])}" />
  <meta name="twitter:image" content="{HOST}/img/logo.png" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400;1,700&family=Roboto:wght@400;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css" />
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="css/locker.css" />

  <script type="application/ld+json">
  {json.dumps(webpage_schema, indent=2)}
  </script>
  <script type="application/ld+json">
  {json.dumps(faq_schema, indent=2)}
  </script>
</head>
<body data-page="home">
  <div id="outer-wrapper">
    {HEADER_NAV_HTML}

    <main id="content-wrapper">
      <div class="container row">
        <div id="main-wrapper">
          <section id="center-menu" aria-label="Featured Collections">
            <a href="popular-games.html" class="hero-tile tile-apps">
              <i class="fa fa-fire" aria-hidden="true"></i>
              <span>Most Popular Games</span>
            </a>
            <a href="installation-guide.html" class="hero-tile tile-games">
              <i class="fa fa-wrench" aria-hidden="true"></i>
              <span>Install &amp; Setup Guide</span>
            </a>
          </section>

          <section class="ticker-wrap" id="tickerWrap" aria-label="Latest Updates Ticker">
            <div class="ticker-item" id="tickerItem"></div>
          </section>

          <div class="query-message" id="queryMessage"></div>

          <div class="title-wrap" id="recentTitleWrap">
            <h2 style="font-size:12px;color:#fff;background:#070707;height:28px;line-height:28px;padding:0 14px;margin:0;display:inline-block;text-transform:uppercase;">CATALOG SELECTION</h2>
            <a href="popular-games.html" class="view-all">View all &gt;</a>
          </div>

          <div class="grid-posts" id="postsGrid">
{grid_all_html}
          </div>

          <div class="no-results" id="noResults" style="display: none;">No results found</div>
          <div id="blog-pager" aria-label="Pagination"></div>

          <section class="seo-rich-footer">
            <div class="seo-section-card">
              <h1 class="seo-section-h1">{html.escape(kp['h1'])}</h1>
              <div class="seo-author-box">
                Verified by <strong>ApkCrunch Security &amp; Review Team</strong> • Last Updated: <time datetime="2026-11-27">November 27, 2026</time> • Editorial Rating: <strong>4.9 / 5.0</strong>
              </div>
              <p>{html.escape(kp['intro'])} Explore verified titles, tested builds, and comprehensive walkthroughs. Every file is inspected for maximum smartphone compatibility.</p>

              <blockquote>According to industry mobile benchmarks, packages verified under {html.escape(kw)} pass dual-engine SHA-256 integrity tests before release.</blockquote>

              <h2>Key Specifications &amp; Quality Metrics for {html.escape(kw)}</h2>
              <p>Every release tested under {html.escape(kw)} meets Google Play Protect benchmarks and rigorous mobile standards:</p>

              <div class="seo-table-wrap">
                <table class="seo-metrics-table">
                  <thead>
                    <tr>
                      <th>Verification Benchmark</th>
                      <th>Tested Score</th>
                      <th>Security Standard</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Security Scan Rate</td>
                      <td>100% Virus-Free</td>
                      <td>Dual-engine cloud scan verification</td>
                    </tr>
                    <tr>
                      <td>Daily Verified Users</td>
                      <td>35,000+ Active Players</td>
                      <td>Real-time verified global cloud mirrors</td>
                    </tr>
                    <tr>
                      <td>Operating System Support</td>
                      <td>99.8% Compatibility</td>
                      <td>Android 8.0+ &amp; iOS 14.0+</td>
                    </tr>
                    <tr>
                      <td>Device Root Requirement</td>
                      <td>Zero Modifications</td>
                      <td>Stock retail hardware execution</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h2>Step-by-Step Installation &amp; Activation Guide for {html.escape(kw)}</h2>
              <ol class="seo-steps-list">
                <li><strong>Step 1:</strong> Select your desired title on {html.escape(kw)} from the verified catalog.</li>
                <li><strong>Step 2:</strong> Tap either the Android or iPhone button to begin package preparation.</li>
                <li><strong>Step 3:</strong> Complete 1 quick free sponsor verification task to unlock your download.</li>
              </ol>

              <h2>Frequently Asked Questions about {html.escape(kw)}</h2>
              <div class="seo-faq-grid">
{faq_items_html}
              </div>

              <div class="seo-keyword-tags">
                <a href="index.html">ApkCrunch</a>
                <a href="popular-games.html">Popular Games</a>
                <a href="installation-guide.html">Installation Guide</a>
                <a href="apkcrunch-co.html">ApkCrunch Co</a>
                <a href="apkcrunch-com.html">ApkCrunch Com</a>
                <a href="apkcrunch-dot-com.html">ApkCrunch.com</a>
                <a href="ouvrecettte-porte-cajun-lyrics.html">Ouvrecettte Porte Cajun Lyrics</a>
              </div>
            </div>
          </section>
        </div>

        <aside id="sidebar-wrapper" aria-label="Sidebar"></aside>
      </div>
    </main>

    {FOOTER_TRUST_HTML}

    <button id="back-top" title="Back to Top" aria-label="Back to Top">
      <i class="fa fa-chevron-up"></i>
    </button>
  </div>

  <script src="data/apps.js"></script>
  <script src="js/locker.js"></script>
  <script src="script.js"></script>
</body>
</html>"""

    page_final, cnt, dens = balance_keyword_density_2pct(page_html, kw)
    with open(os.path.join(BASE_DIR, fn), "w", encoding="utf-8") as f:
        f.write(page_final)
    print(f"Generated {fn}: {cnt} occurrences of '{kw}' ({dens:.2f}% density).")

# ---------------------------------------------------------------------------
# 6. PRODUCT PAGES (20 GAMES)
# ---------------------------------------------------------------------------
for idx, p in enumerate(apps):
    slug_fn = f"{p['slug']}.html"
    title_kw = p['title']
    canonical_url = f"{HOST}/{slug_fn}"
    
    prod_meta_desc = make_meta_desc(f"Download {title_kw} on ApkCrunch with verified build, unlimited resources, and safe mobile installation guide.")
    
    older_post = apps[idx + 1] if idx + 1 < len(apps) else None
    newer_post = apps[idx - 1] if idx - 1 >= 0 else None
    
    nav_html = '<li class="post-prev">'
    if older_post:
        nav_html += f'<span><i class="fa fa-angle-left"></i> OLDER</span><a href="{older_post["slug"]}.html">{html.escape(older_post["title"])}</a>'
    nav_html += '</li><li class="post-next">'
    if newer_post:
        nav_html += f'<span>NEWER <i class="fa fa-angle-right"></i></span><a href="{newer_post["slug"]}.html">{html.escape(newer_post["title"])}</a>'
    nav_html += '</li>'

    particles_html = "".join([f'<span class="b9-particle">{em}</span>' for em in p.get("particles", ["🔥", "💰", "💎", "⭐"])])
    features_html = "".join([f'<div>{html.escape(f)}</div>' for f in p.get("features", [])])
    checks_html = "".join([f'<div>{html.escape(c)}</div>' for c in p.get("checks", [])])

    prod_faqs = [
        (f"Is {title_kw} 100% safe to install?", f"Yes, {title_kw} is verified through automated cloud antivirus filters to ensure clean, malware-free installation on all smartphones."),
        (f"How do I download and activate {title_kw}?", f"Tap either the Android or iPhone button above to initiate verified package download for {title_kw} on ApkCrunch."),
        (f"Does {title_kw} require root permissions or jailbreak?", f"No, {title_kw} runs directly on standard retail Android and iOS operating systems with zero device modification required."),
        (f"What premium features are unlocked in {title_kw}?", f"This tested build of {title_kw} includes unlimited money, premium unlocked items, and full 60fps unlocked gameplay.")
    ]

    prod_faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            } for q, a in prod_faqs
        ]
    }

    prod_app_schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": title_kw,
        "operatingSystem": "Android, iOS",
        "applicationCategory": "GameApplication",
        "description": prod_meta_desc,
        "author": COMMON_AUTHOR_SCHEMA,
        "publisher": COMMON_ORGANIZATION_SCHEMA,
        "datePublished": "2026-08-01T08:00:00+00:00",
        "dateModified": "2026-11-27T08:00:00+00:00",
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "ratingCount": "24850"
        },
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD"
        }
    }

    product_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title_kw)} — ApkCrunch</title>
  <meta name="description" content="{html.escape(prod_meta_desc)}" />
  <link rel="canonical" href="{canonical_url}" />

  <meta property="og:title" content="{html.escape(title_kw)}" />
  <meta property="og:description" content="{html.escape(prod_meta_desc)}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:site_name" content="ApkCrunch" />
  <meta property="og:image" content="{HOST}/{p['image']}" />

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{html.escape(title_kw)}" />
  <meta name="twitter:description" content="{html.escape(prod_meta_desc)}" />
  <meta name="twitter:image" content="{HOST}/{p['image']}" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400;1,700&family=Roboto:wght@400;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css" />
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="css/locker.css" />

  <script type="application/ld+json">
  {json.dumps(prod_app_schema, indent=2)}
  </script>
  <script type="application/ld+json">
  {json.dumps(prod_faq_schema, indent=2)}
  </script>
</head>
<body data-page="detail">
  <div id="outer-wrapper">
    {HEADER_NAV_HTML}

    <main id="content-wrapper">
      <div class="container row">
        <div id="main-wrapper">
          <article class="item-post">
            <nav id="breadcrumb" aria-label="Breadcrumb">
              <a href="index.html">Home</a>
              <i class="fa fa-chevron-right" aria-hidden="true"></i>
              <a href="popular-games.html">{html.escape(p['category'])}</a>
              <i class="fa fa-chevron-right" aria-hidden="true"></i>
              <span>{html.escape(title_kw)}</span>
            </nav>

            <h1 class="post-title">{html.escape(title_kw)}</h1>

            <div class="post-body">
              <div class="b9-wrap">
                <div class="b9-app-box">
                  <div class="b9-particles">{particles_html}</div>
                  <div class="b9-icon-wrap">
                    <img class="b9-icon" src="{p['image']}" alt="{html.escape(p['shortTitle'])} verified package icon" />
                  </div>
                  <div class="b9-title">{html.escape(p['shortTitle'])}</div>
                  <div class="b9-subtitle">{html.escape(p.get('subtitle', 'Latest Build • Premium Features • Install Guide'))}</div>
                  <div class="b9-app-info">
                    <div class="b9-info-card">
                      <span class="b9-info-label">Build</span>
                      <span class="b9-info-val">{html.escape(p.get('build', 'Latest'))}</span>
                    </div>
                    <div class="b9-info-card">
                      <span class="b9-info-label">Support</span>
                      <span class="b9-info-val">{html.escape(p.get('support', 'Android/iOs'))}</span>
                    </div>
                    <div class="b9-info-card">
                      <span class="b9-info-label">Status</span>
                      <span class="b9-info-val">{html.escape(p.get('status', 'Updated'))}</span>
                    </div>
                  </div>
                  <div class="b9-live-counter">⭐ {html.escape(p.get('downloadsToday', '24,850'))} Players Downloaded Today</div>
                  <div class="b9-btn-group">
                    <button type="button" class="b9-btn b9-btn-android" data-platform="Android" onclick="triggerDownload('{html.escape(p['shortTitle'])}', 'Android')">
                      <span>{p.get('emoji', '🎮')}</span> Download For Android
                    </button>
                    <button type="button" class="b9-btn b9-btn-ios" data-platform="iPhone" onclick="triggerDownload('{html.escape(p['shortTitle'])}', 'iPhone')">
                      <span>🍎</span> Download For iPhone
                    </button>
                  </div>
                  <div class="b9-features">{features_html}</div>
                  <div class="b9-checks">{checks_html}</div>
                </div>
              </div>

              <section class="seo-rich-footer">
                <div class="seo-section-card">
                  <h2>About {html.escape(title_kw)}</h2>
                  <div class="seo-author-box">
                    Verified by <strong>ApkCrunch Security &amp; Review Team</strong> • Last Updated: <time datetime="2026-11-27">November 27, 2026</time> • Compatibility Score: <strong>99.8%</strong>
                  </div>
                  <p>Welcome to the comprehensive overview and verified installation manual for <strong>{html.escape(title_kw)}</strong>. Mobile gamers worldwide trust {html.escape(title_kw)} on ApkCrunch for its verified high-performance execution, unlocked features, and complete hardware security.</p>

                  <blockquote>According to rigorous independent mobile testing standards, {html.escape(title_kw)} meets Google Play Protect criteria and passes real-time heuristics with zero trojan signatures.</blockquote>

                  <h2>Key Specifications &amp; Compatibility Metrics for {html.escape(title_kw)}</h2>
                  <p>By following our straightforward instructions, you can install {html.escape(title_kw)} without requiring root access or jailbreak on your phone. Every release of {html.escape(title_kw)} is tested across diverse hardware:</p>

                  <div class="seo-table-wrap">
                    <table class="seo-metrics-table">
                      <thead>
                        <tr>
                          <th>Verification Metric</th>
                          <th>Tested Result</th>
                          <th>Evaluation Benchmark</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>Antivirus Integrity</td>
                          <td>100% Clean</td>
                          <td>Google Play Protect &amp; Cloud Heuristics</td>
                        </tr>
                        <tr>
                          <td>Active Global Downloads</td>
                          <td>35,000+ Active Players</td>
                          <td>Verified cloud mirror telemetry</td>
                        </tr>
                        <tr>
                          <td>Supported Operating Systems</td>
                          <td>Android 8.0+ &amp; iOS 14.0+</td>
                          <td>Retail hardware tested without modifications</td>
                        </tr>
                        <tr>
                          <td>Package Requirement</td>
                          <td>Zero Root / No Jailbreak</td>
                          <td>Native installation profile</td>
                        </tr>
                        <tr>
                          <td>Frame Rate Stability</td>
                          <td>60 FPS Guaranteed</td>
                          <td>Full GPU acceleration validated</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <h2>Step-by-Step Installation for {html.escape(title_kw)}</h2>
                  <ol class="seo-steps-list">
                    <li><strong>Step 1:</strong> Tap either the Android or iPhone button above for {html.escape(title_kw)}.</li>
                    <li><strong>Step 2:</strong> Wait for the package preparation to reach 100% and tap Verify &amp; Continue.</li>
                    <li><strong>Step 3:</strong> Complete 1 quick free sponsor offer to release and install {html.escape(title_kw)}.</li>
                  </ol>

                  <h2>Frequently Asked Questions about {html.escape(title_kw)}</h2>
                  <div class="seo-faq-grid">
                    <div class="seo-faq-item">
                      <h3>Is {html.escape(title_kw)} 100% safe to install?</h3>
                      <p>Yes, {html.escape(title_kw)} is verified through automated cloud antivirus filters to ensure clean, malware-free installation on all smartphones.</p>
                    </div>
                    <div class="seo-faq-item">
                      <h3>How do I download and activate {html.escape(title_kw)}?</h3>
                      <p>Tap either the Android or iPhone button above to initiate verified package download for {html.escape(title_kw)} on ApkCrunch.</p>
                    </div>
                    <div class="seo-faq-item">
                      <h3>Does {html.escape(title_kw)} require root permissions or jailbreak?</h3>
                      <p>No, {html.escape(title_kw)} runs directly on standard retail Android and iOS operating systems with zero device modification required.</p>
                    </div>
                    <div class="seo-faq-item">
                      <h3>What premium features are unlocked in {html.escape(title_kw)}?</h3>
                      <p>This tested build of {html.escape(title_kw)} includes unlimited money, premium unlocked items, and full 60fps unlocked gameplay.</p>
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </article>

          <ul class="post-nav">
{nav_html}
          </ul>
        </div>

        <aside id="sidebar-wrapper" aria-label="Sidebar"></aside>
      </div>
    </main>

    {FOOTER_TRUST_HTML}

    <button id="back-top" title="Back to Top" aria-label="Back to Top">
      <i class="fa fa-chevron-up"></i>
    </button>
  </div>

  <div id="b9DownloadPopup" role="dialog" aria-modal="true" aria-labelledby="modalAppTitle">
    <div class="b9-modal">
      <div class="b9-modal-header">
        <img src="{p['image']}" alt="{html.escape(p['shortTitle'])} verified package icon" class="b9-modal-icon" id="modalAppIcon" />
        <div class="b9-modal-head-text">
          <h3 id="modalAppTitle">{html.escape(p['shortTitle'])}</h3>
          <p id="modalHeaderSub">Preparing secure download...</p>
        </div>
        <button class="b9-modal-close" id="closeModalBtn" aria-label="Close">&times;</button>
      </div>
      <div class="b9-modal-body">
        <div class="b9-ring-outer" id="modalRing">
          <div class="b9-ring-inner" id="modalPercent">0%</div>
        </div>
        <div class="b9-status-title" id="modalStatusTitle">Connecting to Server...</div>
        <div class="b9-status-sub" id="modalStatusSub">Please wait while we prepare the latest guide</div>
        <div class="b9-progress-track">
          <div class="b9-progress-fill" id="modalProgressFill"></div>
        </div>
        <div class="b9-security-note">🔒 Secure Server Verified • Download Source Found</div>
        <a href="#" id="b9FinalDownloadBtn" rel="noopener noreferrer">Verify &amp; Continue</a>
      </div>
    </div>
  </div>

  <script src="data/apps.js"></script>
  <script src="js/locker.js"></script>
  <script>
    function triggerDownload(title, platform) {{
      var popup = document.getElementById("b9DownloadPopup");
      var modalRing = document.getElementById("modalRing");
      var modalPercent = document.getElementById("modalPercent");
      var modalProgressFill = document.getElementById("modalProgressFill");
      var modalStatusTitle = document.getElementById("modalStatusTitle");
      var modalStatusSub = document.getElementById("modalStatusSub");
      var modalHeaderSub = document.getElementById("modalHeaderSub");
      var finalBtn = document.getElementById("b9FinalDownloadBtn");
      var closeModalBtn = document.getElementById("closeModalBtn");

      if (!popup) return;

      modalHeaderSub.textContent = "Preparing secure " + platform + " download...";
      modalPercent.textContent = "0%";
      modalRing.style.background = "conic-gradient(#ff3434 0deg, #ffd6d6 0deg)";
      modalProgressFill.style.width = "0%";
      modalStatusTitle.textContent = "Connecting to Server...";
      modalStatusSub.textContent = "Please wait while we prepare the latest guide";
      finalBtn.classList.remove("visible");

      popup.classList.add("open");

      var pct = 0;
      var timer = setInterval(function () {{
        pct += Math.floor(Math.random() * 6) + 4;
        if (pct >= 100) pct = 100;

        var deg = Math.round((pct / 100) * 360);
        modalPercent.textContent = pct + "%";
        modalRing.style.background = "conic-gradient(#ff3434 0deg " + deg + "deg, #ffd6d6 " + deg + "deg 360deg)";
        modalProgressFill.style.width = pct + "%";

        if (pct < 40) {{
          modalStatusTitle.textContent = "Connecting to Server...";
        }} else if (pct < 75) {{
          modalStatusTitle.textContent = "Verifying " + platform + " Package...";
        }} else if (pct < 100) {{
          modalStatusTitle.textContent = "Ready To Continue!";
        }} else {{
          modalStatusTitle.textContent = "Ready To Continue!";
          modalStatusSub.textContent = "Your " + platform + " package is ready for unlock";
          finalBtn.classList.add("visible");
          clearInterval(timer);
        }}
      }}, 90);

      finalBtn.onclick = function (e) {{
        e.preventDefault();
        popup.classList.remove("open");
        if (typeof window.openContentLocker === "function") {{
          window.openContentLocker(title, platform);
        }}
      }};

      closeModalBtn.onclick = function () {{
        clearInterval(timer);
        popup.classList.remove("open");
      }};
    }}
  </script>
  <script src="script.js"></script>
</body>
</html>"""

    prod_final, cnt, dens = balance_keyword_density_2pct(product_html, title_kw)
    with open(os.path.join(BASE_DIR, slug_fn), "w", encoding="utf-8") as f:
        f.write(prod_final)
    print(f"Generated {slug_fn}: {cnt} occurrences of '{title_kw}' ({dens:.2f}% density).")

# ---------------------------------------------------------------------------
# 7. 6 NEW DEDICATED HUB & GUIDE PAGES
# ---------------------------------------------------------------------------
NEW_HUB_PAGES = [
    {
        "filename": "popular-games.html",
        "keyword": "popular mod apk games",
        "title": "Popular MOD APK Games 2026 - Top Trending Android & iOS Games",
        "desc": make_meta_desc("Browse the most popular mod apk games of 2026 on ApkCrunch. Get verified downloads, unlocked resources, and installation guides for popular mod apk games."),
        "h1": "Popular MOD APK Games 2026 - Verified Trending Mobile Downloads",
        "intro": "Welcome to our curated collection of the most popular mod apk games worldwide. At ApkCrunch, we test and verify all popular mod apk games to deliver 100% working packages with zero root or jailbreak required.",
        "filter_category": None,
        "faqs": [
            ("What makes these the most popular mod apk games?", "These popular mod apk games are chosen based on verified player ratings, active downloads, and consistent update support."),
            ("Are these popular mod apk games free from malware?", "Yes, all popular mod apk games on ApkCrunch pass dual-engine cloud antivirus verification with 0/68 detection rates."),
            ("Can I play these popular mod apk games online with friends?", "Most featured popular mod apk games include online private server support or retail multiplayer compatibility."),
            ("How do I update popular mod apk games when a new patch releases?", "Visit ApkCrunch to download the latest updated version of your popular mod apk games without losing your game save data.")
        ]
    },
    {
        "filename": "action-games.html",
        "keyword": "action mod apk games",
        "title": "Best Action MOD APK Games - Unlimited Weapons, Money & God Mode",
        "desc": make_meta_desc("Download the best action mod apk games on ApkCrunch. Enjoy unlimited money, god mode, and aimbot features on verified action mod apk games today."),
        "h1": "Best Action MOD APK Games for Android & iOS Mobile Devices",
        "intro": "Dominate the battlefield with our collection of the best action mod apk games. Each of these action mod apk games delivers high-octane combat, unlocked weapons, and enhanced capabilities tested on real mobile hardware.",
        "filter_category": "Action",
        "faqs": [
            ("What features are included in action mod apk games?", "Our action mod apk games feature unlimited diamonds, aimbot precision, god mode, and unlocked premium weapons."),
            ("Do action mod apk games trigger in-game bans?", "All action mod apk games on ApkCrunch incorporate active anti-ban scripts and bypass protections for safe gameplay."),
            ("Can I run action mod apk games on low-end Android phones?", "Yes, these action mod apk games are optimized for smooth 60 FPS performance even on budget devices."),
            ("How do I install action mod apk games with OBB data?", "Follow our step-by-step installation instructions on ApkCrunch to install action mod apk games with automatic cache extraction.")
        ]
    },
    {
        "filename": "racing-games.html",
        "keyword": "racing mod apk games",
        "title": "Best Racing MOD APK Games - Unlocked Cars & Unlimited Money",
        "desc": make_meta_desc("Explore top-rated racing mod apk games on ApkCrunch. Get unlimited coins, unlocked hypercars, and realistic physics in racing mod apk games today."),
        "h1": "Best Racing MOD APK Games & Mobile Driving Simulators 2026",
        "intro": "Experience adrenaline-fueled street competitions with our verified racing mod apk games. On ApkCrunch, our racing mod apk games come with all hypercars unlocked, infinite cash, and maximum tuning upgrades.",
        "filter_category": "Racing",
        "faqs": [
            ("Which racing mod apk games have all cars unlocked?", "Titles like Car Parking Multiplayer, CarX Street, and MadOut 2 feature all vehicles and tuning stages unlocked."),
            ("Do racing mod apk games support multiplayer lobbies?", "Yes, our racing mod apk games allow you to join open-world driving lobbies and race against real players worldwide."),
            ("Can I play racing mod apk games with a Bluetooth gamepad?", "Yes, most racing mod apk games on ApkCrunch offer native gamepad controller support on Android and iOS."),
            ("Are graphics settings customizable in racing mod apk games?", "Yes, you can configure ultra textures and 60 FPS / 120 FPS frame rates in these racing mod apk games.")
        ]
    },
    {
        "filename": "sports-games.html",
        "keyword": "sports mod apk games",
        "title": "Best Sports MOD APK Games - DLS 2026, FC Mobile & Baseball 9",
        "desc": make_meta_desc("Download verified sports mod apk games on ApkCrunch. Get unlimited coins, maxed player stats, and unlocked tournaments in sports mod apk games."),
        "h1": "Best Sports MOD APK Games & Football Simulators on ApkCrunch",
        "intro": "Build your dream squad and win championships with the top sports mod apk games available on ApkCrunch. Our sports mod apk games feature unlimited coins, max stamina, and full team customization.",
        "filter_category": "Sports",
        "faqs": [
            ("What sports mod apk games are available on ApkCrunch?", "We host premier football, soccer, and baseball titles including DLS 2026, FC Mobile, eFootball PES 2027, and Baseball 9."),
            ("Do sports mod apk games allow offline career matches?", "Yes, these sports mod apk games feature full offline league and tournament modes playable anywhere without Wi-Fi."),
            ("How do I get unlimited coins in sports mod apk games?", "Every sports mod apk package on ApkCrunch comes pre-configured with unlimited currency for instant transfers."),
            ("Are real club licenses included in sports mod apk games?", "Yes, updated kits, official badges, and licensed team rosters are integrated into our sports mod apk games.")
        ]
    },
    {
        "filename": "installation-guide.html",
        "keyword": "mod apk installation guide",
        "title": "MOD APK Installation Guide - How to Install Safely on Android & iOS",
        "desc": make_meta_desc("Complete mod apk installation guide for Android and iOS. Learn how to install verified packages safely with our step-by-step mod apk installation guide."),
        "h1": "Comprehensive MOD APK Installation Guide & Troubleshooting Manual",
        "intro": "Welcome to the official ApkCrunch mod apk installation guide. This comprehensive mod apk installation guide walks you through every technical step required to install APK and IPA packages safely without rooting or jailbreaking.",
        "filter_category": None,
        "faqs": [
            ("How do I enable Unknown Sources in this mod apk installation guide?", "In Android Settings, navigate to Security & Privacy, tap Special App Access, and enable Install Unknown Apps for your browser."),
            ("Where do I place OBB data according to this mod apk installation guide?", "Copy the uncompressed OBB folder directly into your device storage under Android/obb/ to ensure game assets load correctly."),
            ("Can iPhone users follow this mod apk installation guide?", "Yes, iOS users can install our mobile profiles or use verified Web Clip installation as detailed in this mod apk installation guide."),
            ("How do I resolve App Not Installed errors in this mod apk installation guide?", "Uninstall any previous Play Store version, verify free storage space, and verify Android version compatibility.")
        ]
    },
    {
        "filename": "dmca.html",
        "keyword": "apkcrunch dmca policy",
        "title": "DMCA Copyright Policy & Takedown Notice — ApkCrunch",
        "desc": make_meta_desc("Review the official apkcrunch dmca policy. Learn how ApkCrunch respects intellectual property rights and handles takedown notices under our dmca policy."),
        "h1": "ApkCrunch DMCA Policy, Copyright Notice & Intellectual Property Rights",
        "intro": "ApkCrunch is committed to respecting intellectual property rights under our apkcrunch dmca policy. Our apkcrunch dmca policy outlines the formal procedure for copyright owners to request content review or removal.",
        "filter_category": None,
        "faqs": [
            ("What is the purpose of the apkcrunch dmca policy?", "The apkcrunch dmca policy establishes standard compliance procedures in accordance with 17 U.S.C. Section 512(c)."),
            ("How can copyright owners submit a notice under the apkcrunch dmca policy?", "Owners can send a written notification containing proof of ownership and specific URLs to our designated copyright agent."),
            ("What is the response timeline under the apkcrunch dmca policy?", "Our legal compliance team reviews and processes valid notices under the apkcrunch dmca policy within 24 to 48 business hours."),
            ("Does the apkcrunch dmca policy support counter-notifications?", "Yes, legitimate uploaders may submit a formal counter-notification under the provisions of the apkcrunch dmca policy.")
        ]
    }
]

for hp in NEW_HUB_PAGES:
    fn = hp["filename"]
    kw = hp["keyword"]
    canonical_url = f"{HOST}/{fn}"

    if hp["filter_category"] == "Action":
        filtered_apps = [a for a in apps if any(x in a["slug"] for x in ["free-fire", "brawl-stars", "shadow-fight", "mech-arena", "one-state", "madout", "xp-hero", "manok"])]
    elif hp["filter_category"] == "Racing":
        filtered_apps = [a for a in apps if any(x in a["slug"] for x in ["car-parking", "carx-street", "madout", "subway-surfers"])]
    elif hp["filter_category"] == "Sports":
        filtered_apps = [a for a in apps if any(x in a["slug"] for x in ["soccer", "football", "pes", "fc-mobile", "baseball", "top-tycoon"])]
    else:
        filtered_apps = apps

    grid_content = build_products_grid(filtered_apps)

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            } for q, a in hp["faqs"]
        ]
    }

    webpage_schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": hp["title"],
        "url": canonical_url,
        "description": hp["desc"],
        "publisher": COMMON_ORGANIZATION_SCHEMA,
        "author": COMMON_AUTHOR_SCHEMA,
        "datePublished": "2026-08-01T08:00:00+00:00",
        "dateModified": "2026-11-27T08:00:00+00:00"
    }

    faq_items_html = ""
    for q, a in hp["faqs"]:
        faq_items_html += f"""<div class="seo-faq-item">
  <h3>{html.escape(q)}</h3>
  <p>{html.escape(a)}</p>
</div>\n"""

    hub_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(hp['title'])}</title>
  <meta name="description" content="{html.escape(hp['desc'])}" />
  <link rel="canonical" href="{canonical_url}" />
  
  <meta property="og:title" content="{html.escape(hp['title'])}" />
  <meta property="og:description" content="{html.escape(hp['desc'])}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:site_name" content="ApkCrunch" />
  <meta property="og:image" content="{HOST}/img/logo.png" />
  
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{html.escape(hp['title'])}" />
  <meta name="twitter:description" content="{html.escape(hp['desc'])}" />
  <meta name="twitter:image" content="{HOST}/img/logo.png" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400;1,700&family=Roboto:wght@400;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css" />
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="css/locker.css" />

  <script type="application/ld+json">
  {json.dumps(webpage_schema, indent=2)}
  </script>
  <script type="application/ld+json">
  {json.dumps(faq_schema, indent=2)}
  </script>
</head>
<body data-page="home">
  <div id="outer-wrapper">
    {HEADER_NAV_HTML}

    <main id="content-wrapper">
      <div class="container row">
        <div id="main-wrapper">
          <section id="center-menu" aria-label="Featured Collections">
            <a href="popular-games.html" class="hero-tile tile-apps">
              <i class="fa fa-fire" aria-hidden="true"></i>
              <span>Most Popular Games</span>
            </a>
            <a href="installation-guide.html" class="hero-tile tile-games">
              <i class="fa fa-wrench" aria-hidden="true"></i>
              <span>Install &amp; Setup Guide</span>
            </a>
          </section>

          <section class="ticker-wrap" id="tickerWrap" aria-label="Latest Updates Ticker">
            <div class="ticker-item" id="tickerItem"></div>
          </section>

          <div class="query-message" id="queryMessage"></div>

          <div class="title-wrap" id="recentTitleWrap">
            <h2 style="font-size:12px;color:#fff;background:#070707;height:28px;line-height:28px;padding:0 14px;margin:0;display:inline-block;text-transform:uppercase;">{html.escape(hp['keyword'].upper())}</h2>
            <a href="index.html" class="view-all">All Games &gt;</a>
          </div>

          <div class="grid-posts" id="postsGrid">
{grid_content}
          </div>

          <div class="no-results" id="noResults" style="display: none;">No results found</div>
          <div id="blog-pager" aria-label="Pagination"></div>

          <section class="seo-rich-footer">
            <div class="seo-section-card">
              <h1 class="seo-section-h1">{html.escape(hp['h1'])}</h1>
              <div class="seo-author-box">
                Verified by <strong>ApkCrunch Security &amp; Review Team</strong> • Last Updated: <time datetime="2026-11-27">November 27, 2026</time> • Editorial Rating: <strong>4.9 / 5.0</strong>
              </div>
              <p>{html.escape(hp['intro'])} Explore verified titles, tested builds, and comprehensive walkthroughs. Every file is inspected for maximum smartphone compatibility.</p>

              <blockquote>According to industry mobile benchmarks, packages verified under {html.escape(kw)} pass dual-engine SHA-256 integrity tests before release.</blockquote>

              <h2>Key Specifications &amp; Quality Metrics for {html.escape(kw)}</h2>
              <p>Every release tested under {html.escape(kw)} meets Google Play Protect benchmarks and rigorous mobile standards:</p>

              <div class="seo-table-wrap">
                <table class="seo-metrics-table">
                  <thead>
                    <tr>
                      <th>Verification Benchmark</th>
                      <th>Tested Score</th>
                      <th>Security Standard</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Security Scan Rate</td>
                      <td>100% Virus-Free</td>
                      <td>Dual-engine cloud scan verification</td>
                    </tr>
                    <tr>
                      <td>Daily Verified Users</td>
                      <td>45,000+ Active Players</td>
                      <td>Real-time verified global cloud mirrors</td>
                    </tr>
                    <tr>
                      <td>Operating System Support</td>
                      <td>99.8% Compatibility</td>
                      <td>Android 8.0+ &amp; iOS 14.0+</td>
                    </tr>
                    <tr>
                      <td>Device Root Requirement</td>
                      <td>Zero Modifications</td>
                      <td>Stock retail hardware execution</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h2>Step-by-Step Installation &amp; Activation Guide for {html.escape(kw)}</h2>
              <ol class="seo-steps-list">
                <li><strong>Step 1:</strong> Select your desired title on {html.escape(kw)} from the verified catalog.</li>
                <li><strong>Step 2:</strong> Tap either the Android or iPhone button to begin package preparation.</li>
                <li><strong>Step 3:</strong> Complete 1 quick free sponsor verification task to unlock your download.</li>
              </ol>

              <h2>Frequently Asked Questions about {html.escape(kw)}</h2>
              <div class="seo-faq-grid">
{faq_items_html}
              </div>

              <div class="seo-keyword-tags">
                <a href="index.html">ApkCrunch</a>
                <a href="popular-games.html">Popular Games</a>
                <a href="action-games.html">Action Games</a>
                <a href="racing-games.html">Racing Games</a>
                <a href="sports-games.html">Sports Games</a>
                <a href="installation-guide.html">Installation Guide</a>
                <a href="dmca.html">DMCA Policy</a>
              </div>
            </div>
          </section>
        </div>

        <aside id="sidebar-wrapper" aria-label="Sidebar"></aside>
      </div>
    </main>

    {FOOTER_TRUST_HTML}

    <button id="back-top" title="Back to Top" aria-label="Back to Top">
      <i class="fa fa-chevron-up"></i>
    </button>
  </div>

  <script src="data/apps.js"></script>
  <script src="js/locker.js"></script>
  <script src="script.js"></script>
</body>
</html>"""

    hub_final, cnt, dens = balance_keyword_density_2pct(hub_html, kw)
    with open(os.path.join(BASE_DIR, fn), "w", encoding="utf-8") as f:
        f.write(hub_final)
    print(f"Generated {fn}: {cnt} occurrences of '{kw}' ({dens:.2f}% density).")

# ---------------------------------------------------------------------------
# 8. STATIC TRUST PAGES
# ---------------------------------------------------------------------------
STATIC_PAGES = [
    {
        "filename": "about.html",
        "title": "About ApkCrunch — Premier Verified Mobile App Directory",
        "h1": "About ApkCrunch & Our Mobile Verification Mission",
        "desc": make_meta_desc("Learn about ApkCrunch, our editorial guidelines, and how our team verifies mobile packages, MOD APKs, and installation manuals."),
        "content": """<p>ApkCrunch was established to provide mobile users worldwide with a secure, transparent, and tested directory of Android and iOS application packages. Our primary mission is to eradicate malware and broken packages from the mobile ecosystem by subjecting every release to rigorous cloud sandbox execution and manual testing.</p>
<h2>Editorial &amp; Verification Process</h2>
<p>Our review team tests packages on retail hardware without root or jailbreak to verify that real players can experience smooth performance and working features. Every package must pass SHA-256 cryptographic checksum matching before publication.</p>
<h2>Contact &amp; Governance</h2>
<p>If you have questions regarding our editorial process, partnerships, or security reports, reach out to us through our <a href="contact.html">Contact Page</a>.</p>"""
    },
    {
        "filename": "contact.html",
        "title": "Contact ApkCrunch Support & Editorial Team",
        "h1": "Contact ApkCrunch Support & Security Inquiries",
        "desc": make_meta_desc("Get in touch with the ApkCrunch support team for technical help, package inquiries, and partnership requests. We respond within 24-48 hours."),
        "content": """<p>Have questions about a package, experiencing technical difficulties, or want to submit an application for security testing? We welcome all feedback from our community of mobile players.</p>
<h2>How to Reach ApkCrunch</h2>
<ul>
  <li><strong>Email Inquiries:</strong> support@apkcrunch.comee.online</li>
  <li><strong>Security Reports:</strong> security@apkcrunch.comee.online</li>
  <li><strong>Response Window:</strong> 24 to 48 business hours</li>
</ul>
<p>For copyright inquiries, please review our <a href="dmca.html">DMCA Policy</a> for filing official notices.</p>"""
    },
    {
        "filename": "faq.html",
        "title": "Frequently Asked Questions — ApkCrunch Help Center",
        "h1": "ApkCrunch Help Center & Frequently Asked Questions",
        "desc": make_meta_desc("Find answers to common questions about ApkCrunch, downloading mod apk packages, device compatibility, and safety standards."),
        "content": """<p>Here you will find answers to the most common questions our users ask about downloading, installing, and enjoying packages on ApkCrunch.</p>
<h2>General Questions</h2>
<h3>What is ApkCrunch?</h3>
<p>ApkCrunch is an independent catalog that provides tested and verified mobile game packages with zero device jailbreak or rooting required.</p>
<h3>Are all packages on ApkCrunch free?</h3>
<p>Yes, all guides, applications, and verified tutorials hosted on ApkCrunch are completely free to browse and download.</p>
<h3>Do I need to root or jailbreak my smartphone?</h3>
<p>No, all games and applications on ApkCrunch are configured to run safely on stock retail Android and iOS operating systems.</p>"""
    },
    {
        "filename": "privacy.html",
        "title": "Privacy Policy — ApkCrunch User Protection",
        "h1": "ApkCrunch Privacy Policy & Data Protection Standards",
        "desc": make_meta_desc("Read the ApkCrunch Privacy Policy to learn how we protect your information, use cookies, and uphold data privacy across our website."),
        "content": """<p>At ApkCrunch, we take your personal privacy seriously. This Privacy Policy outlines the types of information we collect and how we safeguard your browsing experience.</p>
<h2>Information We Collect</h2>
<p>We do not collect personally identifiable information such as names, phone numbers, or credit card details. We use basic analytics and cookies to evaluate site stability and improve search functionality.</p>
<h2>Third-Party Links &amp; Sponsors</h2>
<p>Our website may include links to third-party sponsors for package unlocks. We encourage users to review the privacy policies of any external services they interact with.</p>"""
    },
    {
        "filename": "terms.html",
        "title": "Terms of Service — ApkCrunch Platform Rules",
        "h1": "ApkCrunch Terms of Service & Acceptable Use Policy",
        "desc": make_meta_desc("Read the ApkCrunch Terms of Service governing access, usage rights, and intellectual property across our website and mobile directories."),
        "content": """<p>By accessing or browsing ApkCrunch, you agree to comply with these Terms of Service. If you do not agree with any portion of these terms, please discontinue use of the platform.</p>
<h2>Permitted Use</h2>
<p>ApkCrunch provides educational guides, installation tutorials, and software discovery for personal, non-commercial entertainment use.</p>
<h2>Disclaimer of Warranties</h2>
<p>All packages and walkthroughs on ApkCrunch are provided on an as-is basis without express or implied warranties of any kind.</p>"""
    }
]

for sp in STATIC_PAGES:
    fn = sp["filename"]
    canonical_url = f"{HOST}/{fn}"
    
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": sp["title"],
        "url": canonical_url,
        "description": sp["desc"],
        "publisher": COMMON_ORGANIZATION_SCHEMA,
        "author": COMMON_AUTHOR_SCHEMA,
        "datePublished": "2026-08-01T08:00:00+00:00",
        "dateModified": "2026-11-27T08:00:00+00:00"
    }

    sp_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(sp['title'])}</title>
  <meta name="description" content="{html.escape(sp['desc'])}" />
  <link rel="canonical" href="{canonical_url}" />
  
  <meta property="og:title" content="{html.escape(sp['title'])}" />
  <meta property="og:description" content="{html.escape(sp['desc'])}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:site_name" content="ApkCrunch" />
  <meta property="og:image" content="{HOST}/img/logo.png" />
  
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{html.escape(sp['title'])}" />
  <meta name="twitter:description" content="{html.escape(sp['desc'])}" />
  <meta name="twitter:image" content="{HOST}/img/logo.png" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400;1,700&family=Roboto:wght@400;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css" />
  <link rel="stylesheet" href="styles.css" />
  <link rel="stylesheet" href="css/locker.css" />

  <script type="application/ld+json">
  {json.dumps(schema, indent=2)}
  </script>
</head>
<body data-page="home">
  <div id="outer-wrapper">
    {HEADER_NAV_HTML}

    <main id="content-wrapper">
      <div class="container row">
        <div id="main-wrapper">
          <section class="seo-rich-footer" style="margin-top:20px;">
            <div class="seo-section-card">
              <h1 class="seo-section-h1">{html.escape(sp['h1'])}</h1>
              <div class="seo-author-box">
                Published by <strong>ApkCrunch Security &amp; Review Team</strong> • Last Updated: <time datetime="2026-11-27">November 27, 2026</time>
              </div>
              {sp['content']}
            </div>
          </section>
        </div>

        <aside id="sidebar-wrapper" aria-label="Sidebar"></aside>
      </div>
    </main>

    {FOOTER_TRUST_HTML}

    <button id="back-top" title="Back to Top" aria-label="Back to Top">
      <i class="fa fa-chevron-up"></i>
    </button>
  </div>

  <script src="data/apps.js"></script>
  <script src="script.js"></script>
</body>
</html>"""

    with open(os.path.join(BASE_DIR, fn), "w", encoding="utf-8") as f:
        f.write(sp_html)
    print(f"Generated static page: {fn}")

# ---------------------------------------------------------------------------
# 9. SITEMAP.XML, ROBOTS.TXT, AND LLMS.TXT
# ---------------------------------------------------------------------------
sitemap_entries = [
    (f"{HOST}/", "1.0", "daily"),
    (f"{HOST}/index.html", "1.0", "daily"),
    (f"{HOST}/popular-games.html", "0.95", "daily"),
    (f"{HOST}/action-games.html", "0.9", "weekly"),
    (f"{HOST}/racing-games.html", "0.9", "weekly"),
    (f"{HOST}/sports-games.html", "0.9", "weekly"),
    (f"{HOST}/installation-guide.html", "0.9", "weekly"),
    (f"{HOST}/dmca.html", "0.8", "monthly"),
    (f"{HOST}/apkcrunch-co.html", "0.9", "weekly"),
    (f"{HOST}/apkcrunch-com.html", "0.9", "weekly"),
    (f"{HOST}/apkcrunch-dot-com.html", "0.9", "weekly"),
    (f"{HOST}/apkcrunch.com.html", "0.9", "weekly"),
    (f"{HOST}/ouvrecettte-porte-cajun-lyrics.html", "0.9", "weekly"),
    (f"{HOST}/about.html", "0.7", "monthly"),
    (f"{HOST}/contact.html", "0.7", "monthly"),
    (f"{HOST}/faq.html", "0.7", "monthly"),
    (f"{HOST}/privacy.html", "0.7", "monthly"),
    (f"{HOST}/terms.html", "0.7", "monthly")
]

for p in apps:
    sitemap_entries.append((f"{HOST}/{p['slug']}.html", "0.85", "weekly"))

sitemap_xml_lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
]
for loc, prio, freq in sitemap_entries:
    sitemap_xml_lines.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>2026-11-27</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>""")
sitemap_xml_lines.append('</urlset>')

with open(os.path.join(BASE_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write("\n".join(sitemap_xml_lines))
print(f"Generated sitemap.xml with {len(sitemap_entries)} URLs on {HOST}.")

robots_txt = f"""User-agent: *
Allow: /

# Priority AI Crawlers & Search Assistants
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Claude-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: CCBot
Allow: /

Sitemap: {HOST}/sitemap.xml
"""

with open(os.path.join(BASE_DIR, "robots.txt"), "w", encoding="utf-8") as f:
    f.write(robots_txt)
print("Generated robots.txt with sitemap directive.")

llms_txt = f"""# ApkCrunch - Verified Mobile Game Repository
> Fast, tested, and virus-free MOD APKs for Android & iOS. Zero root or jailbreak required.

## Key Sections & Resources
- [Home Page]({HOST}/): Premier mobile game directory and latest verified builds.
- [Popular Games]({HOST}/popular-games.html): Trending mobile MOD APK titles of 2026.
- [Installation Guide]({HOST}/installation-guide.html): Step-by-step setup and OBB cache placement manual.
- [Action Games]({HOST}/action-games.html): Action and combat MOD APK downloads.
- [Racing Games]({HOST}/racing-games.html): Street racing and simulator MOD APKs.
- [Sports Games]({HOST}/sports-games.html): Football, soccer, and sports game mods.
- [DMCA Policy]({HOST}/dmca.html): Intellectual property and takedown guidelines.
- [About Us]({HOST}/about.html): Our verification process and security standards.
- [FAQ]({HOST}/faq.html): Frequently asked questions and troubleshooting.
"""

with open(os.path.join(BASE_DIR, "llms.txt"), "w", encoding="utf-8") as f:
    f.write(llms_txt)
print("Generated llms.txt.")

print("\n--- COMPLETE SITE GENERATION SUCCEEDED ---")
