#!/usr/bin/env python3
"""data.js に data/translations.json の英訳を追加でマージするスクリプト。

data.js 自体は ~/jazz-index/build_data.py が生成する別リポジトリの成果物で、
このスクリプトはそれを上書きするのではなく、生成済みの data.js に対して
formEn / styleEn / harmEn / noteEn / books[].volEn を追加する後処理として使う。
data.js が build_data.py により再生成された場合は、このスクリプトを再実行すればよい。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "data.js"
TRANSLATIONS = ROOT / "data" / "translations.json"

PREFIX = "window.SONGS = "


def main():
    text = DATA_JS.read_text(encoding="utf-8")
    lines = text.split("\n", 1)
    body = lines[1] if len(lines) > 1 else lines[0]
    body = body.strip()
    header_comment = (
        "// 自動生成ファイル。手で編集しないこと。\n"
        "// 生成元は ~/jazz-index/build_data.py (このリポジトリ外)。\n"
        "// 英訳(formEn/styleEn/harmEn/noteEn/books[].volEn)は scripts/apply_translations.py が\n"
        "// data/translations.json をもとに追加している。data.js を再生成した場合は本スクリプトを再実行すること。"
    )
    if not body.startswith(PREFIX):
        raise SystemExit(f"unexpected data.js format: does not start with {PREFIX!r}")
    json_text = body[len(PREFIX):]
    if json_text.endswith(";"):
        json_text = json_text[:-1]
    songs = json.loads(json_text)

    translations = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    form_map = translations["form"]
    style_map = translations["style"]
    harm_map = translations["harmTag"]
    book_vol_map = translations["bookVol"]
    notes_map = translations["notes"]

    missing = {"form": set(), "style": set(), "harm": set(), "bookVol": set(), "note": set()}
    for song in songs:
        if song["form"] in form_map:
            song["formEn"] = form_map[song["form"]]
        else:
            missing["form"].add(song["form"])
        if song["style"] in style_map:
            song["styleEn"] = style_map[song["style"]]
        else:
            missing["style"].add(song["style"])
        harm_en = []
        for tag in song["harm"]:
            if tag in harm_map:
                harm_en.append(harm_map[tag])
            else:
                missing["harm"].add(tag)
                harm_en.append(tag)
        song["harmEn"] = harm_en
        if song["note"]:
            if song["note"] in notes_map:
                song["noteEn"] = notes_map[song["note"]]
            else:
                missing["note"].add(song["note"])
        for book in song.get("books", []):
            if book["vol"] in book_vol_map:
                book["volEn"] = book_vol_map[book["vol"]]
            else:
                missing["bookVol"].add(book["vol"])

    for category, values in missing.items():
        if values:
            print(f"warning: {len(values)} untranslated {category} value(s): {sorted(values)[:10]}")

    new_json = json.dumps(songs, ensure_ascii=False, separators=(",", ":"))
    new_body = PREFIX + new_json + ";"
    DATA_JS.write_text(header_comment + "\n" + new_body + "\n", encoding="utf-8")
    print(f"wrote {DATA_JS} ({len(songs)} songs)")


if __name__ == "__main__":
    main()
