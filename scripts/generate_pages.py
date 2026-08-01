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


def js_string_set(source: str, name: str) -> set[str]:
    block = re.search(rf"{name}\s*=\s*new Set\(\[(.*?)\]\);", source, re.S)
    if block is None:
        raise ValueError(f"js から {name} を読み取れません")
    return set(re.findall(r'"([^"]+)"', block.group(1)))


def load_affiliate() -> tuple[dict[str, str], dict[str, str], set[str]]:
    """ASIN表・検索語表・国内限定書籍を js/ 側から読む。

    表を Python 側にも書き写すと、片方だけ更新されて静的ページとアプリで
    リンク先がずれる。js/affiliate.js と js/config.js を唯一の情報源にする。
    """
    affiliate = (ROOT / "js/affiliate.js").read_text(encoding="utf-8")
    return (
        js_table(affiliate, "BOOK_ASINS"),
        js_table(affiliate, "BOOK_SEARCH_QUERIES"),
        js_string_set(affiliate, "JP_ONLY_BOOKS"),
    )


CONFIG_JS = (ROOT / "js/config.js").read_text(encoding="utf-8")
BOOK_ASINS, BOOK_SEARCH_QUERIES, JP_ONLY_BOOKS = load_affiliate()
ASSOCIATE_TAG = js_const(CONFIG_JS, "AMAZON_ASSOCIATE_TAG")
US_ASSOCIATE_TAG = js_const(CONFIG_JS, "AMAZON_US_ASSOCIATE_TAG")
ADSENSE_CLIENT_ID = js_const(CONFIG_JS, "ADSENSE_CLIENT_ID")
KOFI_USERNAME = js_const(CONFIG_JS, "KOFI_USERNAME")
ADSENSE_INARTICLE_SLOT = js_const(CONFIG_JS, "ADSENSE_INARTICLE_SLOT")


# 書籍ハブページの定義。key は data.js 側の表記と厳密に一致させること。
# 英語名は "the real book volume 1" のような実際の検索語に寄せている。
BOOKS: list[dict[str, str]] = [
    {"key": "Real Book Vol.1", "slug": "real-book-volume-1",
     "en": "The Real Book Volume 1", "ja": "The Real Book Vol.1", "family": "Real Book"},
    {"key": "Real Book Vol.2", "slug": "real-book-volume-2",
     "en": "The Real Book Volume 2", "ja": "The Real Book Vol.2", "family": "Real Book"},
    {"key": "Real Book Vol.3", "slug": "real-book-volume-3",
     "en": "The Real Book Volume 3", "ja": "The Real Book Vol.3", "family": "Real Book"},
    {"key": "Charlie Parker Omnibook (E♭)", "slug": "charlie-parker-omnibook",
     "en": "Charlie Parker Omnibook", "ja": "Charlie Parker Omnibook", "family": "Omnibook"},
    {"key": "Charlie Parker Omnibook Vol.2 (E♭)", "slug": "charlie-parker-omnibook-volume-2",
     "en": "Charlie Parker Omnibook Volume 2", "ja": "Charlie Parker Omnibook Vol.2", "family": "Omnibook"},
    {"key": "Miles Davis Omnibook (E♭)", "slug": "miles-davis-omnibook",
     "en": "Miles Davis Omnibook", "ja": "Miles Davis Omnibook", "family": "Omnibook"},
    {"key": "John Coltrane Omnibook (B♭)", "slug": "john-coltrane-omnibook",
     "en": "John Coltrane Omnibook", "ja": "John Coltrane Omnibook", "family": "Omnibook"},
    {"key": "Cannonball Adderley Omnibook (E♭)", "slug": "cannonball-adderley-omnibook",
     "en": "Cannonball Adderley Omnibook", "ja": "Cannonball Adderley Omnibook", "family": "Omnibook"},
    {"key": "Stan Getz Omnibook (B♭)", "slug": "stan-getz-omnibook",
     "en": "Stan Getz Omnibook", "ja": "Stan Getz Omnibook", "family": "Omnibook"},
    {"key": "Wynton Marsalis Omnibook (B♭)", "slug": "wynton-marsalis-omnibook",
     "en": "Wynton Marsalis Omnibook", "ja": "Wynton Marsalis Omnibook", "family": "Omnibook"},
    {"key": "初版", "slug": "jazz-standard-bible",
     "en": "Jazz Standard Bible (Kuro-bon) 1st Edition", "ja": "黒本（ジャズ・スタンダード・バイブル）初版",
     "family": "Jazz Standard Bible"},
    {"key": "Vol.2", "slug": "jazz-standard-bible-2",
     "en": "Jazz Standard Bible (Kuro-bon) Volume 2", "ja": "黒本（ジャズ・スタンダード・バイブル）Vol.2",
     "family": "Jazz Standard Bible"},
]
BOOK_SLUGS = {book["key"]: book["slug"] for book in BOOKS}


