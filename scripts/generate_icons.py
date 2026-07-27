#!/usr/bin/env python3
"""PWA用アイコン(icons/icon-192.png, icon-512.png)を生成するスクリプト。

アプリのダークテーマ(#14110E)とブラス色(#D9A441)を使い、
中央にブラス色の円と再生三角(iReal Pro連携ボタンのモチーフ)を配置する。
再実行すれば同じデザインで再生成できる。

使い方:
  python3 scripts/generate_icons.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
ICONS_DIR = SCRIPT_DIR.parent / "icons"

BG = (20, 17, 14)
BRASS = (217, 164, 65)
BRASS_DEEP = (176, 127, 44)
DARK_INK = (26, 18, 6)


def draw_icon(size):
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)

    center = size / 2
    radius = size * 0.34

    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill=BRASS,
        outline=BRASS_DEEP,
        width=max(2, round(size * 0.01)),
    )

    tri_h = radius * 1.05
    tri_w = radius * 0.95
    offset = radius * 0.08
    x0 = center - tri_w * 0.42 + offset
    y0 = center - tri_h / 2
    x1 = center - tri_w * 0.42 + offset
    y1 = center + tri_h / 2
    x2 = center + tri_w * 0.58 + offset
    y2 = center
    draw.polygon([(x0, y0), (x1, y1), (x2, y2)], fill=DARK_INK)

    return img


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        icon = draw_icon(size)
        out_path = ICONS_DIR / f"icon-{size}.png"
        icon.save(out_path)
        print(f"生成しました: {out_path}")


if __name__ == "__main__":
    main()
