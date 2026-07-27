#!/usr/bin/env python3
"""Validate generated PSEO outputs using only the Python standard library."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RECORDS = 2599


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    ja_pages = sorted((ROOT / "items").glob("*/index.html"))
    en_pages = sorted((ROOT / "en/items").glob("*/index.html"))
    if len(ja_pages) != EXPECTED_RECORDS or len(en_pages) != EXPECTED_RECORDS:
        fail(f"detail page count: ja={len(ja_pages)}, en={len(en_pages)}")
    if [p.parent.name for p in ja_pages] != [p.parent.name for p in en_pages]:
        fail("Japanese and English slug sets differ")

    required_ja = [
        'rel="canonical"', 'hreflang="ja"', 'hreflang="en"', 'hreflang="x-default"',
        '"@type":"MusicComposition"', '"@type":"BreadcrumbList"',
        "楽譜・コード進行・歌詞そのものは一切含みません",
        "データ提供元で参照された版に基づく",
        'name="twitter:card" content="summary_large_image"',
    ]
    required_en = [
        'rel="canonical"', 'hreflang="ja"', 'hreflang="en"', 'hreflang="x-default"',
        '"@type":"MusicComposition"', '"@type":"BreadcrumbList"',
        "It does not contain any sheet music, chord charts, or lyrics.",
        "may differ between editions",
        'name="twitter:card" content="summary_large_image"',
    ]
    banned = re.compile(r"\b(?:official|authorized|licensed)\b", re.I)
    for language, pages, required in (("ja", ja_pages, required_ja), ("en", en_pages, required_en)):
        for path in pages:
            text = path.read_text(encoding="utf-8")
            missing = [marker for marker in required if marker not in text]
            if missing:
                fail(f"{path.relative_to(ROOT)} missing {missing}")
            if banned.search(text):
                fail(f"{path.relative_to(ROOT)} contains a prohibited partnership term")
            if language == "en":
                related = re.search(r"<h2>Related Tunes</h2>(.*?)</section>", text, re.S)
                if related and 'href="../../../items/' in related.group(1):
                    fail(f"{path.relative_to(ROOT)} has a related-tune link to the wrong locale")
            match = re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
            if not match:
                fail(f"{path.relative_to(ROOT)} has no JSON-LD")
            try:
                json.loads(match.group(1))
            except json.JSONDecodeError as exc:
                fail(f"{path.relative_to(ROOT)} invalid JSON-LD: {exc}")
            for href in re.findall(r'href="([^"]+)"', text):
                parsed = urlsplit(html_unescape(href))
                if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
                    continue
                target = (path.parent / unquote(parsed.path)).resolve()
                if target.is_dir():
                    target = target / "index.html"
                if not target.exists():
                    fail(f"{path.relative_to(ROOT)} has broken link: {href}")

    for path in (ROOT / "items/index.html", ROOT / "en/items/index.html"):
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        if text.count('<li><a href="') != EXPECTED_RECORDS:
            fail(f"{path.relative_to(ROOT)} does not list all records")

    sitemap = ROOT / "sitemap.xml"
    root = ET.parse(sitemap).getroot()
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [node.text for node in root.findall("s:url/s:loc", namespace)]
    if len(urls) != EXPECTED_RECORDS * 2 + 9:
        fail(f"sitemap URL count is {len(urls)}")
    if len(urls) != len(set(urls)):
        fail("sitemap contains duplicate URLs")
    if "Sitemap: https://kimuhixy.com/jazz-ireal/sitemap.xml" not in (ROOT / "robots.txt").read_text(encoding="utf-8"):
        fail("robots.txt does not reference sitemap.xml")

    print(f"Validated {len(ja_pages) + len(en_pages):,} detail pages, 2 indexes, and {len(urls):,} sitemap URLs.")


def html_unescape(value: str) -> str:
    return value.replace("&amp;", "&")


if __name__ == "__main__":
    main()
