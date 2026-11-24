/**
 * ApkCrunch.co Content Locker Engine
 * User ID: 831501
 * Public Key: 8902c82579eec05db438
 * Offers Key: 4a1d7b7a9f26dbe08fc3a0b059296411
 */
(function (window, document) {
  'use strict';

  var LOCKER_CONFIG = {
    userId: "831501",
    apiKeyPublic: "8902c82579eec05db438",
    apiKeyOffers: "4a1d7b7a9f26dbe08fc3a0b059296411",
    feedUrl: "https://dtvpp42hfuyb2.cloudfront.net/public/offers/feed.php?user_id=831501&api_key=4a1d7b7a9f26dbe08fc3a0b059296411&s1=&s2=",
    fallbackJsonUrl: "js/offers.json",
    apkDownloadUrl: "downloads/app.apk"
  };

  var cachedOffers = null;
  var isOfferClicked = false;
  var currentAppName = "ApkCrunch MOD Package";
  var currentPlatform = "Android";

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function fetchOffers(callback) {
    if (cachedOffers && cachedOffers.length > 0) {
      if (callback) callback(cachedOffers);
      return;
    }

    var xhr = new XMLHttpRequest();
    xhr.open("GET", LOCKER_CONFIG.feedUrl, true);
    xhr.timeout = 5000;
    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          var data = JSON.parse(xhr.responseText);
          if (Array.isArray(data) && data.length > 0) {
            cachedOffers = data;
            if (callback) callback(cachedOffers);
            return;
          }
        } catch (e) {}
      }
      fetchFallback(callback);
    };
    xhr.onerror = function () { fetchFallback(callback); };
    xhr.ontimeout = function () { fetchFallback(callback); };
    try {
      xhr.send();
    } catch (e) {
      fetchFallback(callback);
    }
  }

  function fetchFallback(callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", LOCKER_CONFIG.fallbackJsonUrl, true);
    xhr.timeout = 4000;
    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          var data = JSON.parse(xhr.responseText);
          if (Array.isArray(data) && data.length > 0) {
            cachedOffers = data;
            if (callback) callback(cachedOffers);
            return;
          }
        } catch (e) {}
      }
      // Minimal safe fallback
      cachedOffers = [
        {
          id: "f0J6oYMrKhRm5E3",
          name: "Ball Catcher",
          anchor: "Catch soccer balls to get special bonuses!",
          conversion: "Complete the free survey",
          network_icon: "https://cdn.affise.com/affise-media-service-prod/offers/959/33079/3019980592.200x200.jpeg",
          url: "https://oak.hoprly.com/a?p=o0J7NAb5C87OEGJ&o=f0J6oYMrKhRm5E3&s7=null&s8=null&s9=e1a94f417040"
        },
        {
          id: "f0J6oYX3QDUNnDi",
          name: "ClickBox - Earn Bonus",
          anchor: "Tap to claim your reward!",
          conversion: "Complete the survey",
          network_icon: "https://cdn.affise.com/affise-media-service-prod/offers/959/28565/1457439075.200x200.png",
          url: "https://oak.hoprly.com/a?p=o0J7NAb5C87OEGJ&o=f0J6oYX3QDUNnDi&s7=null&s8=null&s9=e1a94f417040"
        }
      ];
      if (callback) callback(cachedOffers);
    };
    xhr.onerror = function () {
      if (callback) callback([]);
    };
    try {
      xhr.send();
    } catch (e) {
      if (callback) callback([]);
    }
  }

  function buildModalHtml(appName, platform) {
    return [
      '<div id="apkcrunchLockerModal" class="apkcrunch-locker-backdrop" role="dialog" aria-modal="true">',
      '  <div class="apkcrunch-locker-card">',
      '    <div class="apkcrunch-locker-header">',
      '      <button type="button" class="apkcrunch-locker-close" id="apkcrunchLockerClose" aria-label="Close">&times;</button>',
      '      <div class="apkcrunch-locker-badge"><i class="fa fa-shield"></i> Verification Required</div>',
      '      <h3 class="apkcrunch-locker-title" id="apkcrunchLockerTitle">Unlock ' + escapeHtml(appName) + '</h3>',
      '      <p class="apkcrunch-locker-subtitle">Complete 1 quick sponsor offer below to verify your device and instantly release your package.</p>',
      '    </div>',
      '    <div class="apkcrunch-locker-body">',
      '      <div class="apkcrunch-locker-status-bar">',
      '        <span>Status: <b id="apkcrunchLockerStatus">Pending Offer</b></span>',
      '        <span>Platform: <b>' + escapeHtml(platform) + '</b></span>',
      '      </div>',
      '      <div id="apkcrunchOffersContainer">',
      '        <div class="apkcrunch-loading">',
      '          <div class="apkcrunch-spinner"></div>',
      '          <p>Loading verified offers for your region...</p>',
      '        </div>',
      '      </div>',
      '    </div>',
      '    <div class="apkcrunch-locker-footer">',
      '      <button type="button" id="apkcrunchCheckBtn" class="apkcrunch-check-btn">',
      '        <i class="fa fa-download"></i> Download Verified APK',
      '      </button>',
      '      <p class="apkcrunch-footer-note">Free & 100% Virus Free • Verified by Google Play Protect & SafeScan</p>',
      '    </div>',
      '  </div>',
      '</div>'
    ].join('\n');
  }

  function renderOffersList(offers) {
    var container = document.getElementById("apkcrunchOffersContainer");
    if (!container) return;

    if (!offers || offers.length === 0) {
      container.innerHTML = '<div class="apkcrunch-loading"><p>No offers available. Click the button below to download directly.</p></div>';
      return;
    }

    var html = '<div class="apkcrunch-offers-list">';
    for (var i = 0; i < offers.length; i++) {
      var item = offers[i];
      var icon = item.network_icon || 'img/logo.png';
      var name = item.name || 'Verified Sponsor Offer';
      var desc = item.conversion || item.anchor || 'Complete quick task to unlock';
      var url = item.url || '#';
      var imp = item.impression_url || '';

      html += '<a href="' + escapeHtml(url) + '" target="_blank" rel="noopener noreferrer" class="apkcrunch-offer-item" data-imp="' + escapeHtml(imp) + '">';
      html += '  <img src="' + escapeHtml(icon) + '" alt="' + escapeHtml(name) + '" class="apkcrunch-offer-icon" onerror="this.src=\'img/logo.png\'">';
      html += '  <div class="apkcrunch-offer-info">';
      html += '    <h4 class="apkcrunch-offer-name">' + escapeHtml(name) + '</h4>';
      html += '    <p class="apkcrunch-offer-desc">' + escapeHtml(desc) + '</p>';
      html += '  </div>';
      html += '  <span class="apkcrunch-offer-btn"><i class="fa fa-unlock-alt"></i> Free</span>';
      html += '</a>';
    }
    html += '</div>';

    container.innerHTML = html;

    // Attach click events & fire impressions
    var items = container.querySelectorAll(".apkcrunch-offer-item");
    items.forEach(function (el) {
      el.addEventListener("click", function () {
        isOfferClicked = true;
        var impUrl = el.getAttribute("data-imp");
        if (impUrl) {
          var img = new Image();
          img.src = impUrl;
        }

        var statusEl = document.getElementById("apkcrunchLockerStatus");
        if (statusEl) {
          statusEl.innerHTML = '<span style="color:#16a34a;">Verifying...</span>';
        }

        var checkBtn = document.getElementById("apkcrunchCheckBtn");
        if (checkBtn) {
          checkBtn.classList.add("unlocked");
          checkBtn.innerHTML = '<i class="fa fa-check-circle"></i> Verification Complete — Click to Download APK';
        }
      });
    });
  }

  window.openContentLocker = function (appName, platform) {
    currentAppName = appName || "ApkCrunch Package";
    currentPlatform = platform || "Android";

    var modal = document.getElementById("apkcrunchLockerModal");
    if (!modal) {
      var div = document.createElement("div");
      div.innerHTML = buildModalHtml(currentAppName, currentPlatform);
      document.body.appendChild(div.firstElementChild);
      modal = document.getElementById("apkcrunchLockerModal");

      var closeBtn = document.getElementById("apkcrunchLockerClose");
      if (closeBtn) {
        closeBtn.addEventListener("click", window.closeContentLocker);
      }

      var checkBtn = document.getElementById("apkcrunchCheckBtn");
      if (checkBtn) {
        checkBtn.addEventListener("click", function () {
          if (!isOfferClicked) {
            alert("Please complete at least 1 free offer above to unlock your package!");
            return;
          }
          // Deliver APK download
          var a = document.createElement("a");
          a.href = LOCKER_CONFIG.apkDownloadUrl;
          a.download = (currentAppName.replace(/[^a-zA-Z0-9_-]/g, "_") || "apkcrunch") + ".apk";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        });
      }
    } else {
      var titleEl = document.getElementById("apkcrunchLockerTitle");
      if (titleEl) titleEl.textContent = 'Unlock ' + currentAppName;
      modal.style.display = "flex";
    }

    document.body.style.overflow = "hidden";
    fetchOffers(function (offers) {
      renderOffersList(offers);
    });
  };

  window.closeContentLocker = function () {
    var modal = document.getElementById("apkcrunchLockerModal");
    if (modal) {
      modal.style.display = "none";
      document.body.style.overflow = "";
    }
  };

  // Pre-load offers in background
  fetchOffers();

})(window, document);
