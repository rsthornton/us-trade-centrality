import type { ButtonHTMLAttributes, ReactNode } from "react";
import { tint } from "./style";

export type ButtonVariant = "ghost" | "outline" | "solid";
export type ButtonSize = "sm" | "md";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Toggle-style active state (tints with the accent). */
  active?: boolean;
  /** Accent color (hex or CSS var). Defaults to the blue accent. */
  accent?: string;
  mono?: boolean;
  children: ReactNode;
}

const SIZES: Record<ButtonSize, string> = {
  sm: "px-2.5 py-1 text-xs",
  md: "px-3 py-1.5 text-sm",
};

export default function Button({
  variant = "outline",
  size = "md",
  active = false,
  accent = "var(--accent-blue)",
  mono = false,
  className = "",
  style,
  children,
  ...rest
}: ButtonProps) {
  const base =
    "rounded font-medium border cursor-pointer transition-all duration-200 " +
    "disabled:opacity-40 disabled:cursor-not-allowed";

  let computed: React.CSSProperties;
  if (variant === "solid") {
    computed = { backgroundColor: accent, borderColor: accent, color: "#ffffff" };
  } else if (active) {
    computed = { backgroundColor: tint(accent, 12), borderColor: accent, color: accent };
  } else {
    computed = {
      backgroundColor: "transparent",
      borderColor: variant === "ghost" ? "transparent" : "var(--border)",
      color: "var(--text-secondary)",
    };
  }

  return (
    <button
      className={`${base} ${SIZES[size]} ${mono ? "font-mono" : ""} ${className}`}
      style={{ ...computed, ...style }}
      {...rest}
    >
      {children}
    </button>
  );
}
