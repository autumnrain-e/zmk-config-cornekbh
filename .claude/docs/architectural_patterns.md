# Architectural patterns

These are the patterns and conventions that recur across this repo's files, or several
times inside `config/corne.keymap`. Line numbers were correct when this was written
(commit `942520c`). Re-check them after edits.

## 1. Features span two channels: Kconfig switches them on, devicetree uses them

ZMK splits configuration into **Kconfig** (`config/corne.conf`: compile-time feature
flags that apply to both halves) and **devicetree** (`config/corne.keymap`: what the
keys do). Most features need both, and sometimes the build matrix too. If you remove
one piece, the build fails or the feature silently stops working.

| Feature | Kconfig | Build matrix | Keymap |
|---|---|---|---|
| ZMK Studio | `corne.conf:16` `CONFIG_ZMK_STUDIO=y` | `build.yaml:24` `snippet: studio-rpc-usb-uart` (left only) | `&studio_unlock` `corne.keymap:256`; `display-name` on every layer (`:202`, `:219`, `:236`, `:253`, `:262`) and on macros (`:86`) |
| Mouse keys | `corne.conf:17` `CONFIG_ZMK_POINTING=y` | none | `#include <dt-bindings/zmk/pointing.h>` `:4`; `&mmv`/`&msc`/`&mkp` `:264-266` |
| Bluetooth | `corne.conf:8` TX power | none | `#include <dt-bindings/zmk/bt.h>` `:2`; `&bt` `:257` |

**Rule:** when you add a behavior that depends on a feature, add the Kconfig flag, the
`#include` and the binding in the same change.

## 2. The ZMK version is pinned in lockstep

`config/west.yml:3` (`revision: v0.3`) chooses the ZMK source that gets compiled.
`.github/workflows/build.yml:6` (`build-user-config.yml@v0.3`) chooses the build
pipeline. Upgrade both together, never one at a time. Anything taken from the zmk.dev
docs has to exist in the pinned version, because the site defaults to `main`.

## 3. The split halves are asymmetric: central and peripheral

The **left half is the central**: it runs the keymap, talks to the host and hosts
Studio. The right half is a peripheral that reports key presses.

- Only the left build gets the Studio USB snippet (`build.yaml:22-24` vs `:25-26`).
- The screens differ too. The left half uses ZMK's stock `nice_view` shield (a status
  screen). The right half uses `nice_view_custom` from `boards/shields/`, which shows
  one of our own pictures, picked at random at each start. Kconfig options for the
  right half's screen (`CONFIG_NICE_VIEW_CUSTOM_WIDGET_*`) go in that shield's
  `nice_view_custom.conf`.
  In `corne.conf`, the left build would ignore them with an "assigned … but got"
  warning.
- The README tells users to plug in the left half for Studio (`README.md:5`).
- `corne.conf` has no per-side split. Every flag in it applies to both halves.
- `settings_reset` (`build.yaml:27-28`) is a third, stand-alone firmware that wipes
  stored settings (see `build_and_flash.md`).

## 4. Define a behavior once, reference it by label

Custom behaviors (`corne.keymap:29-68`) and macros (`:70-90`) are nodes of the form
`label: node-name { compatible = "zmk,behavior-…"; #binding-cells = <N>; … }`.
Bindings reference them as `&label`, in combos (`:184`, `:190`) and in layers (`:229`).

- The label usually equals the node name (`paraless: paraless`, `browsertab: browsertab`).
  The one exception is `hm: homerow_mods` (`:30`).
- `#binding-cells` is the number of parameters a binding takes: `0` for macros,
  tap-dance and mod-morph (`:43`, `:57`, `:73`); `2` for hold-tap (`:32`, used as
  `&hm LSHFT A`).
- Macros come in two forms. Explicit `&macro_press`/`&macro_tap`/`&macro_release`
  sequences are used when a key must be held (`browsertab`, `:74-80`). A flat list
  of taps is used for typed strings (`closenvim`, `:87`).

## 5. Tune built-ins in place; define new behaviors only for new semantics

