import type { ReactNode } from "react";
import { zIndex } from "../../tokens";

export interface TooltipProps {
  /** Viewport-relative position (px). */
  x: number;
  y: number;
  visible: boolean;
  children: ReactNode;
}

/**
 * A controlled floating tooltip. The caller tracks pointer position and
 * visibility (used for the SVG map, where native title tooltips are the
 * accessible fallback). Rendered fixed and pointer-transparent.
 */
export default function Tooltip({ x, y, visible, children }: TooltipProps) {
  if (!visible) return null;
  return (
    <div
      className="fixed pointer-events-none rounded-md px-2.5 py-1.5 text-xs shadow-lg"
      style={{
        left: x + 12,
        top: y + 12,
        zIndex: zIndex.tooltip,
        backgroundColor: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        color: "var(--text-primary)",
        boxShadow: "var(--shadow-card)",
        maxWidth: 220,
      }}
    >
      {children}
    </div>
  );
}
