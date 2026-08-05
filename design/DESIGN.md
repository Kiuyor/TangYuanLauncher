---
version: alpha
name: Rev.Ini Editor (MD3 Dark / Amber)
description: Material Design 3 dark theme with an amber-orange primary for a CS:GO config editor. Calm, precise, trustworthy.
colors:
  # ---- Primary (amber orange, derived from #ff9f1c) ----
  primary: "#ffb868"
  on-primary: "#4a2800"
  primary-container: "#6d3c00"
  on-primary-container: "#ffdcc0"
  primary-hover: "#f0ac5f"
  # ---- Secondary / Tertiary ----
  secondary: "#dbc5a6"
  on-secondary: "#3d2e1a"
  secondary-container: "#5c462d"
  on-secondary-container: "#f9dfc4"
  tertiary: "#b8cca4"
  tertiary-container: "#3e4f31"
  on-tertiary-container: "#d3e9be"
  # ---- Error ----
  error: "#ffb4ab"
  error-container: "#93000a"
  on-error-container: "#ffdad6"
  # ---- Surface elevation (dark theme, no shadows) ----
  surface: "#121212"
  surface-dim: "#121212"
  surface-bright: "#3a3836"
  surface-lowest: "#0d0d0d"
  surface-low: "#1b1b1b"
  surface-container: "#211f1e"
  surface-high: "#2c2a28"
  surface-highest: "#373533"
  surface-tint: "#ffb868"
  card-hover: "#2b2b2b"
  field-hover: "#454341"
  tonal-hover: "#67523b"
  field-border: "#5c544d"
  # ---- Text / outlines ----
  on-surface: "#e6e1df"
  on-surface-variant: "#cdc5bf"
  outline: "#9a8f88"
  outline-variant: "#4e4640"
  scrim: "#000000"
  # ---- Inverse (Snackbar) ----
  inverse-surface: "#e6e1df"
  inverse-on-surface: "#1b1b1b"
  inverse-primary: "#6d3c00"
  # ---- State layers (#AARRGGBB, alpha in high byte) ----
  state-layer-on-surface-5: "#0ce6e1df"
  state-layer-on-surface-6: "#0fe6e1df"
  state-layer-on-surface-7: "#12e6e1df"
  state-layer-on-surface-8: "#14e6e1df"
  state-layer-on-surface-9: "#16e6e1df"
  state-layer-on-surface-12: "#1ee6e1df"
  state-layer-error-12: "#1effb4ab"
  state-layer-error-16: "#2affb4ab"
  state-layer-error-container-7: "#1293000a"
  state-layer-error-container-12: "#1e93000a"
typography:
  title-large:
    fontFamily: "Google Sans, Noto Sans SC, Microsoft YaHei UI, sans-serif"
    fontSize: 22px
    fontWeight: 400
    lineHeight: 1.27
    letterSpacing: "0em"
  title-medium:
    fontFamily: "Google Sans, Noto Sans SC, Microsoft YaHei UI, sans-serif"
    fontSize: 16px
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0.15px"
  title-small:
    fontFamily: "Google Sans, Noto Sans SC, Microsoft YaHei UI, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.43
    letterSpacing: "0.1px"
  body-large:
    fontFamily: "Google Sans, Noto Sans SC, Microsoft YaHei UI, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0.5px"
  body-medium:
    fontFamily: "Google Sans, Noto Sans SC, Microsoft YaHei UI, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.43
    letterSpacing: "0.25px"
  body-small:
    fontFamily: "Google Sans, Noto Sans SC, Microsoft YaHei UI, sans-serif"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.33
    letterSpacing: "0.4px"
  label-large:
    fontFamily: "Google Sans, Noto Sans SC, Microsoft YaHei UI, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.43
    letterSpacing: "0.1px"
  label-small:
    fontFamily: "JetBrains Mono, Consolas, monospace"
    fontSize: 11px
    fontWeight: 500
    lineHeight: 1.45
    letterSpacing: "0.5px"
