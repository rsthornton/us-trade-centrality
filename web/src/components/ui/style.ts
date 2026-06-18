/** Shared style helpers for UI primitives. */

/**
 * Return a translucent version of a color at the given percent opacity.
 * Hex colors get an appended alpha channel; CSS vars / named colors use color-mix.
 */
export function tint(color: string, pct: number): string {
  if (color.startsWith("#") && (color.length === 7 || color.length === 4)) {
    const a = Math.round((pct / 100) * 255)
      .toString(16)
      .padStart(2, "0");
    return color + a;
  }
  return `color-mix(in srgb, ${color} ${pct}%, transparent)`;
}
