#!/usr/bin/env python3
"""Generate bilingual tune pages, indexes, sitemap.xml, and robots.txt.

Uses only the Python standard library. Run from any working directory:
    python3 scripts/generate_pages.py
"""

from __future__ import annotations

import html
import json
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path
from string import Template
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://kimuhixy.com/jazz-ireal"
OG_IMAGE = f"{BASE_URL}/icons/icon-512.png"
MAX_RELATED = 6
RESERVED_SLUGS = {"index"}


def js_const(source: str, name: str) -> str:
    match = re.search(rf'{name}\s*=\s*"([^"]*)"', source)
    if match is None:
        raise ValueError(f"js から {name} を読み取れません")
    return match.group(1)


def js_table(source: str, name: str) -> dict[str, str]:
    block = re.search(rf"{name}\s*=\s*\{{(.*?)\n\}};", source, re.S)
    if block is None:
        raise ValueError(f"js から {name} を読み取れません")
    return dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', block.group(1)))


def load_affiliate() -> tuple[str, dict[str, str], dict[str, str]]:
    """アソシエイトタグ・ASIN表・検索語表を js/ 側から読む。

    表を Python 側にも書き写すと、片方だけ更新されて静的ページとアプリで
    リンク先がずれる。js/affiliate.js と js/config.js を唯一の情報源にする。
    """
    config = (ROOT / "js/config.js").read_text(encoding="utf-8")
    affiliate = (ROOT / "js/affiliate.js").read_text(encoding="utf-8")
    return js_const(config, "AMAZON_ASSOCIATE_TAG"), js_table(affiliate, "BOOK_ASINS"), js_table(affiliate, "BOOK_SEARCH_QUERIES")


CONFIG_JS = (ROOT / "js/config.js").read_text(encoding="utf-8")
ASSOCIATE_TAG, BOOK_ASINS, BOOK_SEARCH_QUERIES = load_affiliate()
ADSENSE_CLIENT_ID = js_const(CONFIG_JS, "ADSENSE_CLIENT_ID")
KOFI_USERNAME = js_const(CONFIG_JS, "KOFI_USERNAME")
ADSENSE_INARTICLE_SLOT = js_const(CONFIG_JS, "ADSENSE_INARTICLE_SLOT")
ANALYTICS_TOKEN = js_const(CONFIG_JS, "ANALYTICS_TOKEN")


def amazon_link(book_key: str) -> str | None:
    if not ASSOCIATE_TAG:
        return None
    asin = BOOK_ASINS.get(book_key)
    if asin:
        return f"https://www.amazon.co.jp/dp/{quote(asin)}?tag={quote(ASSOCIATE_TAG)}"
    query = BOOK_SEARCH_QUERIES.get(book_key)
    if not query:
        return None
    return f"https://www.amazon.co.jp/s?k={quote(query)}&tag={quote(ASSOCIATE_TAG)}"


def ad_unit_markup() -> str:
    """楽譜セクション直後の記事内広告。スロット未設定なら自動広告のみに任せる。"""
    if not ADSENSE_INARTICLE_SLOT or not ADSENSE_CLIENT_ID:
        return ""
    return (
        '<ins class="adsbygoogle inarticle-ad" style="display:block; text-align:center"'
        ' data-ad-layout="in-article" data-ad-format="fluid"'
        f' data-ad-client="{esc(ADSENSE_CLIENT_ID)}" data-ad-slot="{esc(ADSENSE_INARTICLE_SLOT)}"></ins>'
        '<script>if(location.hostname==="kimuhixy.com"){(adsbygoogle=window.adsbygoogle||[]).push({})}</script>'
    )


def kofi_markup(english: bool) -> str:
    """静的ページのフッターにもKo-fiリンクを出す。

    アプリ本体は donate.js が動的に差し込むが、検索流入が着地するのは静的ページ側。
    文言は js/strings.js の kofiSupport と揃えている。
    """
    if not KOFI_USERNAME:
        return ""
    label = "☕ Support on Ko-fi" if english else "☕ Ko-fiで応援する"
    return (
        f'<p class="footer-donate"><a href="https://ko-fi.com/{quote(KOFI_USERNAME)}"'
        f' target="_blank" rel="noopener">{label}</a></p>'
    )


def analytics_markup() -> str:
    """Cloudflare Web Analyticsのビーコン。Cookieを使わないので同意管理の対象外。"""
    if not ANALYTICS_TOKEN:
        return ""
    token = json.dumps({"token": ANALYTICS_TOKEN}, separators=(",", ":"))
    return (
        '<script defer src="https://static.cloudflareinsights.com/beacon.min.js"'
        f" data-cf-beacon='{token}'></script>"
    )