def amazon_link(book_key: str, english: bool) -> str | None:
    """js/affiliate.js の buildBookLink と同じ規則でリンクを組み立てる。"""
    if english and book_key not in JP_ONLY_BOOKS:
        host, tag = "https://www.amazon.com", US_ASSOCIATE_TAG
    else:
        host, tag = "https://www.amazon.co.jp", ASSOCIATE_TAG
    asin = BOOK_ASINS.get(book_key)
    if asin:
        return f"{host}/dp/{quote(asin)}" + (f"?tag={quote(tag)}" if tag else "")
    query = BOOK_SEARCH_QUERIES.get(book_key)
    if not query:
        return None
    return f"{host}/s?k={quote(query)}" + (f"&tag={quote(tag)}" if tag else "")


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


def reference_markup(entries: list[tuple[str, str, str]], english: bool) -> str:
    """掲載位置の各行に、書籍ハブページへの内部リンクと Amazon リンク(PR表記付き)を添える。

    書名をハブページに繋ぐことで「この本には他に何が入っているか」へ回遊でき、
    曲ページ同士が孤立しなくなる。
    """
    items = []
    for display, suffix, book_key in entries:
        slug = BOOK_SLUGS.get(book_key)
        # 曲ページは /items/<slug>/ と /en/items/<slug>/ にあり、どちらからも同じ相対階層
        name = f'<a href="../../books/{slug}/">{esc(display)}</a>' if slug else esc(display)
        href = amazon_link(book_key, english)
        if href:
            aria = f"Buy {book_key} on Amazon" if english else f"{book_key}をAmazonで探す"
            buy = (
                f'<a class="buy-link" href="{esc(href)}" target="_blank" rel="sponsored noopener"'
                f' aria-label="{esc(aria)}">{"Buy on Amazon" if english else "Amazonで探す"}'
                f'<span class="pr-badge">PR</span></a>'
            )
        else:
            buy = ""
        items.append(f"<li>{name}{esc(suffix)}{buy}</li>")
    return '<ul class="reference-list">' + "".join(items) + "</ul>"


