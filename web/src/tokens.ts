/**
 * Typed design-token mirror for JS/SVG consumers.
 *
 * The canonical values live as CSS custom properties in `src/index.css` and are
 * consumed in inline styles via `var(--x)`. This module mirrors the values that
 * SVG presentation props and numeric props need (var() is not valid there).
 * Keep the two in sync; both are documented in web/DESIGN.md.
 */

export const mapColors = {
  selection: "#ffa94d",
  dim: "#9ca3af",
  empty: "#e8e8f0",
  stroke: "#d0d0d8",
} as const;

export const radius = {
  sm: 4,
  md: 6,
  lg: 8,
  button: 24,
  pill: 9999,
} as const;

export const shadow = {
  card: "0 4px 14px rgba(0, 0, 0, 0.08)",
  cardHover: "0 6px 20px rgba(0, 0, 0, 0.12)",
  drawer: "-4px 0 24px rgba(0, 0, 0, 0.12)",
} as const;

export const zIndex = {
  drawer: 10,
  tooltip: 20,
  hint: 30,
} as const;

export const transition = {
  fast: 150,
  base: 200,
  slow: 300,
} as const;
