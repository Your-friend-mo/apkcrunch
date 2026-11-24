(function () {
  "use strict";

  const posts = window.APKCRUNCH_POSTS || [];
  const config = window.APKCRUNCH_CONFIG || {
    siteName: "ApkCrunch.co",
    downloadRedirectUrl: "#download-ready",
    postsPerPage: 7
  };

  /* =========================================================
     International Normalization, Levenshtein & Fuzzy Search
     ========================================================= */
  function normalizeText(str) {
    if (!str) return "";
    return str
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "") // remove diacritics/accents (e.g. é -> e, ü -> u, ñ -> n)
      .toLowerCase()
      .replace(/ß/g, "ss")
      .replace(/ø/g, "o")
      .replace(/æ/g, "ae")
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function levenshtein(s1, s2) {
    if (s1 === s2) return 0;
    const len1 = s1.length;
    const len2 = s2.length;
    if (len1 === 0) return len2;
    if (len2 === 0) return len1;

    let prev = new Array(len2 + 1);
    let curr = new Array(len2 + 1);
    for (let j = 0; j <= len2; j++) prev[j] = j;

    for (let i = 1; i <= len1; i++) {
      curr[0] = i;
      const c1 = s1.charCodeAt(i - 1);
      for (let j = 1; j <= len2; j++) {
        const c2 = s2.charCodeAt(j - 1);
        const cost = c1 === c2 ? 0 : 1;
        curr[j] = Math.min(
          prev[j] + 1,       // deletion
          curr[j - 1] + 1,   // insertion
          prev[j - 1] + cost // substitution
        );
      }
      for (let j = 0; j <= len2; j++) prev[j] = curr[j];
    }
    return prev[len2];
  }

  const SYNONYMS = {
    futbol: ["football", "soccer"],
    futebol: ["football", "soccer"],
    voetbal: ["football", "soccer"],
    fussball: ["football", "soccer"],
    calcio: ["football", "soccer"],
    beisbol: ["baseball"],
    pelota: ["baseball"],
    carreras: ["racing", "car", "street", "parking"],
    course: ["racing", "car"],
    carros: ["car", "parking", "street"],
    coches: ["car", "parking", "street"],
    voiture: ["car"],
    auto: ["car"],
    autos: ["car"],
    dinero: ["money"],
    argent: ["money"],
    geld: ["money"],
    monedas: ["coins"],
    gemas: ["gems"],
    diamantes: ["diamonds"],
    rooster: ["manok", "pula"],
    gallo: ["manok", "pula"],
    chicken: ["manok", "pula"],
    dls: ["dream", "league", "soccer"],
    pes: ["efootball", "pes"],
    cpm: ["car", "parking", "multiplayer"],
    fifa: ["fc", "mobile"],
    fut: ["fc", "mobile"],
    "1": ["one", "1st"],
    one: ["1"],
    "2": ["two", "2nd"],
    two: ["2"],
    "3": ["three", "3rd"],
    three: ["3"],
    "9": ["nine"],
    nine: ["9"]
  };

  function scorePost(post, rawQuery) {
    const query = normalizeText(rawQuery);
    if (!query) return 0;

    const titleNorm = normalizeText(post.title);
    const shortTitleNorm = normalizeText(post.shortTitle);
    const catNorm = normalizeText(post.category);
    const featNorm = (post.features || []).map(normalizeText).join(" ");
    const checksNorm = (post.checks || []).map(normalizeText).join(" ");
    const subtitleNorm = normalizeText(post.subtitle || "");

    const titleWords = titleNorm.split(" ");
    const shortWords = shortTitleNorm.split(" ");

    // 1. Single character special handling
    if (query.length === 1) {
      let s = 0;
      const variants = [query].concat(SYNONYMS[query] || []);

      for (let i = 0; i < variants.length; i++) {
        const v = variants[i];
        if (shortWords.indexOf(v) !== -1) return 3000;
        if (titleWords.indexOf(v) !== -1) return 2500;
      }

      if (shortTitleNorm.indexOf(query) === 0) return 2000;
      if (titleNorm.indexOf(query) === 0) return 1800;

      for (let i = 0; i < shortWords.length; i++) {
        if (shortWords[i].indexOf(query) === 0) return 1500;
      }
      for (let i = 0; i < titleWords.length; i++) {
        if (titleWords[i].indexOf(query) === 0) return 1200;
      }

      if (shortTitleNorm.indexOf(query) !== -1) s += 300;
      else if (titleNorm.indexOf(query) !== -1) s += 200;
      else if (catNorm.indexOf(query) !== -1) s += 100;
      else if ((featNorm + " " + checksNorm).indexOf(query) !== -1) s += 50;

      return s;
    }

    // 2. Exact full substring match boosts
    if (shortTitleNorm === query) return 4000;
    if (titleNorm === query) return 3800;
    if (shortTitleNorm.indexOf(query) === 0) return 3400;
    if (titleNorm.indexOf(query) === 0) return 3200;
    if (shortTitleNorm.indexOf(query) !== -1) return 2500;
    if (titleNorm.indexOf(query) !== -1) return 2000;
    if (catNorm.indexOf(query) !== -1) return 1200;

    // 3. Collect post tokens
    const allWords = (titleNorm + " " + shortTitleNorm + " " + catNorm + " " + featNorm + " " + checksNorm + " " + subtitleNorm).split(" ");
    const postWords = [];
    for (let i = 0; i < allWords.length; i++) {
      const w = allWords[i];
      if (w.length > 0 && postWords.indexOf(w) === -1) {
        postWords.push(w);
      }
    }

    const rawQueryTokens = query.split(" ").filter(function (w) { return w.length > 0; });
    const queryTokensExpanded = rawQueryTokens.map(function (tok) {
      const list = [tok];
      if (SYNONYMS[tok]) {
        for (let j = 0; j < SYNONYMS[tok].length; j++) {
          list.push(SYNONYMS[tok][j]);
        }
      }
      return list;
    });

    let totalScore = 0;
    let matchedTokensCount = 0;

    for (let i = 0; i < queryTokensExpanded.length; i++) {
      const tokVariants = queryTokensExpanded[i];
      let bestTokScore = 0;

      for (let j = 0; j < tokVariants.length; j++) {
        const qTok = tokVariants[j];
        for (let k = 0; k < postWords.length; k++) {
          const pTok = postWords[k];
          if (pTok === qTok) {
            bestTokScore = Math.max(bestTokScore, 300);
          } else if (pTok.indexOf(qTok) === 0) {
            bestTokScore = Math.max(bestTokScore, 200);
          } else if (qTok.length >= 3 && pTok.indexOf(qTok) !== -1) {
            bestTokScore = Math.max(bestTokScore, 150);
          } else if (qTok.length >= 3) {
            // Typo tolerance
            const lenDiff = Math.abs(pTok.length - qTok.length);
            let maxDist = 1;
            if (qTok.length >= 8) maxDist = 3;
            else if (qTok.length >= 5) maxDist = 2;

            if (lenDiff <= maxDist) {
              const dist = levenshtein(qTok, pTok);
              if (dist <= maxDist) {
                const sim = 140 - dist * 40;
                bestTokScore = Math.max(bestTokScore, sim);
              }
            }
          }
        }
      }

      if (bestTokScore > 0) {
        totalScore += bestTokScore;
        matchedTokensCount++;
      }
    }

    // Bonus when all query tokens matched
    if (matchedTokensCount === rawQueryTokens.length && matchedTokensCount > 0) {
      totalScore += 600 * matchedTokensCount;
    }

    return totalScore;
  }

  /* =========================================================
     Shared UI: Search Overlay, Mobile Nav, Back-to-Top
     ========================================================= */
  const openSearchBtn = document.getElementById("openSearchBtn");
  const closeSearchBtn = document.getElementById("closeSearchBtn");
  const navSearch = document.getElementById("nav-search");
  const searchInput = document.getElementById("searchInput");
  const searchForm = document.getElementById("searchForm");
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const mainMenuNav = document.getElementById("main-menu-nav");
  const backTopBtn = document.getElementById("back-top");

  const currentFile = (window.location.pathname.split("/").pop() || "index.html").split("?")[0];
  const isListingPage = [
    "index.html",
    "apkcrunch-co.html",
    "apkcrunch-com.html",
    "apkcrunch-dot-com.html",
    "apkcrunch.com.html",
    "ouvrecettte-porte-cajun-lyrics.html",
    ""
  ].indexOf(currentFile) !== -1;

  const targetBase = isListingPage ? (currentFile || "index.html") : "index.html";

  // Dropdown Auto-Suggest state
  let searchResultsDropdown = null;
  let activeSuggestIndex = -1;

  function initSearchUI() {
    if (!navSearch) return;

    searchResultsDropdown = document.getElementById("nav-search-results");
    if (!searchResultsDropdown) {
      searchResultsDropdown = document.createElement("div");
      searchResultsDropdown.id = "nav-search-results";
      navSearch.appendChild(searchResultsDropdown);
    }

    function closeSearch() {
      navSearch.classList.remove("open");
      hideSuggest();
    }

    function openSearch() {
      navSearch.classList.add("open");
      if (searchInput) {
        searchInput.focus();
        const curVal = searchInput.value.trim();
        if (curVal.length > 0) {
          renderSuggestions(curVal);
        }
      }
    }

    function hideSuggest() {
      if (searchResultsDropdown) {
        searchResultsDropdown.style.display = "none";
        searchResultsDropdown.innerHTML = "";
      }
      activeSuggestIndex = -1;
    }

    function renderSuggestions(query) {
      if (!searchResultsDropdown || !query) {
        hideSuggest();
        return;
      }

      const scored = posts
        .map(function (p) {
          return { post: p, score: scorePost(p, query) };
        })
        .filter(function (x) {
          return x.score > 0;
        })
        .sort(function (a, b) {
          return b.score - a.score;
        });

      activeSuggestIndex = -1;

      if (scored.length === 0) {
        searchResultsDropdown.innerHTML =
          '<div class="search-suggest-empty">' +
            '<i class="fa fa-search" aria-hidden="true"></i>' +
            '<div>No games or apps found matching "<strong>' + escapeHtml(query) + '</strong>"</div>' +
            '<div style="font-size:11.5px;color:#777777;margin-top:5px;">Try checking your spelling or search for popular terms (e.g. Sports, Racing, Money).</div>' +
          '</div>';
        searchResultsDropdown.style.display = "block";
        return;
      }

      const topItems = scored.slice(0, 6);
      let html = "";
      topItems.forEach(function (item, idx) {
        const p = item.post;
        const targetHref = p.slug + ".html";
        html +=
          '<a class="search-suggest-item" href="' + targetHref + '" data-index="' + idx + '">' +
            '<img class="suggest-thumb" src="' + escapeHtml(p.image) + '" alt="' + escapeHtml(p.shortTitle) + '" loading="lazy" />' +
            '<div class="suggest-info">' +
              '<div class="suggest-title">' + escapeHtml(p.title) + '</div>' +
              '<div class="suggest-meta">' +
                '<span class="suggest-badge">' + escapeHtml(p.category) + '</span>' +
                '<span class="suggest-sub">' + escapeHtml(p.subtitle || "Mod APK • Free Download") + '</span>' +
              '</div>' +
            '</div>' +
            '<i class="fa fa-chevron-right suggest-arrow" aria-hidden="true"></i>' +
          '</a>';
      });

      html +=
        '<div class="search-suggest-footer">' +
          '<span>Found <strong>' + scored.length + '</strong> match' + (scored.length === 1 ? '' : 'es') + '</span>' +
          '<span>Press <kbd>Enter</kbd> to view all</span>' +
        '</div>';

      searchResultsDropdown.innerHTML = html;
      searchResultsDropdown.style.display = "block";
    }

    if (openSearchBtn) {
      openSearchBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        openSearch();
      });
    }

    if (closeSearchBtn) {
      closeSearchBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        closeSearch();
      });
    }

    document.addEventListener("click", function (e) {
      if (navSearch && navSearch.classList.contains("open")) {
        if (!navSearch.contains(e.target) && e.target !== openSearchBtn && !openSearchBtn.contains(e.target)) {
          closeSearch();
        }
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && navSearch && navSearch.classList.contains("open")) {
        closeSearch();
      }
    });

    if (searchInput) {
      searchInput.addEventListener("input", function () {
        const val = searchInput.value.trim();
        if (val.length > 0) {
          renderSuggestions(val);
        } else {
          hideSuggest();
        }
      });

      searchInput.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
          closeSearch();
          return;
        }

        if (!searchResultsDropdown || searchResultsDropdown.style.display === "none") return;

        const items = searchResultsDropdown.querySelectorAll(".search-suggest-item");
        if (items.length === 0) return;

        if (e.key === "ArrowDown") {
          e.preventDefault();
          activeSuggestIndex = (activeSuggestIndex + 1) % items.length;
          updateActiveSuggest(items);
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          activeSuggestIndex = (activeSuggestIndex - 1 + items.length) % items.length;
          updateActiveSuggest(items);
        } else if (e.key === "Enter") {
          if (activeSuggestIndex >= 0 && activeSuggestIndex < items.length) {
            e.preventDefault();
            const targetUrl = items[activeSuggestIndex].getAttribute("href");
            if (targetUrl) {
              window.location.href = targetUrl;
            } else {
              items[activeSuggestIndex].click();
            }
          }
        }
      });
    }

    function updateActiveSuggest(items) {
      items.forEach(function (el, idx) {
        if (idx === activeSuggestIndex) {
          el.classList.add("active");
          el.scrollIntoView({ block: "nearest" });
        } else {
          el.classList.remove("active");
        }
      });
    }

    if (searchForm && searchInput) {
      searchForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const q = searchInput.value.trim();
        const dest = q ? (targetBase + "?q=" + encodeURIComponent(q)) : targetBase;
        window.location.href = dest;
      });
    }
  }

  initSearchUI();

  if (mobileMenuBtn && mainMenuNav) {
    mobileMenuBtn.addEventListener("click", function () {
      mainMenuNav.classList.toggle("mobile-open");
    });
  }

  if (backTopBtn) {
    backTopBtn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* =========================================================
     Helpers
     ========================================================= */
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getParams() {
    return new URLSearchParams(window.location.search);
  }

  /* =========================================================
     Home / Category / Search / Static Pages
     ========================================================= */
  function initHomePage() {
    const params = getParams();
    const label = params.get("label");
    const query = params.get("q");
    const staticPage = params.get("page");
    const viewAll = params.get("view") === "all";
    const pageNum = Math.max(1, parseInt(params.get("p") || "1", 10) || 1);

    const centerMenu = document.getElementById("center-menu");
    const tickerWrap = document.getElementById("tickerWrap");
    const queryMessage = document.getElementById("queryMessage");
    const recentTitleWrap = document.getElementById("recentTitleWrap");
    const staticPageBox = document.getElementById("staticPageBox");
    const postsGrid = document.getElementById("postsGrid");
    const noResults = document.getElementById("noResults");
    const blogPager = document.getElementById("blog-pager");

    // Static pages (About / FAQ via query param)
    if (staticPage === "about" || staticPage === "faq") {
      if (centerMenu) centerMenu.style.display = "none";
      if (tickerWrap) tickerWrap.style.display = "none";
      if (recentTitleWrap) recentTitleWrap.style.display = "none";
      if (postsGrid) postsGrid.style.display = "none";
      if (blogPager) blogPager.style.display = "none";
      if (staticPageBox) {
        staticPageBox.style.display = "block";
        if (staticPage === "about") {
          document.title = "About — " + config.siteName;
          staticPageBox.innerHTML =
            "<h1>About ApkCrunch.co</h1>" +
            "<p>Welcome to <strong>ApkCrunch.co</strong>, your destination for the latest Android and iOS game guides, updates, and featured mobile collections.</p>" +
            "<p>We regularly review and curate popular mobile games and applications with clear setup guides and compatibility details.</p>";
        } else {
          document.title = "FAQ — " + config.siteName;
          staticPageBox.innerHTML =
            "<h1>Frequently Asked Questions</h1>" +
            '<div class="faq-item"><h4>How do I find a specific game or app?</h4><p>Click the red search icon on the top-right of the navigation bar and enter the game or app title.</p></div>' +
            '<div class="faq-item"><h4>Are both Android and iOS supported?</h4><p>Yes, each game detail page includes dedicated download and setup options for both Android and iPhone devices.</p></div>' +
            '<div class="faq-item"><h4>How often are listings updated?</h4><p>We update our catalog regularly whenever new builds and features are released.</p></div>';
        }
      }
      return;
    }

    // Filter posts
    let filtered = posts.slice();
    const isHomePage1 = !label && !query && !viewAll && pageNum === 1;

    if (label) {
      filtered = posts.filter(function (p) {
        return p.category.toLowerCase() === label.toLowerCase();
      });
      document.title = label + " — " + config.siteName;
      if (queryMessage) {
        queryMessage.classList.add("visible");
        queryMessage.innerHTML =
          'Showing posts with the label <strong>"' +
          escapeHtml(label) +
          '"</strong> <a href="' + targetBase + '">Show all</a>';
      }
    } else if (query) {
      filtered = posts
        .map(function (p) {
          return { post: p, score: scorePost(p, query) };
        })
        .filter(function (x) {
          return x.score > 0;
        })
        .sort(function (a, b) {
          return b.score - a.score;
        })
        .map(function (x) {
          return x.post;
        });

      document.title = 'Search "' + query + '" — ' + config.siteName;
      if (searchInput) searchInput.value = query;
      if (queryMessage) {
        queryMessage.classList.add("visible");
        const countStr = filtered.length === 1 ? "1 result" : filtered.length + " results";
        queryMessage.innerHTML =
          'Showing posts matching the search for <strong>"' +
          escapeHtml(query) +
          '"</strong> (' + countStr + ') <a href="' + targetBase + '">Show all</a>';
      }
    }

    // Show/hide hero & ticker exactly like apkcrunch.co (only on Homepage Page 1)
    if (!isHomePage1) {
      if (centerMenu) centerMenu.style.display = "none";
      if (tickerWrap) tickerWrap.style.display = "none";
    } else {
      initTicker();
    }

    if ((label || query) && recentTitleWrap) {
      recentTitleWrap.style.display = "none";
    }

    // Pagination calculation
    const perPage = viewAll ? 10 : config.postsPerPage;
    const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
    const currentPage = Math.min(pageNum, totalPages);
    const startIdx = (currentPage - 1) * perPage;
    const pageItems = filtered.slice(startIdx, startIdx + perPage);

    if (pageItems.length === 0) {
      if (postsGrid) postsGrid.innerHTML = "";
      if (noResults) {
        noResults.style.display = "block";
        if (query) {
          noResults.innerHTML =
            '<div style="text-align:center;padding:30px 15px;">' +
              '<i class="fa fa-search" style="font-size:32px;color:#bf353a;margin-bottom:12px;display:block;"></i>' +
              '<h3 style="color:#ffffff;margin-bottom:8px;font-size:18px;">No games or apps found</h3>' +
              '<p style="color:#888888;font-size:14px;max-width:440px;margin:0 auto 15px;">We couldn\'t find any results matching "<strong>' + escapeHtml(query) + '</strong>". Try checking your spelling or search for popular terms like <em>Sports</em>, <em>Racing</em>, or <em>Money</em>.</p>' +
              '<a href="' + targetBase + '" class="b9-btn b9-btn-android" style="display:inline-block;padding:8px 18px;font-size:13px;width:auto;text-decoration:none;">View All Games</a>' +
            '</div>';
        } else {
          noResults.textContent = "No results found";
        }
      }
      if (blogPager) blogPager.innerHTML = "";
      return;
    }

    if (noResults) noResults.style.display = "none";
    if (postsGrid) {
      postsGrid.innerHTML = pageItems
        .map(function (post) {
          const href = post.slug + ".html";
          const catHref = targetBase + "?label=" + encodeURIComponent(post.category);
          return (
            '<article class="index-post">' +
              '<a class="post-image-wrap" href="' + href + '">' +
                '<img src="' + escapeHtml(post.image) + '" alt="' + escapeHtml(post.title) + '" loading="lazy" />' +
              "</a>" +
              '<div class="post-info">' +
                '<h2 class="post-title"><a href="' + href + '">' + escapeHtml(post.title) + "</a></h2>" +
                '<a class="post-tag" href="' + catHref + '">' + escapeHtml(post.category) + "</a>" +
              "</div>" +
            "</article>"
          );
        })
        .join("");
    }

    // Render pagination
    if (blogPager) {
      if (totalPages <= 1) {
        blogPager.innerHTML = "";
      } else {
        const buildPageUrl = function (p) {
          const nextParams = new URLSearchParams(window.location.search);
          if (p === 1) {
            nextParams.delete("p");
          } else {
            nextParams.set("p", String(p));
          }
          const qs = nextParams.toString();
          return targetBase + (qs ? "?" + qs : "");
        };

        let html = "";
        if (currentPage > 1) {
          html +=
            '<a class="pager-btn" href="' +
            buildPageUrl(currentPage - 1) +
            '" aria-label="Previous page"><i class="fa fa-angle-left"></i></a>';
        }
        for (let i = 1; i <= totalPages; i++) {
          html +=
            '<a class="pager-btn' +
            (i === currentPage ? " active" : "") +
            '" href="' +
            buildPageUrl(i) +
            '">' +
            i +
            "</a>";
        }
        if (currentPage < totalPages) {
          html +=
            '<a class="pager-btn" href="' +
            buildPageUrl(currentPage + 1) +
            '" aria-label="Next page"><i class="fa fa-angle-right"></i></a>';
        }
        blogPager.innerHTML = html;
      }
    }
  }

  /* =========================================================
     Auto-Rotating News Ticker
     ========================================================= */
  function initTicker() {
    const tickerItem = document.getElementById("tickerItem");
    if (!tickerItem || posts.length === 0) return;

    let idx = 0;

    function renderTicker() {
      const p = posts[idx];
      const href = p.slug + ".html";
      tickerItem.innerHTML =
        '<a href="' + href + '">' +
          '<img class="ticker-thumb" src="' + escapeHtml(p.image) + '" alt="' + escapeHtml(p.shortTitle) + '" />' +
        "</a>" +
        '<div class="ticker-meta">' +
          '<a class="ticker-title" href="' + href + '">' + escapeHtml(p.title) + "</a>" +
          '<span class="ticker-date">' + escapeHtml(p.author) + " - " + escapeHtml(p.date) + "</span>" +
        "</div>";
      // Re-trigger animation
      tickerItem.style.animation = "none";
      void tickerItem.offsetWidth;
      tickerItem.style.animation = "";
    }

    renderTicker();
    setInterval(function () {
      idx = (idx + 1) % posts.length;
      renderTicker();
    }, 4000);
  }

  /* =========================================================
     App Detail Page + Download Progress Modal
     ========================================================= */
  function initDetailPage() {
    const params = getParams();
    const slug = params.get("slug");
    const detailContainer = document.getElementById("detailContainer");
    const postNav = document.getElementById("postNav");

    let index = posts.findIndex(function (p) {
      return p.slug === slug;
    });
    if (index === -1) index = 0;

    const post = posts[index];
    if (!post || !detailContainer) return;

    document.title = post.title + " — " + config.siteName;

    const particlesHtml = (post.particles || ["🔥", "💰", "💎", "⭐"])
      .map(function (em) {
        return '<span class="b9-particle">' + em + "</span>";
      })
      .join("");

    const featuresHtml = (post.features || [])
      .map(function (f) {
        return "<div>" + escapeHtml(f) + "</div>";
      })
      .join("");

    const checksHtml = (post.checks || [])
      .map(function (c) {
        return "<div>" + escapeHtml(c) + "</div>";
      })
      .join("");

    detailContainer.innerHTML =
      '<nav id="breadcrumb" aria-label="Breadcrumb">' +
        '<a href="index.html">Home</a>' +
        '<i class="fa fa-chevron-right" aria-hidden="true"></i>' +
        '<a href="index.html?label=' + encodeURIComponent(post.category) + '">' + escapeHtml(post.category) + "</a>" +
        '<i class="fa fa-chevron-right" aria-hidden="true"></i>' +
        "<span>" + escapeHtml(post.title) + "</span>" +
      "</nav>" +
      '<h1 class="post-title">' + escapeHtml(post.title) + "</h1>" +
      '<div class="post-body">' +
        '<div class="b9-wrap">' +
          '<div class="b9-app-box">' +
            '<div class="b9-particles">' + particlesHtml + "</div>" +
            '<div class="b9-icon-wrap">' +
              '<img class="b9-icon" src="' + escapeHtml(post.image) + '" alt="' + escapeHtml(post.shortTitle) + '" />' +
            "</div>" +
            '<div class="b9-title">' + escapeHtml(post.shortTitle) + "</div>" +
            '<div class="b9-subtitle">' + escapeHtml(post.subtitle) + "</div>" +
            '<div class="b9-app-info">' +
              '<div class="b9-info-card"><span class="b9-info-label">Build</span><span class="b9-info-val">' + escapeHtml(post.build) + "</span></div>" +
              '<div class="b9-info-card"><span class="b9-info-label">Support</span><span class="b9-info-val">' + escapeHtml(post.support) + "</span></div>" +
              '<div class="b9-info-card"><span class="b9-info-label">Status</span><span class="b9-info-val">' + escapeHtml(post.status) + "</span></div>" +
            "</div>" +
            '<div class="b9-live-counter">⚾ ' + escapeHtml(post.downloadsToday) + " Players Downloaded Today</div>" +
            '<div class="b9-btn-group">' +
              '<button type="button" class="b9-btn b9-btn-android" data-platform="Android">' +
                '<span>' + post.emoji + "</span> Download For Android" +
              "</button>" +
              '<button type="button" class="b9-btn b9-btn-ios" data-platform="iPhone">' +
                "<span>🍎</span> Download For iPhone" +
              "</button>" +
            "</div>" +
            '<div class="b9-features">' + featuresHtml + "</div>" +
            '<div class="b9-checks">' + checksHtml + "</div>" +
          "</div>" +
        "</div>" +
      "</div>";

    // Render Older / Newer links
    if (postNav) {
      const olderPost = posts[index + 1] || null;
      const newerPost = posts[index - 1] || null;
      let navHtml = '<li class="post-prev">';
      if (olderPost) {
        navHtml +=
          '<span><i class="fa fa-angle-left"></i> OLDER</span>' +
          '<a href="app.html?slug=' + encodeURIComponent(olderPost.slug) + '">' + escapeHtml(olderPost.title) + "</a>";
      }
      navHtml += '</li><li class="post-next">';
      if (newerPost) {
        navHtml +=
          '<span>NEWER <i class="fa fa-angle-right"></i></span>' +
          '<a href="app.html?slug=' + encodeURIComponent(newerPost.slug) + '">' + escapeHtml(newerPost.title) + "</a>";
      }
      navHtml += "</li>";
      postNav.innerHTML = navHtml;
    }

    // Bind Download Modal
    const popup = document.getElementById("b9DownloadPopup");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const modalAppIcon = document.getElementById("modalAppIcon");
    const modalAppTitle = document.getElementById("modalAppTitle");
    const modalHeaderSub = document.getElementById("modalHeaderSub");
    const modalRing = document.getElementById("modalRing");
    const modalPercent = document.getElementById("modalPercent");
    const modalStatusTitle = document.getElementById("modalStatusTitle");
    const modalStatusSub = document.getElementById("modalStatusSub");
    const modalProgressFill = document.getElementById("modalProgressFill");
    const finalBtn = document.getElementById("b9FinalDownloadBtn");

    let progressTimer = null;

    function closeModal() {
      if (progressTimer) {
        clearInterval(progressTimer);
        progressTimer = null;
      }
      if (popup) popup.classList.remove("open");
    }

    function openDownloadModal(platform) {
      if (!popup) return;
      closeModal();

      modalAppIcon.src = post.image;
      modalAppIcon.alt = post.shortTitle;
      modalAppTitle.textContent = post.shortTitle;
      modalHeaderSub.textContent = "Preparing secure " + platform + " download...";
      modalPercent.textContent = "0%";
      modalRing.style.background = "conic-gradient(#ff3434 0deg, #ffd6d6 0deg)";
      modalProgressFill.style.width = "0%";
      modalStatusTitle.textContent = "Connecting to Server...";
      modalStatusSub.textContent = "Please wait while we prepare the latest guide";
      finalBtn.classList.remove("visible");
      finalBtn.textContent = post.emoji + " Verify & Continue";
      finalBtn.href = config.downloadRedirectUrl;

      popup.classList.add("open");

      let pct = 0;
      progressTimer = setInterval(function () {
        pct += Math.floor(Math.random() * 6) + 3;
        if (pct >= 100) pct = 100;

        const deg = Math.round((pct / 100) * 360);
        modalPercent.textContent = pct + "%";
        modalRing.style.background =
          "conic-gradient(#ff3434 0deg " + deg + "deg, #ffd6d6 " + deg + "deg 360deg)";
        modalProgressFill.style.width = pct + "%";

        if (pct < 35) {
          modalStatusTitle.textContent = "Connecting to Server...";
        } else if (pct < 70) {
          modalStatusTitle.textContent = "Verifying " + platform + " Package...";
        } else if (pct < 100) {
          modalStatusTitle.textContent = "Ready To Continue!";
        } else {
          modalStatusTitle.textContent = "Ready To Continue!";
          modalStatusSub.textContent = "Your " + platform + " download package is ready";
          finalBtn.classList.add("visible");
          clearInterval(progressTimer);
          progressTimer = null;
          finalBtn.onclick = function (e) {
            e.preventDefault();
            closeModal();
            if (typeof window.openContentLocker === "function") {
              window.openContentLocker(post.title, platform);
            }
          };
        }
      }, 95);
    }

    detailContainer.querySelectorAll(".b9-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        openDownloadModal(btn.getAttribute("data-platform") || "Android");
      });
    });

    if (closeModalBtn) {
      closeModalBtn.addEventListener("click", closeModal);
    }

    if (popup) {
      popup.addEventListener("click", function (e) {
        if (e.target === popup) closeModal();
      });
    }
  }

  /* =========================================================
     Bootstrap
     ========================================================= */
  const pageType = document.body.getAttribute("data-page");
  if (pageType === "detail") {
    initDetailPage();
  } else {
    initHomePage();
  }
})();
