#!/usr/bin/env python3
# /// script
# dependencies = ["pillow"]
# ///
"""Turn an image into the picture shown on the right half's nice!view.

Usage (from the repo root):

    python3 boards/shields/nice_view_custom/art/make_art.py my_picture.png

It overwrites boards/shields/nice_view_custom/widgets/art.c. Commit that file
and push; the next CI build puts the picture into the right half's firmware.

The picture area is 68 pixels wide and 140 pixels tall, as you look at the
keyboard (the 20 pixels above it show the battery and connection icons).
Any image size works: it is shrunk to fit, and converted to pure black and
white because the screen has no greys.

Options:
    --crop           fill the whole area and cut off the edges that don't fit,
                     instead of shrinking the image and adding white bars
    --threshold N    plain black/white cut at brightness N (0-255, try 128).
                     Best for logos, text and line art. Without it, greys are
                     turned into a dot pattern (dithering), which suits photos.
    --preview FILE   also save a PNG of the result, enlarged 4x, to check it
                     before flashing

Needs the Pillow library (pip install pillow), or run it with
`uv run make_art.py ...`, which installs it automatically.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageOps

# Size of the picture as seen on the keyboard (portrait).
WIDTH, HEIGHT = 68, 140

SHIELD_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SHIELD_DIR.parent.parent.parent
OUTPUT = SHIELD_DIR / "widgets" / "art.c"


def load_portrait(path, crop):
    """Open the image and fit it into WIDTH x HEIGHT, in greyscale."""
    img = Image.open(path)
    # Transparent areas would turn black; put the image on white first.
    img = img.convert("RGBA")
    background = Image.new("RGBA", img.size, "white")
    img = Image.alpha_composite(background, img).convert("L")

    if img.size == (WIDTH, HEIGHT):
        return img  # Already the right size: keep every pixel as drawn.
    if crop:
        return ImageOps.fit(img, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    img = ImageOps.contain(img, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    canvas = Image.new("L", (WIDTH, HEIGHT), 255)
    canvas.paste(img, ((WIDTH - img.width) // 2, (HEIGHT - img.height) // 2))
    return canvas


def to_black_and_white(img, threshold):
    if threshold is None:
        return img.convert("1")  # Floyd-Steinberg dithering
    return img.point(lambda p: 255 if p >= threshold else 0).convert(
        "1", dither=Image.Dither.NONE
    )


def c_source(data, source_name):
    rows = []
    for i in range(0, len(data), 15):
        rows.append("        " + ", ".join(f"0x{b:02x}" for b in data[i : i + 15]) + ",")
    body = "\n".join(rows)
    return f"""/*
 * The picture shown on the right half's nice!view.
 *
 * GENERATED FILE, do not edit by hand. It was made from
 *     {source_name}
 * by boards/shields/nice_view_custom/art/make_art.py.
 *
 * Format: an LVGL 8 image (the graphics library ZMK v0.3 uses), 140 x 68
 * pixels, 1 bit per pixel (0 = black, 1 = white), 8 pixels per byte. It is
 * stored turned 90 degrees clockwise because the screen is mounted sideways.
 */

#include <lvgl.h>

#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

#ifndef LV_ATTRIBUTE_IMG_CUSTOM_ART
#define LV_ATTRIBUTE_IMG_CUSTOM_ART
#endif

const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_CUSTOM_ART uint8_t
    custom_art_map[] = {{
#if CONFIG_NICE_VIEW_CUSTOM_WIDGET_INVERTED
        0xff, 0xff, 0xff, 0xff, /*Color of index 0*/
        0x00, 0x00, 0x00, 0xff, /*Color of index 1*/
#else
        0x00, 0x00, 0x00, 0xff, /*Color of index 0*/
        0xff, 0xff, 0xff, 0xff, /*Color of index 1*/
#endif

{body}
}};

const lv_img_dsc_t custom_art = {{
    .header.cf = LV_IMG_CF_INDEXED_1BIT,
    .header.always_zero = 0,
    .header.reserved = 0,
    .header.w = {HEIGHT},
    .header.h = {WIDTH},
    .data_size = {len(data) + 8},
    .data = custom_art_map,
}};
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image", type=Path)
    parser.add_argument("--crop", action="store_true")
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()

    picture = to_black_and_white(load_portrait(args.image, args.crop), args.threshold)
    if args.preview:
        picture.resize((WIDTH * 4, HEIGHT * 4), Image.Resampling.NEAREST).save(args.preview)

    # Turn it on its side (90 degrees clockwise) to match the screen, then pack
    # the pixels into bytes. Each row of 140 pixels takes 18 bytes (the last
    # 4 bits are padding), which is the layout LVGL expects.
    sideways = picture.transpose(Image.Transpose.ROTATE_270)
    data = sideways.tobytes()
    assert len(data) == 18 * WIDTH, len(data)

    source = args.image.resolve()
    source_name = source.relative_to(REPO_ROOT) if source.is_relative_to(REPO_ROOT) else source.name
    OUTPUT.write_text(c_source(data, source_name))
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
