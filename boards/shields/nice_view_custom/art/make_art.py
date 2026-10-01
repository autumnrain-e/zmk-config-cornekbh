#!/usr/bin/env python3
# /// script
# dependencies = ["pillow"]
# ///
"""Turn images into the pictures shown on the right half's nice!view.

Usage (from the repo root), listing every picture you want on the keyboard:

    python3 boards/shields/nice_view_custom/art/make_art.py first.png second.png

It overwrites boards/shields/nice_view_custom/widgets/art.c with all of them
(at most 32). The right half shows them in turns, in a random order, switching
every minute (see nice_view_custom.conf to change that). Commit art.c and push;
the next CI build puts the pictures into the right half's firmware. To drop a
picture, run the command again without it.

The picture area is 68 pixels wide and 140 pixels tall, as you look at the
keyboard (the 20 pixels above it show the battery and connection icons).
Any image size works: it is shrunk to fit, and converted to pure black and
white because the screen has no greys.

Options (they apply to every image):
    --crop           fill the whole area and cut off the edges that don't fit,
                     instead of shrinking the image and adding white bars
    --threshold N    plain black/white cut at brightness N (0-255, try 128).
                     Best for logos, text and line art. Without it, greys are
                     turned into a dot pattern (dithering), which suits photos.
    --preview FILE   also save a PNG of the results side by side, enlarged 4x,
                     to check them before flashing

Needs the Pillow library (pip install pillow), or run it with
`uv run make_art.py ...`, which installs it automatically.
"""

import argparse
import re
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


def c_picture(name, source_name, data):
    """C code for one picture: its pixels, and the LVGL image that uses them."""
    rows = []
    for i in range(0, len(data), 15):
        rows.append("        " + ", ".join(f"0x{b:02x}" for b in data[i : i + 15]) + ",")
    body = "\n".join(rows)
    return f"""
// From {source_name}
const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_CUSTOM_ART uint8_t
    {name}_map[] = {{
#if CONFIG_NICE_VIEW_CUSTOM_WIDGET_INVERTED
        0xff, 0xff, 0xff, 0xff, /*Color of index 0*/
        0x00, 0x00, 0x00, 0xff, /*Color of index 1*/
#else
        0x00, 0x00, 0x00, 0xff, /*Color of index 0*/
        0xff, 0xff, 0xff, 0xff, /*Color of index 1*/
#endif

{body}
}};

const lv_img_dsc_t {name} = {{
    .header.cf = LV_IMG_CF_INDEXED_1BIT,
    .header.always_zero = 0,
    .header.reserved = 0,
    .header.w = {HEIGHT},
    .header.h = {WIDTH},
    .data_size = {len(data) + 8},
    .data = {name}_map,
}};
"""


def c_source(pictures, command):
    """The whole art.c: every picture, then the list the right half picks from."""
    images = "".join(c_picture(name, source_name, data) for name, source_name, data in pictures)
    names = "\n".join(f"    &{name}," for name, _, _ in pictures)
    return f"""/*
 * The pictures shown on the right half's nice!view. They take turns on the
 * screen in a random order (see peripheral_status.c).
 *
 * GENERATED FILE, do not edit by hand. To rebuild it, run from the repo root:
 *     python3 boards/shields/nice_view_custom/art/{command}
 *
 * Format: LVGL 8 images (the graphics library ZMK v0.3 uses), 140 x 68
 * pixels, 1 bit per pixel, 8 pixels per byte. On the nice!view a 1 shows as
 * black and a 0 as white (the display driver flips LVGL's colors). They are
 * stored turned 90 degrees clockwise because the screen is mounted sideways.
 */

#include <stddef.h>
#include <lvgl.h>

#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

#ifndef LV_ATTRIBUTE_IMG_CUSTOM_ART
#define LV_ATTRIBUTE_IMG_CUSTOM_ART
#endif
{images}
// The list the right half picks from, and how many pictures it holds.
const lv_img_dsc_t *const custom_arts[] = {{
{names}
}};
const size_t custom_arts_count = sizeof(custom_arts) / sizeof(custom_arts[0]);
"""


def to_bytes(picture):
    # Turn it on its side (90 degrees clockwise) to match the screen, then pack
    # the pixels into bytes. Each row of 140 pixels takes 18 bytes (the last
    # 4 bits are padding), which is the layout LVGL expects.
    sideways = picture.transpose(Image.Transpose.ROTATE_270)
    # Flip every pixel. The nice!view's display driver in ZMK v0.3 shows LVGL's
    # "white" as a dark pixel and its "black" as a light one (ZMK's own pictures
    # are drawn that way too), so without this the screen shows a negative.
    data = bytes(b ^ 0xFF for b in sideways.tobytes())
    assert len(data) == 18 * WIDTH, len(data)
    return data


def repo_path(path):
    """The path as written in art.c: relative to the repo root when possible."""
    source = path.resolve()
    return source.relative_to(REPO_ROOT) if source.is_relative_to(REPO_ROOT) else source.name


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("images", type=Path, nargs="+")
    parser.add_argument("--crop", action="store_true")
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    # peripheral_status.c tracks which pictures it has shown in 32 bits.
    if len(args.images) > 32:
        parser.error("at most 32 pictures fit (see peripheral_status.c)")

    pictures, previews = [], []
    for path in args.images:
        # The C name comes from the file name: art/coffee.png -> custom_art_coffee.
        name = "custom_art_" + re.sub(r"\W+", "_", path.stem.lower())
        if any(name == other for other, _, _ in pictures):
            parser.error(f"two images would both be called {name}; rename one")
        picture = to_black_and_white(load_portrait(path, args.crop), args.threshold)
        previews.append(picture)
        pictures.append((name, repo_path(path), to_bytes(picture)))

    if args.preview:
        sheet = Image.new("1", ((WIDTH + 4) * len(previews) - 4, HEIGHT), 0)
        for i, picture in enumerate(previews):
            sheet.paste(picture, (i * (WIDTH + 4), 0))
        sheet.resize((sheet.width * 4, HEIGHT * 4), Image.Resampling.NEAREST).save(args.preview)

    # Record the exact command in art.c, so the pictures can be rebuilt later.
    command = "make_art.py " + " ".join(str(source_name) for _, source_name, _ in pictures)
    if args.crop:
        command += " --crop"
    if args.threshold is not None:
        command += f" --threshold {args.threshold}"
    OUTPUT.write_text(c_source(pictures, command))
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)} with {len(pictures)} picture(s)")


if __name__ == "__main__":
    main()