def books_markup(song: dict, english: bool) -> str:
    groups: list[tuple[str, list[tuple[str, str, str]]]] = []
    if song["books"]:
        groups.append((
            "Jazz Standard Bible (Kuro-bon)" if english else "黒本（ジャズ・スタンダード・バイブル）",
            [(b.get("volEn", b["vol"]) if english else b["vol"], f' — p.{b["page"]}', b["vol"]) for b in song["books"]],
        ))
    if song["omnibooks"]:
        groups.append((
            "Omnibook",
            [(b["book"], f' — {b["key"]}, p.{b["page"]}', b["book"]) for b in song["omnibooks"]],
        ))
    if song["realbooks"]:
        groups.append((
            "Real Book",
            [(b["vol"], f' — p.{b["page"]}', b["vol"]) for b in song["realbooks"]],
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


def primary_reference(song: dict) -> tuple[str, int] | None:
    """タイトルに出す代表的な掲載位置を1件選ぶ。

    英語圏の読者に通りが良い順(Real Book → Omnibook → 黒本)に見る。
    黒本は国内向けの本なので英語ページの見出しには使わない。
    """
    if song["realbooks"]:
        entry = song["realbooks"][0]
        return entry["vol"], entry["page"]
    if song["omnibooks"]:
        entry = song["omnibooks"][0]
        return entry["book"], entry["page"]
    return None


def english_title(song: dict) -> str:
    """「so what real book page」のような検索に当たるよう、書名とページを題名に入れる。"""
    reference = primary_reference(song)
    if not reference:
        return f'{song["title"]} | Jazz Analysis'
    book, page = reference
    return f'{song["title"]} — {book} p.{page} | Jazz Analysis'


def description(song: dict, english: bool) -> str:
    form = song["formEn"] if english else song["form"]
    style = song["styleEn"] if english else song["style"]
    refs = len(song["books"]) + len(song["omnibooks"]) + len(song["realbooks"])
    if english:
        # 冒頭に掲載位置を置く。検索結果で最初に読まれるのはここで、
        # このサイトの価値は解説そのものより「どの本の何ページか」にある。
        reference = primary_reference(song)
        lead = f'{song["title"]} is in {reference[0]} on p.{reference[1]}. ' if reference else ""
        text = f"{lead}Form: {form}; style: {style}"
        text += f"; {refs} sheet music page reference{'s' if refs != 1 else ''}." if refs else "."
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
        "page_title": esc(english_title(song) if english else f'{song["title"]} | Jazz アナライズ'),
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
        "robots": robots_markup(song),
        "kofi": kofi_markup(english),
        "related_section": section("Related Tunes" if english else "関連曲", related_body),
        "app_url": ("../../../en/" if english else "../../") + "?q=" + quote(song["title"]),
        "ireal_url": "irealb://search?" + quote(re.sub(r"^the\s+", "", song["title"], flags=re.I)),
        "spotify_url": "https://open.spotify.com/search/" + quote(song["title"]),
        "en_relative": f"../../en/items/{slug}/",
        "ja_relative": f"../../../items/{slug}/",
    }


def book_listings(songs: list[dict], slugs: list[str]) -> dict[str, list[tuple[str, str, int, str]]]:
    """書籍キーごとに (曲名, 曲slug, ページ番号, 調号) を集める。"""
    listings: dict[str, list[tuple[str, str, int, str]]] = defaultdict(list)
    for song, slug in zip(songs, slugs):
        for entry in song["books"]:
            listings[entry["vol"]].append((song["title"], slug, entry["page"], ""))
        for entry in song["omnibooks"]:
            listings[entry["book"]].append((song["title"], slug, entry["page"], entry["key"]))
        for entry in song["realbooks"]:
            listings[entry["vol"]].append((song["title"], slug, entry["page"], ""))
    for rows in listings.values():
        rows.sort(key=lambda row: (row[0].lstrip("('").upper(), row[2]))
    return listings


def book_listing_markup(rows: list[tuple[str, str, int, str]], english: bool) -> str:
    page_label = "p." if english else "p."
    items = "".join(
        f'<li><a href="../../items/{slug}/">{esc(title)}</a>'
        f'<span class="page-ref">{page_label}{page}</span></li>'
        for title, slug, page, _ in rows
    )
    return f'<ul class="book-listing">{items}</ul>'


def book_buy_markup(book: dict[str, str], english: bool) -> str:
    href = amazon_link(book["key"], english)
    if not href:
        return ""
    name = book["en"] if english else book["ja"]
    label = "Buy on Amazon" if english else "Amazonで探す"
    aria = f'Buy {name} on Amazon' if english else f"{name}をAmazonで探す"
    return (
        f'<p class="book-buy"><a class="buy-link" href="{esc(href)}" target="_blank"'
        f' rel="sponsored noopener" aria-label="{esc(aria)}">{label}'
        f'<span class="pr-badge">PR</span></a></p>'
    )


def book_json_ld(book: dict[str, str], rows: list, english: bool) -> str:
    canonical = f'{BASE_URL}/{"en/" if english else ""}books/{book["slug"]}/'
    home = f'{BASE_URL}/{"en/" if english else ""}'
    name = book["en"] if english else book["ja"]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "ItemList",
                "@id": f"{canonical}#tunes",
                "name": f"Tunes in {name}" if english else f"{name}の収録曲",
                "numberOfItems": len(rows),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": position,
                        "name": title,
                        "url": f'{BASE_URL}/{"en/" if english else ""}items/{slug}/',
                    }
                    for position, (title, slug, _, _) in enumerate(rows, 1)
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home" if english else "トップ", "item": home},
                    {"@type": "ListItem", "position": 2, "name": "Fake books" if english else "楽譜集",
                     "item": f'{BASE_URL}/{"en/" if english else ""}books/'},
                    {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
                ],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def book_context(book: dict[str, str], rows: list, english: bool) -> dict[str, str]:
    name = book["en"] if english else book["ja"]
    count = len(rows)
    if english:
        heading = f"{name} — Song List with Page Numbers"
        page_title = f"{name} — Song List &amp; Page Numbers | Jazz Analysis"
        lead = (
            f"All {count} tunes in {name}, in alphabetical order with the page each one starts on. "
            "Select a title for its form, style, and harmonic analysis."
        )
        meta = f"Complete song list for {name}: {count} tunes with page numbers, in alphabetical order."
    else:
        heading = f"{name} 収録曲一覧（ページ番号つき）"
        page_title = f"{name} 収録曲一覧・ページ番号 | Jazz アナライズ"
        lead = (
            f"{name}に収録されている{count}曲を五十音・アルファベット順に並べ、掲載ページを添えています。"
            "曲名を選ぶと形式・スタイル・和声的特徴が見られます。"
        )
        meta = f"{name}の収録曲{count}曲とページ番号の一覧。曲名から形式・スタイル・和声的特徴の解説へ。"
    return {
        "page_title": page_title,
        "meta_description": esc(meta[:155]),
        "canonical_url": f'{BASE_URL}/{"en/" if english else ""}books/{book["slug"]}/',
        "ja_url": f'{BASE_URL}/books/{book["slug"]}/',
        "en_url": f'{BASE_URL}/en/books/{book["slug"]}/',
        "og_title": esc(heading),
        "og_image": OG_IMAGE,
        "json_ld": book_json_ld(book, rows, english),
        "short_name": esc(name),
        "heading": esc(heading),
        "lead": esc(lead),
        "count": str(count),
        "buy": book_buy_markup(book, english),
        "ad_unit": ad_unit_markup(),
        "listing": book_listing_markup(rows, english),
        "kofi": kofi_markup(english),
        "ja_relative": f'../../../books/{book["slug"]}/',
        "en_relative": f'../../en/books/{book["slug"]}/',
    }


