# Editing `config/corne.keymap`

## Key positions

Combos use `key-positions`, and each layer's `bindings` list is read in this same
order: row by row, left to right, across both halves.

```
 0  1  2  3  4  5 |  6  7  8  9 10 11
12 13 14 15 16 17 | 18 19 20 21 22 23
24 25 26 27 28 29 | 30 31 32 33 34 35
         36 37 38 | 39 40 41
```

Positions 0–5, 12–17, 24–29 and 36–38 are on the left (central) half; the rest are on
the right. To find what a position does on the base layer, count along the `DEF`
bindings (`:211-214`).

## How the layers are reached

| Layer | How to reach it | Where it is bound |
|---|---|---|
| `DEF` 0, "Base" | default | none |
| `NAV` 1, "NavNum" | hold pos 37 | `&mo 1` `:214` |
| `SYM` 2, "Symbols" | hold pos 40 (tap = Tab) | `&lt 2 TAB` `:214` |
| `ADJ` 3, "System" | NAV + hold pos 40, **or** SYM + hold pos 37 | `&mo 3` `:231`, `:248` |
| `EXTRA` 4, "Extra" (mouse) | hold pos 35 | `&mo 4` `:213` |

`ADJ` holds the F-keys, Bluetooth profile select/clear, `&studio_unlock` (pos 17)
and `&bootloader` (pos 34, right half). The README calls the unlock layer "the last
layer", but it is actually `ADJ`, not `EXTRA`.

## Checklists

**Add a combo:** copy an existing node inside `combos { }` (`:92-194`). Choose
positions from the grid, and check that no other combo already uses the same pair.
Add `layers = <0>` unless the combo should also fire on the upper layers.

**Add a behavior or macro:** put it in `behaviors { }` (`:29-68`) or `macros { }`
(`:70-90`), following pattern 4 in `architectural_patterns.md`. Give it a
`display-name` if the owner might bind it in Studio. If it needs a feature flag
(mouse keys, and so on), add the flag to `corne.conf` in the same change.

**Change a layer's bindings:** each layer needs exactly 42 entries, in position
order. A miscount moves every key after the mistake to the wrong position. When you
change a layer, update or delete its ASCII comment diagram too.

**Add or reorder a layer:** every layer reference is a numeric literal. Update the
`#define`s (`:6-10`), each `&mo`/`&lt` and every combo `layers = <…>`. Give the new
layer a `display-name`.

**Tune timing:** use the `&mt`/`&lt` overrides (`:20-26`) for global changes, and
`hm` (`:30-39`) for home-row mods. Keep the plain-language comment above each value
up to date.

## Traps

- **Studio override.** If the owner has saved changes in Studio, the keyboard does not
  pick up edits to this file until "Restore Stock Settings" is run in Studio (or
  `settings_reset` is flashed). Say so after every keymap change.
- **Two different minus keys.** The `minus` combo sends `KP_MINUS`, the keypad minus
  (`:160`), while `SYM` sends `MINUS` (`:246`). Some apps treat them differently.
- **Two caps-word bindings.** The custom `caps` (`:47-51`, continue-list
  `MINUS BACKSPACE`) is not bound. `NAV` uses the built-in `&caps_word` (`:229`).
- **Keycode names.** They must exist in ZMK v0.3's `dt-bindings/zmk/keys.h`. Aliases
  are mixed freely here (`LEFT_PARENTHESIS` next to `RPAR`), and both forms are valid.