def load_songs() -> list[dict]:
    source = (ROOT / "data.js").read_text(encoding="utf-8")
    match = re.search(r"window\.SONGS\s*=\s*(\[.*\]);\s*$", source, re.S)
    if not match:
        raise ValueError("data.js から window.SONGS を読み取れません")
    songs = json.loads(match.group(1))
    required = {
        "title", "form", "formEn", "style", "styleEn", "harm", "harmEn",
        "note", "noteEn", "ver", "orig", "books", "omnibooks", "realbooks",
    }
    for number, song in enumerate(songs, 1):
        missing = required - song.keys()
        if missing:
            raise ValueError(f"レコード {number} に必須項目がありません: {sorted(missing)}")
    return songs


def slug_base(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")
    return slug or "tune"


def assign_slugs(songs: list[dict]) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    used: set[str] = set()
    slugs = []
    for index, song in enumerate(songs, 1):
        base = slug_base(song["title"])
        if base == "tune":
            base = f"tune-{index}"
        if base in RESERVED_SLUGS:
            base = f"tune-{base}"
        counts[base] += 1
        candidate = base if counts[base] == 1 else f"{base}-{counts[base]}"
        while candidate in used:
            counts[base] += 1
            candidate = f"{base}-{counts[base]}"
        used.add(candidate)
        slugs.append(candidate)
    return slugs


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def pill(label: str, value: object) -> str:
    return f'<span class="pill"><span class="k">{esc(label)}</span>{esc(value)}</span>'


def section(heading: str, body: str) -> str:
    return f'<section class="item-section"><h2>{esc(heading)}</h2>{body}</section>'


def list_markup(values: list[str], class_name: str = "detail-list") -> str:
    return f'<ul class="{class_name}">' + "".join(f"<li>{esc(v)}</li>" for v in values) + "</ul>"


def reference_markup(entries: list[tuple[str, str]], english: bool) -> str:
    """掲載位置の各行に、書名が対照表にあれば Amazon 検索リンク(PR表記付き)を添える。"""
    items = []
    for label, book_key in entries:
        href = amazon_link(book_key)
        if href:
            aria = f"Search for {book_key} on Amazon" if english else f"{book_key}をAmazonで探す"
            items.append(
                f"<li>{esc(label)}"
                f'<a class="buy-link" href="{esc(href)}" target="_blank" rel="sponsored noopener"'
                f' aria-label="{esc(aria)}">{"Buy on Amazon" if english else "Amazonで探す"}'
                f'<span class="pr-badge">PR</span></a></li>'
            )
        else:
            items.append(f"<li>{esc(label)}</li>")
    return '<ul class="reference-list">' + "".join(items) + "</ul>"


def books_markup(song: dict, english: bool) -> str:
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    if song["books"]:
        groups.append((
            "Jazz Standard Bible (Kuro-bon)" if english else "黒本（ジャズ・スタンダード・バイブル）",
            [(f'{b.get("volEn", b["vol"]) if english else b["vol"]} — p.{b["page"]}', b["vol"]) for b in song["books"]],
        ))
    if song["omnibooks"]:
        groups.append((
            "Omnibook",
            [(f'{b["book"]} — {b["key"]}, p.{b["page"]}', b["book"]) for b in song["omnibooks"]],
        ))
    if song["realbooks"]:
        groups.append((
            "Real Book",
            [(f'{b["vol"]} — p.{b["page"]}', b["vol"]) for b in song["realbooks"]],
        ))
    if not groups:
        message = "No page reference recorded." if english else "ページ参照の登録はありません。"
        return section("Sheet Music References" if english else "楽譜掲載位置", f"<p>{message}</p>")
    content = "".join(
        f'<div class="reference-group"><h3>{esc(name)}</h3>{reference_markup(entries, english)}</div>'
        for name, entries in groups
    )
    return section("Sheet Music References" if english else "楽譜掲載位置", content)


def has_references(song: dict) -> bool:
    return bool(song["books"] or song["omnibooks"] or song["realbooks"])


def robots_markup(song: dict) -> str:
    """楽譜掲載位置が無い曲は noindex にする。

    本文が定型文だけの薄いページが大量にあるとサイト全体の評価を下げるため、
    掲載位置を持つ曲にクロールを集中させる。follow は残すので、これらのページ経由で
    関連曲へのリンクはたどられる。掲載位置を追加すれば自動的にindex対象へ戻る。
    """
    if has_references(song):
        return ""
    return '<meta name="robots" content="noindex,follow">'


def relation_keys(song: dict) -> set[str]:
    return {f'form:{song["form"]}', f'style:{song["style"]}'} | {f"harm:{v}" for v in song["harm"]}


def related_indices(songs: list[dict]) -> list[list[int]]:
    buckets: dict[str, list[int]] = defaultdict(list)
    keys = [relation_keys(song) for song in songs]
    for index, song_keys in enumerate(keys):
        for key in song_keys:
            buckets[key].append(index)
    result: list[list[int]] = []
    for index, song_keys in enumerate(keys):
        candidates = set()
        for key in song_keys:
            candidates.update(buckets[key])
        candidates.discard(index)
        ranked = sorted(
            candidates,
            key=lambda other: (-len(song_keys & keys[other]), songs[other]["title"].casefold(), other),
        )
        result.append(ranked[:MAX_RELATED])
    return result


def description(song: dict, english: bool) -> str:
    form = song["formEn"] if english else song["form"]
    style = song["styleEn"] if english else song["style"]
    refs = len(song["books"]) + len(song["omnibooks"]) + len(song["realbooks"])
    if english:
        text = f'{song["title"]}: {form}; {style}. Jazz tune analysis'
        text += f" with {refs} sheet music page reference{'s' if refs != 1 else ''}." if refs else "."
    else:
        text = f'{song["title"]}の形式は{form}、スタイルは{style}。ジャズ楽曲の解説'
        text += f"と楽譜掲載位置{refs}件。" if refs else "。"
    return text[:155]


def json_ld(song: dict, slug: str, english: bool) -> str:
    canonical = f'{BASE_URL}/{"en/" if english else ""}items/{slug}/'
    home = f'{BASE_URL}/{"en/" if english else ""}'
    index_url = f'{BASE_URL}/{"en/" if english else ""}items/'
    form = song["formEn"] if english else song["form"]
    style = song["styleEn"] if english else song["style"]
    harmonic = song["harmEn"] if english else song["harm"]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": f"{BASE_URL}/",
                "name": "Jazz Analysis × iReal Pro" if english else "Jazz アナライズ × iReal Pro",
                "inLanguage": ["ja", "en"],
            },
            {
                "@type": "MusicComposition",
                "@id": f"{canonical}#composition",
                "name": song["title"],
                "alternateName": song["orig"],
                "genre": style,
                "url": canonical,
                "inLanguage": "en" if english else "ja",
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "Form", "value": form},
                    {"@type": "PropertyValue", "name": "Harmonic features", "value": harmonic},
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home" if english else "トップ", "item": home},
                    {"@type": "ListItem", "position": 2, "name": "Tune index" if english else "曲目索引", "item": index_url},
                    {"@type": "ListItem", "position": 3, "name": song["title"], "item": canonical},
                ],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def detail_context(song: dict, slug: str, related: list[int], songs: list[dict], slugs: list[str], english: bool) -> dict[str, str]:
    lang_prefix = "en/" if english else ""
    canonical = f"{BASE_URL}/{lang_prefix}items/{slug}/"
    ja_url = f"{BASE_URL}/items/{slug}/"
    en_url = f"{BASE_URL}/en/items/{slug}/"
    form = song["formEn"] if english else song["form"]
    style = song["styleEn"] if english else song["style"]
    harmonic = song["harmEn"] if english else song["harm"]
    note = song["noteEn"] if english else song["note"]
    pills = pill("Form" if english else "形式", form) + pill("Style" if english else "スタイル", style)
    pills += pill("Listings" if english else "収録", song["ver"])
    harmonic_body = "".join(f'<span class="chord">{esc(value)}</span>' for value in harmonic)
    if not harmonic_body:
        harmonic_body = f'<span class="unknown">{"Not recorded" if english else "記載なし"}</span>'
    variants = song["orig"]
    variants_body = list_markup(variants) if variants else f'<p>{"None recorded." if english else "記載なし"}</p>'
    relative_prefix = ".."
    related_links = "".join(
        f'<li><a href="{relative_prefix}/{slugs[i]}/">{esc(songs[i]["title"])}</a>'
        f'<span>{esc(songs[i]["formEn"] if english else songs[i]["form"])}</span></li>'
        for i in related
    )
    related_body = f'<ul class="related-list">{related_links}</ul>' if related_links else f'<p>{"No related tunes found." if english else "関連曲はありません。"}</p>'
    return {
        "page_title": esc(f'{song["title"]} | Jazz Analysis' if english else f'{song["title"]} | Jazz アナライズ'),
        "meta_description": esc(description(song, english)),
        "canonical_url": canonical,
        "ja_url": ja_url,
        "en_url": en_url,
        "og_title": esc(song["title"]),
        "og_image": OG_IMAGE,
        "json_ld": json_ld(song, slug, english),
        "title": esc(song["title"]),
        "pills": pills,
        "harmonic_section": section("Harmonic Features" if english else "和声的特徴", f'<div class="chips">{harmonic_body}</div>'),
        "note_section": section("Analysis Notes" if english else "分類・分析メモ", f'<p class="note">{esc(note)}</p>'),
        "variants_section": section("Alternate Titles / Source Listings" if english else "元の表記・別表記", variants_body),
        "books_section": books_markup(song, english),
        "ad_unit": ad_unit_markup(),
        "analytics": analytics_markup(),
        "robots": robots_markup(song),
        "kofi": kofi_markup(english),
        "related_section": section("Related Tunes" if english else "関連曲", related_body),
        "app_url": ("../../../en/" if english else "../../") + "?q=" + quote(song["title"]),
        "ireal_url": "irealb://search?" + quote(re.sub(r"^the\s+", "", song["title"], flags=re.I)),
        "spotify_url": "https://open.spotify.com/search/" + quote(song["title"]),
        "en_relative": f"../../en/items/{slug}/",
        "ja_relative": f"../../../items/{slug}/",
    }


