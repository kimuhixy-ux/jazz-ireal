// app.js: 一覧・検索・絞り込み・詳細シートのロジック(旧index.html内スクリプトをESモジュール化)
import { LOCALE, ROOT } from "./i18n.js";
import { S } from "./strings.js";
import { buildBookSearchLink } from "./affiliate.js";
import { renderDonateLink } from "./donate.js";
import { initAds } from "./ads.js";

(function () {
  "use strict";
  var EN = LOCALE === "en";
  var SONGS = window.SONGS || [];
  var UNKNOWN = "不明";

  function pickForm(s) { return EN && s.formEn ? s.formEn : s.form; }
  function pickStyle(s) { return EN && s.styleEn ? s.styleEn : s.style; }
  function pickHarm(s) { return EN && s.harmEn ? s.harmEn : s.harm; }
  function pickNote(s) { return EN && s.noteEn ? s.noteEn : s.note; }
  function pickBookVol(b) { return EN && b.volEn ? b.volEn : b.vol; }

  // ---- フィルタ用の選択肢を抽出(値は常に原文の日本語、表示ラベルのみロケール対応) ----
  var formLabel = new Map(), styleLabel = new Map(), harmLabel = new Map();
  SONGS.forEach(function (s) {
    formLabel.set(s.form, pickForm(s));
    styleLabel.set(s.style, pickStyle(s));
    var harmEn = pickHarm(s);
    s.harm.forEach(function (t, i) { harmLabel.set(t, harmEn[i]); });
  });

  var compareLocale = EN ? "en" : "ja";
  function uniqSortedByLabel(values, labelMap) {
    return Array.from(new Set(values)).sort(function (a, b) {
      return labelMap.get(a).localeCompare(labelMap.get(b), compareLocale);
    });
  }
  var forms = uniqSortedByLabel(SONGS.map(function (s) { return s.form; }), formLabel);
  var styles = uniqSortedByLabel(SONGS.map(function (s) { return s.style; }), styleLabel);
  var harmTags = uniqSortedByLabel(
    SONGS.reduce(function (a, s) { return a.concat(s.harm); }, []),
    harmLabel
  );

  function fillSelect(el, label, opts, labelMap) {
    el.innerHTML = "";
    var o0 = document.createElement("option");
    o0.value = "";
    o0.textContent = label;
    el.appendChild(o0);
    opts.forEach(function (v) {
      var o = document.createElement("option");
      o.value = v;
      o.textContent = labelMap.get(v);
      el.appendChild(o);
    });
  }
  var elForm = document.getElementById("fForm"),
    elStyle = document.getElementById("fStyle"),
    elBook = document.getElementById("fBook");
  fillSelect(elForm, S.filterFormAllLabel, forms, formLabel);
  fillSelect(elStyle, S.filterStyleAllLabel, styles, styleLabel);

  elBook.innerHTML = "";
  var oBookAll = document.createElement("option");
  oBookAll.value = "";
  oBookAll.textContent = S.filterBookAllLabel;
  elBook.appendChild(oBookAll);
  S.bookFilterOptions.forEach(function (opt) {
    var o = document.createElement("option");
    o.value = opt.value;
    o.textContent = opt.label;
    elBook.appendChild(o);
  });

  var tagrow = document.getElementById("tagrow");
  var activeTags = new Set();
  harmTags.forEach(function (t) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "tag";
    b.textContent = harmLabel.get(t);
    b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", function () {
      if (activeTags.has(t)) {
        activeTags.delete(t);
        b.setAttribute("aria-pressed", "false");
      } else {
        activeTags.add(t);
        b.setAttribute("aria-pressed", "true");
      }
      render();
    });
    tagrow.appendChild(b);
  });

  // ---- フィルタリング ----
  var elQ = document.getElementById("q");
  function norm(s) { return (s || "").toLowerCase(); }
  function matches(s) {
    var q = norm(elQ.value.trim());
    if (q) {
      var hay = norm(s.title) + " " + norm(s.orig.join(" "));
      if (hay.indexOf(q) === -1) return false;
    }
    if (elForm.value && s.form !== elForm.value) return false;
    if (elStyle.value && s.style !== elStyle.value) return false;
    if (elBook.value) {
      var bk = s.books && s.books.length,
        om = s.omnibooks && s.omnibooks.length,
        rb = s.realbooks && s.realbooks.length;
      if (elBook.value === "kurobon" && !bk) return false;
      if (elBook.value === "omnibook" && !om) return false;
      if (elBook.value === "realbook" && !rb) return false;
      if (elBook.value === "any" && !bk && !om && !rb) return false;
      if (elBook.value === "all" && (!bk || !om || !rb)) return false;
    }
    if (activeTags.size) {
      for (var t of activeTags) {
        if (s.harm.indexOf(t) === -1) return false;
      }
    }
    return true;
  }

  // ---- 一覧描画 ----
  var listEl = document.getElementById("list"),
    countEl = document.getElementById("count"),
    emptyEl = document.getElementById("empty");
  var filtered = [];
  function render() {
    filtered = SONGS.filter(matches);
    countEl.textContent = filtered.length.toLocaleString(compareLocale);
    emptyEl.hidden = filtered.length !== 0;
    var html = "";
    for (var i = 0; i < filtered.length; i++) {
      var s = filtered[i];
      var formTxt = s.form === UNKNOWN ? '<span class="unknown">' + S.unknownFormRow + "</span>" : esc(pickForm(s));
      var styleTxt = s.style === UNKNOWN ? '<span class="unknown">' + S.unknownStyleRow + "</span>" : esc(pickStyle(s));
      html +=
        '<li class="row" data-i="' +
        i +
        '">' +
        '<div style="min-width:0;flex:1 1 auto">' +
        '<div class="name">' +
        esc(s.title) +
        "</div>" +
        '<div class="sub">' +
        formTxt +
        " ・ " +
        styleTxt +
        "</div>" +
        "</div>" +
        '<svg class="chev" width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
        "</li>";
    }
    listEl.innerHTML = html;
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  listEl.addEventListener("click", function (e) {
    var li = e.target.closest("li.row");
    if (!li) return;
    openSheet(filtered[+li.dataset.i]);
  });
  elQ.addEventListener("input", render);
  elForm.addEventListener("change", render);
  elStyle.addEventListener("change", render);
  elBook.addEventListener("change", render);

  // ---- iReal Pro 検索URL(先頭 The を外す) ----
  function irealURL(title) {
    var q = String(title).trim().replace(/^the\s+/i, "");
    return "irealb://search?" + encodeURIComponent(q);
  }

  function spotifyURL(title) {
    return "spotify:search:" + encodeURIComponent(String(title).trim());
  }

  // ---- 書籍チップ(該当すればAmazon検索リンク化) ----
  function bookChip(iconSvg, key, innerHtml, displayName) {
    var href = buildBookSearchLink(key);
    if (!href) {
      return '<span class="book">' + iconSvg + innerHtml + "</span>";
    }
    return (
      '<a class="book" href="' +
      href +
      '" target="_blank" rel="sponsored noopener" aria-label="' +
      esc(S.amazonSearchAriaLabel(displayName || key)) +
      '">' +
      iconSvg +
      innerHtml +
      ' <span class="pr-badge">PR</span></a>'
    );
  }

  // ---- 詳細シート ----
  var scrim = document.getElementById("scrim"),
    sheet = document.getElementById("sheet"),
    body = document.getElementById("sheetBody"),
    closeBtn = document.getElementById("close");
  var lastFocus = null;

  function openSheet(s) {
    var harmValues = pickHarm(s);
    var harmHtml = harmValues.length
      ? '<div class="chips">' + harmValues.map(function (t) { return '<span class="chord">' + esc(t) + "</span>"; }).join("") + "</div>"
      : '<span class="unknown">' + S.unknownShort + "</span>";
    var noteHtml = s.note ? "<p class=\"note\">" + esc(pickNote(s)) + "</p>" : '<span class="unknown">' + S.noteUnrecorded + "</span>";
    var origHtml =
      s.orig.length > 1
        ? '<div class="d-h">' + S.altTitlesHeading(s.orig.length) + '</div><ul class="orig">' + s.orig.map(function (o) { return "<li>" + esc(o) + "</li>"; }).join("") + "</ul>"
        : "";
    var bookIcon =
      '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M2 3.5C2 3 2.5 2.5 3.2 2.5H8v10H3.2C2.5 12.5 2 12 2 11.5v-8zM14 3.5C14 3 13.5 2.5 12.8 2.5H8v10h4.8c.7 0 1.2-.5 1.2-1v-8z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>';
    var omniIcon =
      '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 2h10v12H3z" stroke="currentColor" stroke-width="1.2"/><path d="M5.5 5h5M5.5 8h5M5.5 11h3" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>';
    var realIcon =
      '<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M2 2h12v12H2z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/><path d="M5 5h6M5 8h6M5 11h4" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>';
    var bookGroups = [];
    if (s.books && s.books.length) {
      bookGroups.push(
        '<div class="book-group"><span class="book-group-label">' +
          S.subKurobon +
          '</span><div class="chips">' +
          s.books.map(function (b) { return bookChip(bookIcon, b.vol, esc(pickBookVol(b)) + " <b>p." + b.page + "</b>", pickBookVol(b)); }).join("") +
          "</div></div>"
      );
    }
    if (s.omnibooks && s.omnibooks.length) {
      bookGroups.push(
        '<div class="book-group"><span class="book-group-label">' +
          S.subOmnibook +
          '</span><div class="chips">' +
          s.omnibooks
            .map(function (b) {
              var short = esc(b.book.replace(/ Omnibook.*$/, ""));
              return bookChip(omniIcon, b.book, short + ' <span class="key-tag">' + esc(b.key) + "</span> <b>p." + b.page + "</b>");
            })
            .join("") +
          "</div></div>"
      );
    }
    if (s.realbooks && s.realbooks.length) {
      bookGroups.push(
        '<div class="book-group"><span class="book-group-label">' +
          S.subRealBook +
          '</span><div class="chips">' +
          s.realbooks.map(function (b) { return bookChip(realIcon, b.vol, esc(b.vol) + " <b>p." + b.page + "</b>"); }).join("") +
          "</div></div>"
      );
    }
    var booksSectionHtml = bookGroups.length ? '<div class="d-h">' + S.headingSheetMusic + "</div>" + bookGroups.join("") : "";
    var formP = s.form === UNKNOWN ? '<span class="unknown">' + S.unknownShort + "</span>" : esc(pickForm(s));
    var styleP = s.style === UNKNOWN ? '<span class="unknown">' + S.unknownShort + "</span>" : esc(pickStyle(s));

    body.innerHTML =
      '<div class="d-eyebrow">Tune</div>' +
      '<h2 class="d-title">' +
      esc(s.title) +
      "</h2>" +
      '<div class="d-line">' +
      '<span class="pill"><span class="k">' +
      S.pillFormLabel +
      "</span>" +
      formP +
      "</span>" +
      '<span class="pill"><span class="k">' +
      S.pillStyleLabel +
      "</span>" +
      styleP +
      "</span>" +
      '<span class="pill"><span class="k">' +
      S.pillEditionLabel +
      "</span>" +
      S.editionValue(s.ver) +
      "</span>" +
      "</div>" +
      '<div class="d-h">' +
      S.headingHarmonic +
      "</div>" +
      harmHtml +
      '<div class="d-h">' +
      S.headingClassificationNote +
      "</div>" +
      noteHtml +
      origHtml +
      booksSectionHtml +
      '<div class="cta-wrap">' +
      '<a class="cta" href="' +
      irealURL(s.title) +
      '">' +
      '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M4 3l11 6-11 6V3z" fill="#1A1206"/></svg>' +
      S.ctaIreal +
      "</a>" +
      '<a class="cta-spotify" href="' +
      spotifyURL(s.title) +
      '">' +
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="#fff"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.6 0 12 0zm5.5 17.3c-.2.3-.6.4-.9.2-2.5-1.5-5.7-1.9-9.4-1-.4.1-.7-.1-.8-.5-.1-.4.1-.7.5-.8 4.1-.9 7.6-.5 10.4 1.2.3.2.4.6.2.9zm1.5-3.3c-.3.4-.8.5-1.2.3-2.9-1.8-7.2-2.3-10.6-1.3-.4.1-.9-.1-1-.5-.1-.4.1-.9.5-1 3.9-1.2 8.7-.6 12 1.4.4.2.5.7.3 1.1zm.1-3.4c-3.4-2-9.1-2.2-12.4-1.2-.5.2-1-.2-1.2-.7-.2-.5.2-1 .7-1.2 3.8-1.2 10-1 14 1.4.5.3.6.9.4 1.4-.3.4-.9.6-1.5.3z"/></svg>' +
      S.ctaSpotify +
      "</a>" +
      '<div class="cta-foot">' +
      S.ctaFootHtml +
      "</div>" +
      "</div>";
    body.scrollTop = 0;
    lastFocus = document.activeElement;
    scrim.classList.add("open");
    sheet.classList.add("open");
    sheet.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    closeBtn.focus();
  }
  function closeSheet() {
    scrim.classList.remove("open");
    sheet.classList.remove("open");
    sheet.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }
  closeBtn.addEventListener("click", closeSheet);
  scrim.addEventListener("click", closeSheet);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && sheet.classList.contains("open")) closeSheet();
  });

  var initialQuery = new URLSearchParams(location.search).get("q");
  if (initialQuery) elQ.value = initialQuery;
  render();
  renderDonateLink();
  initAds();

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register(ROOT + "sw.js").catch(function (err) {
        console.warn("Service Workerの登録に失敗しました:", err);
      });
    });
  }
})();
