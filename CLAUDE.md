<!-- Maintainers: keep this under 150 lines. It loads every session; put
specialized detail in .claude/docs/ and link it from the last section. -->

# CLAUDE.md

## Project overview

ZMK firmware config for a wireless **Corne** split keyboard ("CorneKBH"). The repo
started from a vendor template (keyboard-hoarders) and is now the owner's personal
config. There is no application code. The repo is the *input* to a ZMK build: a
devicetree keymap, Kconfig flags and a build matrix. GitHub Actions compiles them
into `.uf2` firmware files, which get flashed onto each half.

The owner is learning ZMK, so explain changes in plain language, in comments as well
as in chat.

## Tech stack

- **ZMK v0.3** (on Zephyr RTOS). The version is pinned in two places that must
  always match: `config/west.yml:3` and `.github/workflows/build.yml:6`
- **Hardware:** 2 × nice!nano v2 (nRF52840, Bluetooth) with nice!view displays;
  42 keys (3×6 plus 3 thumb keys per half); the left half is the central
- **Keymap:** devicetree plus the C preprocessor (`#include`, `#define`)
- **Features:** Kconfig flags in `config/corne.conf`
- **Build:** West manifest, plus GitHub Actions calling ZMK's reusable
  `build-user-config.yml`
- **ZMK Studio** (zmk.studio): a browser-based live keymap editor, enabled over USB
  on the left half

## Key files and directories

| Path | Purpose |
|---|---|
| `config/corne.keymap` | Everything the keys do: built-in tuning `:20-26`, custom behaviors `:29-68`, macros `:70-90`, combos `:92-194`, the 5 layers `:198-270` |
| `config/corne.conf` | Kconfig for **both** halves: BT power, sleep, name, Studio, pointing (mouse keys), debounce |
| `build.yaml` | CI build matrix (`:21-28`): left half with the Studio snippet, right half, `settings_reset` |
| `config/west.yml` | Pins the ZMK revision. External modules go here (`:7-8`) |
| `.github/workflows/build.yml` | Runs the ZMK build on every push, every PR and manual dispatch |
| `zephyr/module.yml`, `boards/shields/` | Make the repo a Zephyr module so custom shields can live in `boards/shields/`. The Corne shield comes from upstream ZMK |
| `boards/shields/nice_view_custom/` | A renamed copy of ZMK v0.3's `nice_view` shield, used by the right half only, so its screen shows our own pictures, taking turns in a random order every minute. Its `README.md` explains how to add or change pictures |
| `README.md` | The vendor's end-user guide and images. It describes the vendor's keymap, not necessarily the current one |

## Build and verify

There is no test suite and no local toolchain (`west` is not installed).
**The CI build is the check.** A change compiles only when the GitHub Actions run
passes. Whether it *behaves* correctly is something only the owner can confirm, by
typing on the keyboard.

```sh
git push                                 # triggers "Build ZMK firmware" (~2 min)
gh run watch                             # follow the latest run
gh run list -L 5                         # recent runs and their status
gh run view <run-id> --log-failed        # devicetree/Kconfig errors land here
gh run download <run-id> -n firmware -D ~/Downloads/corne-fw   # the 3 .uf2 files
gh workflow run build.yml                # rebuild without a commit
```

Local builds, flashing order and `settings_reset` are covered in
`.claude/docs/build_and_flash.md`.

**Commits:** imperative, sentence-case subject with no type prefix, and a body that
says what the change does on the keyboard (see `git log`). Work lands directly on
`main`.

## Gotchas

- **IMPORTANT:** once Studio has saved changes, the keyboard **ignores later edits to
  `corne.keymap`** until someone runs "Restore Stock Settings" in Studio. A passing
  build does not mean the keyboard runs the file's keymap. Tell the owner this
  whenever you change the keymap.
- A behavior the file never binds is not necessarily dead code. Some, such as
  `closenvim` (`config/corne.keymap:83-88`, which has a `display-name`), are defined
  so they can be bound through Studio. Ask before you delete one.
- The ASCII layer diagrams in the keymap comments (`:204-208`, `:221-225`, `:238-242`)
  are stale. The `bindings` are the source of truth.
- The zmk.dev docs default to ZMK `main`, and some syntax there differs from v0.3 (for
  example, `main` names the board `nice_nano//zmk`; v0.3 uses `nice_nano_v2`).
  Confirm that a feature exists in v0.3 before you use it.
- Layer references use numeric literals (`&mo 1`, `&lt 2`, `layers = <0>`) even though
  `#define`s exist at `:6-10`. Reordering layers means updating every literal.

## Additional documentation

Read these when the task touches their topic:

- `.claude/docs/architectural_patterns.md`: how the config is organized, which
  features span several files, naming and comment conventions. **Read it before any
  structural change.**
- `.claude/docs/keymap_editing.md`: the key-position grid, how the layers are
  reached, and checklists for adding combos, behaviors, macros and layers. **Read it
  before you edit `corne.keymap`.**
- `.claude/docs/build_and_flash.md`: the CI pipeline and its artifacts, a local
  build recipe, flashing each half, `settings_reset` and bootloader access.
