# Building and flashing

## CI (the normal path)

`.github/workflows/build.yml` calls `zmkfirmware/zmk/.github/workflows/build-user-config.yml@v0.3`.
That workflow reads `build.yaml`, builds each matrix entry inside the
`zmkfirmware/zmk-build-arm:stable` container, and merges the outputs into one
artifact named **`firmware`**. It contains:

- `corne_left nice_view_adapter nice_view-nice_nano_v2-zmk.uf2` (with Studio)
- `corne_right nice_view_adapter nice_view_custom-nice_nano_v2-zmk.uf2` (custom
  screen pictures, from `boards/shields/nice_view_custom/`)
- `settings_reset-nice_nano_v2-zmk.uf2`

The file names contain spaces, so quote them. The `gh` commands are in `CLAUDE.md`.
When a build fails, the error usually sits in the "West Build" step of
`gh run view <id> --log-failed`. Look for devicetree syntax errors, unknown
keycodes, or a behavior used without its Kconfig flag or `#include`.

Because `zephyr/module.yml` exists, CI copies `config/` into an isolated temporary
workspace and passes the repo as `-DZMK_EXTRA_MODULES`. A west workspace cannot sit
at the repo root, because west would clone Zephyr into the repo's own `zephyr/`
folder.

## Local build (not set up; untested recipe that mirrors CI)

This needs the ZMK toolchain (Zephyr SDK plus `west`), or Docker with the image
above. Keep the workspace in `.zmk/`, which is already gitignored:

```sh
mkdir -p .zmk/config && cp config/west.yml .zmk/config/ && cd .zmk
west init -l config && west update && west zephyr-export
west build -s zmk/app -d build/left -b nice_nano_v2 -S studio-rpc-usb-uart -- \
  -DSHIELD="corne_left nice_view_adapter nice_view" \
  -DZMK_CONFIG="$PWD/../config" -DZMK_EXTRA_MODULES="$PWD/.."
west build -s zmk/app -d build/right -b nice_nano_v2 -- \
  -DSHIELD="corne_right nice_view_adapter nice_view_custom" \
  -DZMK_CONFIG="$PWD/../config" -DZMK_EXTRA_MODULES="$PWD/.."
```

The firmware lands in `.zmk/build/<side>/zephyr/zmk.uf2`. To rebuild one half, run
`west build -d build/left`. Add `-p` for a clean (pristine) rebuild after you change
boards or shields.

## Flashing (the owner does this by hand)

1. Put a half into its bootloader. Either double-tap the reset button on its
   nice!nano, or, for the right half only, press `&bootloader` on the `ADJ` layer
   (pos 34). Bootloader and reset act on the half where the key is pressed.
2. It mounts as a USB drive (`NICENANO`). Copy that side's `.uf2` onto it, and it
   reboots by itself.
3. The keymap runs on the left (central) half. A keymap-only change usually needs
   only the left half reflashed. Flash **both** halves when `corne.conf` changes,
   when ZMK is upgraded, or when you are unsure.

## `settings_reset`

Use it when pairing between the halves or with a host breaks. Flash
`settings_reset` to **both** halves, then flash the normal firmware to each, then
remove the keyboard from the host's Bluetooth list and pair again. It erases all
stored settings, including Bluetooth bonds and any keymap changes saved in Studio.
