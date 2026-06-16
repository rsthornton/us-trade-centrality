import type { ReactNode } from "react";
import { tint } from "./style";

export interface PillProps {
  active?: boolean;
  /** Accent color when active (hex or CSS var). */
  color?: string;
  /** Small label rendered above the main content. */
  subtitle?: string;
  onClick?: () => void;
  children: ReactNode;
}

export default function Pill({
  active = false,
  color = "var(--accent-blue)",
  subtitle,
  onClick,
  children,
}: PillProps) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer border"
      style={{
        backgroundColor: active ? tint(color, 13) : "transparent",
        borderColor: active ? color : "var(--border)",
        color: active ? color : "var(--text-secondary)",
      }}
    >
      {subtitle && <span className="block text-xs opacity-60">{subtitle}</span>}
      {children}
    </button>
  );
}
