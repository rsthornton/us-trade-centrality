import type { ReactNode } from "react";
import { tint } from "./style";

export type BadgeTone = "neutral" | "green" | "blue" | "red";

export interface BadgeProps {
  tone?: BadgeTone;
  /** Explicit color overrides tone (hex or CSS var). */
  color?: string;
  mono?: boolean;
  children: ReactNode;
}

const TONE_COLORS: Record<BadgeTone, string> = {
  neutral: "var(--text-muted)",
  green: "var(--accent-green)",
  blue: "var(--accent-blue)",
  red: "var(--accent-red)",
};

export default function Badge({ tone = "neutral", color, mono = true, children }: BadgeProps) {
  const c = color ?? TONE_COLORS[tone];
  return (
    <span
      className={`${mono ? "font-mono" : ""} text-sm font-semibold px-1.5 py-0.5 rounded`}
      style={{ color: c, backgroundColor: tint(c, 8) }}
    >
      {children}
    </span>
  );
}