Built-in behaviors are adjusted with top-level node overrides (`&mt { … }` and
`&lt { … }`, `corne.keymap:20-26`), which change them everywhere. When a *different*
flavor is needed, a new node is defined instead (`hm`, `:30-39`, a tap-preferred
hold-tap with its own timings). Kconfig follows the same idea for scanning: debounce
is overridden in `corne.conf:19-21`.

Values that equal ZMK's defaults are still written out on purpose, so that they are
easy to find and tune (`corne.keymap:19`).

## 6. Layers: named indexes, display names and transparent fall-through

- Layer indexes are `#define`d (`corne.keymap:6-10`), and the layer nodes use those
  names (`DEF {`, `NAV {`, …).
- Every layer has a `display-name` for Studio.
- The upper layers are mostly `&trans`, so unassigned keys fall through to `DEF`.
- **Inconsistency:** bindings and combos use numeric literals (`&mo 1`, `&lt 2 TAB`,
  `&mo 3`, `&mo 4`, `layers = <0>`), not the macros. If you reorder layers, grep for
  both forms.

## 7. Layer access is a hand-rolled tri-layer

Holding both inner thumb keys reaches `ADJ`, in either order. Each of the two layers
maps the *other* thumb key to `&mo 3`: in NAV at `:231` and in SYM at `:248`. `EXTRA`
(mouse) is reached separately, from the base layer's outer-right key (`:213`). ZMK's
`conditional_layers` would be the built-in alternative. Changing that is a design
decision for the owner, not a cleanup. The full map is in `keymap_editing.md`.

## 8. Combo conventions

- **Positions, not keycodes:** combos are defined by `key-positions` (hardware
  indexes), so remapping a key does not move a combo.
- **Vertical pairs for symbols.** Top plus home row gives the shifted-number symbols
  on the left (`@ # $ %` at `:129`, `:123`, `:117`, `:105`) and `+ *` on the right
  (`:153`, `:141`). Home plus bottom row gives the others (`\ =` on the left;
  `_ - /` on the right).
- **Horizontal pairs for brackets:** `[ ]` (`:171-181`) and the paren/angle
  mod-morphs (`:183-193`).
- **Scope:** symbol combos are limited to the base layer with `layers = <0>`, so
  they cannot fire while NAV or SYM is active. Only `escape` and `delete`
  (`:95-103`) are global.

## 9. Shift-morph pairs

`zmk,behavior-mod-morph` with `mods = <(MOD_LSFT)>` puts a key and its shifted
variant on one binding: `paraless` gives `(` or `<` (`:53-59`); `paragreat` gives
`)` or `>` (`:61-67`). Follow this shape for any new "tap for X, Shift-tap for Y" key.

## 10. The files are also a palette for Studio

The keymap file serves two purposes: it is the stock keymap, and it is the list of
behaviors that Studio can offer. `closenvim` (`:83-88`) is defined with a
`display-name` but never bound in the file. It exists to be bound in Studio.
`hm`, `para` and the custom `caps` (`:30-51`) are also unbound in the file; NAV
binds the built-in `&caps_word` at `:229`, not `&caps`. Treat unbound behaviors as
deliberate unless the owner says otherwise.

## 11. Comment and commit conventions

- **Comments explain the effect for a ZMK beginner:** what the setting does, how to
  change it, and its default. Examples: `corne.keymap:12-19` (tap vs. hold),
  `corne.conf:10-11` (sleep timeout in ms). Recent commits exist only to improve
  such comments (`942520c`, `e87d8f0`).
- **Template comments are kept.** The explanatory headers in `build.yaml:1-19` and
  `config/west.yml:7-8`, and the commented-out RGB/OLED blocks in `corne.conf:1-6`,
  come from the upstream template. This build gets its displays from the nice!view
  entries in the `build.yaml` shield list, not from those blocks.
- **Commits:** an imperative, sentence-case subject with no prefix
  (`Add closenvim macro to quit Neovim`) and a body describing the effect on the
  keyboard.
