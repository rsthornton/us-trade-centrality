import type { CSSProperties, ReactNode } from "react";

export interface CardProps {
  children: ReactNode;
  className?: string;
  /** Surface background; defaults to the inset surface token. */
  surface?: "surface" | "secondary";
  padded?: boolean;
  style?: CSSProperties;
}

export default function Card({
  children,
  className = "",
  surface = "surface",
  padded = true,
  style,
}: CardProps) {
  const bg = surface === "secondary" ? "var(--bg-secondary)" : "var(--bg-surface)";
  return (
    <div
      className={`rounded-lg ${padded ? "p-3" : ""} ${className}`}
      style={{ backgroundColor: bg, ...style }}
    >
      {children}
    </div>
  );
}