def index_groups(songs: list[dict], slugs: list[str]) -> str:
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for song, slug in zip(songs, slugs):
        first = song["title"].lstrip("('").upper()[:1]
        key = first if "A" <= first <= "Z" else "#"
        groups[key].append((song["title"], slug))
    nav = '<nav class="az-nav" aria-label="A–Z">' + "".join(f'<a href="#{key}">{key}</a>' for key in sorted(groups)) + "</nav>"
    sections = []
    for key in sorted(groups):
        links = "".join(f'<li><a href="{slug}/">{esc(title)}</a></li>' for title, slug in groups[key])
        sections.append(f'<section class="index-group"><h2 id="{key}">{key}</h2><ul>{links}</ul></section>')
    return nav + "".join(sections)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def generate() -> None:
    songs = load_songs()
    slugs = assign_slugs(songs)
    related = related_indices(songs)
    templates = {
        "ja": Template((ROOT / "templates/detail_ja.html").read_text(encoding="utf-8")),
        "en": Template((ROOT / "templates/detail_en.html").read_text(encoding="utf-8")),
        "index_ja": Template((ROOT / "templates/index_ja.html").read_text(encoding="utf-8")),
        "index_en": Template((ROOT / "templates/index_en.html").read_text(encoding="utf-8")),
    }
    for generated_dir in (ROOT / "items", ROOT / "en/items"):
        if generated_dir.exists():
            shutil.rmtree(generated_dir)
    for index, (song, slug) in enumerate(zip(songs, slugs)):
        write(ROOT / "items" / slug / "index.html", templates["ja"].substitute(detail_context(song, slug, related[index], songs, slugs, False)))
        write(ROOT / "en/items" / slug / "index.html", templates["en"].substitute(detail_context(song, slug, related[index], songs, slugs, True)))
    groups = index_groups(songs, slugs)
    shared = {
        "ja_url": f"{BASE_URL}/items/", "en_url": f"{BASE_URL}/en/items/", "og_image": OG_IMAGE, "groups": groups,
        "analytics": analytics_markup(),
    }
    write(ROOT / "items/index.html", templates["index_ja"].substitute(shared, canonical_url=shared["ja_url"], kofi=kofi_markup(False)))
    write(ROOT / "en/items/index.html", templates["index_en"].substitute(shared, canonical_url=shared["en_url"], kofi=kofi_markup(True)))

    urls = [
        f"{BASE_URL}/", f"{BASE_URL}/en/", f"{BASE_URL}/about.html", f"{BASE_URL}/en/about.html",
        f"{BASE_URL}/privacy.html", f"{BASE_URL}/en/privacy.html", f"{BASE_URL}/harmony-tree/",
        f"{BASE_URL}/items/", f"{BASE_URL}/en/items/",
    ]
    # noindex にしたページはサイトマップからも外す。両者が食い違うとSearch Consoleが
    # 「サイトマップに登録済みだが除外」の警告を大量に出す。
    indexable = [slug for song, slug in zip(songs, slugs) if has_references(song)]
    urls.extend(f"{BASE_URL}/items/{slug}/" for slug in indexable)
    urls.extend(f"{BASE_URL}/en/items/{slug}/" for slug in indexable)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{html.escape(url)}</loc></url>\n" for url in urls)
    sitemap += "</urlset>\n"
    write(ROOT / "sitemap.xml", sitemap)
    write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n")
    noindexed = len(songs) - len(indexable)
    print(
        f"Generated {len(songs) * 2:,} detail pages ({noindexed * 2:,} noindex), "
        f"2 indexes, and {len(urls):,} sitemap URLs."
    )


if __name__ == "__main__":
    generate()
