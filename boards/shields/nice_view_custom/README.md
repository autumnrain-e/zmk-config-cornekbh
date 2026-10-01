# nice!view with custom pictures (right half)

The right half's screen shows a picture below the battery and connection icons.
Stock ZMK compiles that picture into the firmware from its own `nice_view` shield,
which picks a hot-air balloon or a mountain at random. To show our own pictures,
this folder holds a copy of that shield, and `build.yaml` uses it for the right
half. The left half still uses ZMK's stock `nice_view`.

The copy comes from ZMK v0.3 (`app/boards/shields/nice_view`). It differs in
four ways:

- **It is renamed to `nice_view_custom`**: the folder, the file names and the
  Kconfig options (`CONFIG_NICE_VIEW_CUSTOM_WIDGET_*`). With its own name, it
  can't clash with ZMK's shield.
- **`widgets/peripheral_status.c`** shows our pictures instead of the balloon
  or the mountain. They take turns, switching every minute (see
  [Changing pictures over time](#changing-pictures-over-time)).
- **`Kconfig.defconfig`** adds the setting for how often the picture changes.
- **`widgets/art.c`** holds our pictures. `art/make_art.py` generates it from
  the images in `art/`. The comment at the top of `art.c` shows the exact command
  that made it. The current pictures are `art/corne_kbh.png` ("CorneKBH" and a
  mini keyboard), `art/coffee.png` (a steaming cup in front of a retro sunset),
  `art/black_cat.png` (a black cat on a wall in front of the full moon),
  `art/poodles.png` (a white mother poodle with a halo, on a cloud, above her
  two brown pups), `art/woman_and_kid.png` (an anime-style woman hugging a
  laughing toddler) and `art/autumn_rain.png` (maple leaves falling through the
  rain at night, above the owner's handle, "autumnrain-e"). All are drawn pixel
  by pixel at the screen's exact size.

When you upgrade ZMK, compare this folder with the new version's
`app/boards/shields/nice_view` in case upstream changed something.

## Adding or changing pictures

1. **Pick an image.** The picture area is 68 pixels wide and 140 tall, as you
   look at the keyboard. Any size works because the script shrinks it to fit.
   An image that is exactly 68 × 140 is used pixel for pixel, so you can draw
   one in any pixel editor. The screen shows only black and white, so simple,
   high-contrast images work best. White in the image shows as white on the
   screen. The strip above the picture (battery and connection icons) is black
   with white icons.
2. **Save it in `art/` and convert it.** Keeping it in `art/` records where the
   picture came from. From the repo root, run the command at the top of
   `widgets/art.c` with your new image added to the list:

   ```sh
   python3 boards/shields/nice_view_custom/art/make_art.py \
     boards/shields/nice_view_custom/art/corne_kbh.png \
     boards/shields/nice_view_custom/art/coffee.png \
     boards/shields/nice_view_custom/art/black_cat.png \
     boards/shields/nice_view_custom/art/poodles.png \
     boards/shields/nice_view_custom/art/woman_and_kid.png \
     boards/shields/nice_view_custom/art/autumn_rain.png \
     boards/shields/nice_view_custom/art/my_picture.png --preview /tmp/preview.png
   ```

   This rewrites `widgets/art.c` with every image in the list (at most 32), so
   leave one out to remove it. Open `/tmp/preview.png` to check the results side by side.
   For logos, text or line art, add `--threshold 128` for clean edges instead of
   a dot pattern. Add `--crop` to fill the whole area instead of adding white
   bars. The script needs Pillow (`pip install pillow`); `uv run` installs it
   automatically.
3. **Commit, push and flash.** Commit `widgets/art.c` together with the images
   and push. When the CI build passes, flash only the right half with
   `corne_right nice_view_adapter nice_view_custom-nice_nano_v2-zmk.uf2`.

Studio's saved settings only cover the keymap, so they never hide a new
picture.

## Changing pictures over time

When the right half starts, it shows one picture picked at random, then
switches to the next one every minute. The pictures take turns like a shuffled
deck of cards: each one is shown once, in a random order, before any of them
comes back. A new round never starts with the picture already on screen. With
six pictures you see all of them every six minutes.

To change how often, set `CONFIG_NICE_VIEW_CUSTOM_WIDGET_ART_INTERVAL_SEC` in
`nice_view_custom.conf`, in seconds. Set it to `0` to keep the first picture
until the next start. The timer only runs while the keyboard is awake: during
deep sleep (after `CONFIG_ZMK_IDLE_SLEEP_TIMEOUT` in `config/corne.conf`)
nothing changes, and waking up starts a new round.

The battery cost is negligible. The nice!view is a memory LCD, which holds its
image without power-hungry refreshing, and ZMK already wakes the chip 100 times
a second to run the screen. Switching pictures once a minute only sends about
1 KB to the screen.

## Inverting the colors

`CONFIG_NICE_VIEW_CUSTOM_WIDGET_INVERTED=y` swaps black and white on the right
half's screen. Set it in `nice_view_custom.conf`, which only the right half
loads. `config/corne.conf` would also work, but that file is shared with the left
half. The left half's build can't use this option, so it ignores it and prints an
"assigned the value 'y' but got the value 'n'" warning.