def books_index_markup(listings: dict, english: bool) -> str:
    families: dict[str, list[dict[str, str]]] = defaultdict(list)
    for book in BOOKS:
        families[book["family"]].append(book)
    sections = []
    for family, members in families.items():
        links = "".join(
            f'<li><a href="{book["slug"]}/">{esc(book["en"] if english else book["ja"])}</a>'
            f'<span class="page-ref">{len(listings[book["key"]])}'
            f'{" tunes" if english else "曲"}</span></li>'
            for book in members
        )
        sections.append(f'<section class="index-group"><h2>{esc(family)}</h2><ul class="book-listing">{links}</ul></section>')
    return "".join(sections)


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
        "book_ja": Template((ROOT / "templates/book_ja.html").read_text(encoding="utf-8")),
        "book_en": Template((ROOT / "templates/book_en.html").read_text(encoding="utf-8")),
        "books_ja": Template((ROOT / "templates/books_index_ja.html").read_text(encoding="utf-8")),
        "books_en": Template((ROOT / "templates/books_index_en.html").read_text(encoding="utf-8")),
    }
    for generated_dir in (ROOT / "items", ROOT / "en/items", ROOT / "books", ROOT / "en/books"):
        if generated_dir.exists():
            shutil.rmtree(generated_dir)
    for index, (song, slug) in enumerate(zip(songs, slugs)):
        write(ROOT / "items" / slug / "index.html", templates["ja"].substitute(detail_context(song, slug, related[index], songs, slugs, False)))
        write(ROOT / "en/items" / slug / "index.html", templates["en"].substitute(detail_context(song, slug, related[index], songs, slugs, True)))
    groups = index_groups(songs, slugs)
    shared = {
        "ja_url": f"{BASE_URL}/items/", "en_url": f"{BASE_URL}/en/items/", "og_image": OG_IMAGE, "groups": groups,
    }
    write(ROOT / "items/index.html", templates["index_ja"].substitute(shared, canonical_url=shared["ja_url"], kofi=kofi_markup(False)))
    write(ROOT / "en/items/index.html", templates["index_en"].substitute(shared, canonical_url=shared["en_url"], kofi=kofi_markup(True)))

    listings = book_listings(songs, slugs)
    missing = [book["key"] for book in BOOKS if not listings.get(book["key"])]
    if missing:
        raise ValueError(f"BOOKS の書名が data.js と一致しません: {missing}")
    for book in BOOKS:
        rows = listings[book["key"]]
        write(ROOT / "books" / book["slug"] / "index.html", templates["book_ja"].substitute(book_context(book, rows, False)))
        write(ROOT / "en/books" / book["slug"] / "index.html", templates["book_en"].substitute(book_context(book, rows, True)))
    books_shared = {
        "ja_url": f"{BASE_URL}/books/", "en_url": f"{BASE_URL}/en/books/", "og_image": OG_IMAGE,
        "total": f"{len(songs):,}",
        "json_ld": json.dumps({"@context": "https://schema.org", "@type": "CollectionPage",
                               "name": "Fake Book & Omnibook Contents", "url": f"{BASE_URL}/en/books/"},
                              ensure_ascii=False, separators=(",", ":")),
    }
    write(ROOT / "books/index.html", templates["books_ja"].substitute(
        books_shared, canonical_url=books_shared["ja_url"], kofi=kofi_markup(False),
        listing=books_index_markup(listings, False)))
    write(ROOT / "en/books/index.html", templates["books_en"].substitute(
        books_shared, canonical_url=books_shared["en_url"], kofi=kofi_markup(True),
        listing=books_index_markup(listings, True)))

    urls = [
        f"{BASE_URL}/", f"{BASE_URL}/en/", f"{BASE_URL}/about.html", f"{BASE_URL}/en/about.html",
        f"{BASE_URL}/privacy.html", f"{BASE_URL}/en/privacy.html", f"{BASE_URL}/harmony-tree/",
        f"{BASE_URL}/items/", f"{BASE_URL}/en/items/",
        f"{BASE_URL}/books/", f"{BASE_URL}/en/books/",
    ]
    for book in BOOKS:
        urls.append(f'{BASE_URL}/books/{book["slug"]}/')
        urls.append(f'{BASE_URL}/en/books/{book["slug"]}/')
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
        f"{len(BOOKS) * 2 + 2:,} book pages, 2 indexes, and {len(urls):,} sitemap URLs."
    )


if __name__ == "__main__":
    generate()
