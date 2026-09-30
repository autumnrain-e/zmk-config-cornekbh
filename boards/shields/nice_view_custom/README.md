# nice!view with a custom picture (right half)

The right half's screen shows a picture below the battery and connection icons.
Stock ZMK compiles that picture into the firmware from its own `nice_view` shield,
which picks a hot-air balloon or a mountain at random. To show our own picture,
this folder holds a copy of that shield, and `build.yaml` uses it for the right
half. The left half still uses ZMK's stock `nice_view`.

The copy comes from ZMK v0.3 (`app/boards/shields/nice_view`). It differs in
three ways:

- **It is renamed to `nice_view_custom`**: the folder, the file names and the
  Kconfig options (`CONFIG_NICE_VIEW_CUSTOM_WIDGET_*`). With its own name, it
  can't clash with ZMK's shield.
- **`widgets/peripheral_status.c`** always shows `custom_art` instead of picking
  at random.
- **`widgets/art.c`** holds our picture. `art/make_art.py` generates it from
  `art/corne_kbh.png`.

When you upgrade ZMK, compare this folder with the new version's
`app/boards/shields/nice_view` in case upstream changed something.

## Changing the picture

1. **Pick an image.** The picture area is 68 pixels wide and 140 tall, as you
   look at the keyboard. Any size works because the script shrinks it to fit.
   The screen shows only black and white, so simple, high-contrast images work
   best.
2. **Save it in `art/` and convert it.** Keeping it in `art/` records where the
   picture came from. Run this from the repo root:

   ```sh
   python3 boards/shields/nice_view_custom/art/make_art.py \
     boards/shields/nice_view_custom/art/my_picture.png --preview /tmp/preview.png
   ```

   This rewrites `widgets/art.c`. Open `/tmp/preview.png` to check the result.
   For logos, text or line art, add `--threshold 128` for clean edges instead of
   a dot pattern. Add `--crop` to fill the whole area instead of adding white
   bars. The script needs Pillow (`pip install pillow`); `uv run` installs it
   automatically.
3. **Commit, push and flash.** Commit `widgets/art.c` together with the image
   and push. When the CI build passes, flash only the right half with
   `corne_right nice_view_adapter nice_view_custom-nice_nano_v2-zmk.uf2`.

Studio's saved settings only cover the keymap, so they never hide a new
picture.

## Inverting the colors

`CONFIG_NICE_VIEW_CUSTOM_WIDGET_INVERTED=y` swaps black and white on the right
half's screen. Set it in `nice_view_custom.conf`, which only the right half
loads. **Don't set it in `config/corne.conf`.** That file is shared with the left
half, whose build doesn't know this option and would fail.