rounded:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
components:
  # ---- Buttons (self-painted RoundButton) ----
  button-filled:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.full}"
    padding: 12px
  button-filled-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.full}"
  button-filled-down:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    rounded: "{rounded.full}"
  button-outlined:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: 12px
  button-tonal:
    backgroundColor: "{colors.secondary-container}"
    textColor: "{colors.on-secondary-container}"
    rounded: "{rounded.full}"
  button-tonal-hover:
    backgroundColor: "{colors.tonal-hover}"
    textColor: "{colors.on-secondary-container}"
    rounded: "{rounded.full}"
  button-danger:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.error}"
    rounded: "{rounded.full}"
  button-danger-hover:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.on-error-container}"
    rounded: "{rounded.full}"
  button-icon:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.on-surface-variant}"
    rounded: "{rounded.full}"
  button-link:
    backgroundColor: "{colors.inverse-surface}"
    textColor: "{colors.inverse-primary}"
  # ---- Chips (assist / filter) ----
  chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface-variant}"
    rounded: "{rounded.full}"
  chip-hover:
    backgroundColor: "{colors.secondary-container}"
    textColor: "{colors.on-secondary-container}"
    rounded: "{rounded.full}"
  chip-selected:
    backgroundColor: "{colors.secondary-container}"
    textColor: "{colors.on-secondary-container}"
    rounded: "{rounded.full}"
  chip-pressed:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    rounded: "{rounded.full}"
  # ---- Cards ----
  card:
    backgroundColor: "{colors.surface-low}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: 16px
  card-hover:
    backgroundColor: "{colors.card-hover}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
  card-flash:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
  card-desc:
    backgroundColor: "{colors.surface-low}"
    textColor: "{colors.on-surface-variant}"
  # ---- Text fields (filled) ----
  text-field:
    backgroundColor: "{colors.surface-highest}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.sm}"
  text-field-hover:
    backgroundColor: "{colors.field-hover}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.sm}"
  text-field-disabled:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.outline}"
    rounded: "{rounded.sm}"
  # ---- Search ----
  search-box:
    backgroundColor: "{colors.surface-high}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.sm}"
  search-panel:
    backgroundColor: "{colors.surface-highest}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
  search-result-selected:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    rounded: "{rounded.sm}"
  # ---- Navigation rail ----
  nav-rail:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.on-surface-variant}"
  nav-item-selected:
    backgroundColor: "{colors.secondary-container}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
  # ---- Switch ----
  switch-on:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.full}"
  # ---- Tabs ----
  tab-selected:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
  tab-hover:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
  # ---- Snackbar (inverse surface) ----
  snackbar:
    backgroundColor: "{colors.inverse-surface}"
    textColor: "{colors.inverse-on-surface}"
    rounded: "{rounded.full}"
  snackbar-action:
    backgroundColor: "{colors.inverse-surface}"
    textColor: "{colors.inverse-primary}"
  snackbar-action-error:
    backgroundColor: "{colors.inverse-surface}"
    textColor: "{colors.error-container}"
  snackbar-icon-error:
    backgroundColor: "{colors.inverse-surface}"
    textColor: "{colors.error-container}"
  # ---- Tool page ----
  tool-card:
    backgroundColor: "{colors.surface-low}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
  tool-cat-badge:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
  tool-status-ok:
    backgroundColor: "{colors.surface-low}"
    textColor: "{colors.tertiary}"
  tool-status-err:
    backgroundColor: "{colors.surface-low}"
    textColor: "{colors.error}"
  # ---- Dialog / status bar / tooltip ----
  dialog:
    backgroundColor: "{colors.surface-high}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
  dialog-msg:
    backgroundColor: "{colors.surface-high}"
    textColor: "{colors.on-surface-variant}"
  status-bar:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.on-surface}"
  status-ok:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.tertiary}"
  status-err:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.error}"
  version-badge:
    backgroundColor: "{colors.surface-high}"
    textColor: "{colors.on-surface-variant}"
    rounded: "{rounded.full}"
  tooltip:
    backgroundColor: "{colors.surface-high}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.sm}"
---

## Overview

Rev.Ini Editor is a CS:GO config tool for no-steam players. The identity is
**modern, precise, trustworthy**: a strict Material Design 3 dark theme
(`#121212` base) with a warm amber-orange primary. Hierarchy is built with
surface elevation (progressively lighter containers), never shadows. State
changes speak through 5–16% state-layer overlays, motion through
emphasized easing at 100–300ms. The UI should feel like Android's settings
app: calm, structured, and invisible in service of the task.

## Colors

- **Primary ({colors.primary}):** The amber signal — selected states, the
  launch-game button, focus underlines, search-result jumps. Used sparingly
  so it keeps its meaning.
- **On-surface ({colors.on-surface}) vs On-surface-variant
  ({colors.on-surface-variant}):** Primary text vs secondary text/keys.
  Variant stays readable on every surface level (≥ 7:1).
- **Surfaces:** `surface` (window) → `surface-low` (cards) →
  `surface-container` (rail, bars) → `surface-high` (search, dialogs) →
  `surface-highest` (popups, dropdowns).
- **Error ({colors.error})** appears only on dark surfaces; on the light
  inverse-surface Snackbar, error content switches to
  `error-container` ({colors.error-container}) to hold WCAG AA.
- **State layers** are `on-surface`/`error` tints at 5–16% alpha, defined as
  `#AARRGGBB` tokens so every widget paints from the same store.

## Typography

Sans stack (Google Sans → Noto Sans SC → Microsoft YaHei UI) for all UI text;
JetBrains Mono for config keys, values, and status readouts — the "code
precise" voice. Hierarchy via weight/size: 22px title-large page heads,
16px title-medium card titles, 14px body, 11px label-small mono for keys.

## Layout

Spacing is a 4px baseline: 16px card padding, 12px inter-card gaps, 8px
control margins. Layout skeleton: 88px navigation rail | content scroll |
40px bottom bar; 64px top app bar with the launch button truly centered.

## Elevation & Depth

Dark theme uses no drop shadows. Depth = surface tone + a primary-tint
overlay at 5–14% for elevation levels 1–5. Popups sit on `surface-highest`.

## Shapes

`sm` (8px) controls, `md` (12px) cards/dialogs/search panel, `full` pills
for buttons, chips, switch, snackbar. The 4px page-head accent bar is the
only `xs` corner.

## Components

- `button-filled` is the app's single high-emphasis action (保存 / 启动游戏).
- `card` = every field row and tool card; hover lifts to `card-hover`,
  search jumps flash `card-flash`.
- `snackbar` lives on the inverse surface; its error variant uses
  `error-container` content (icon + action) to stay readable.
- `chip` starts outlined on the surface; once its args are added to the
  launch command it switches to the `chip-selected` tonal fill.
- `nav-item-selected` is a full-pill `secondary-container` indicator with a
  `primary` icon — 5.3:1, AA.

## Do's and Don'ts

- **Do** reference tokens (`{colors.primary}`) — the palette is single-source
  in `app/style.py`'s `MD3` dict; this file mirrors it.
- **Do** express states as alpha state layers, never as invented colors.
- **Don't** use `#000000` for surfaces (MD3 dark base is `#121212`).
- **Don't** put `error` (#ffb4ab) on the light inverse-surface — it fails
  WCAG AA 4.5:1; use `error-container` there.
- **Don't** nest component variants — `button-filled-hover` is a sibling.
