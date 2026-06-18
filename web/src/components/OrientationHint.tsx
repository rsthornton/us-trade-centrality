import { useState } from "react";
import { zIndex } from "../tokens";

const STORAGE_KEY = "ipo-hint-dismissed";

/** First-visit nudge over the map. Dismissible and remembered via localStorage. */
export default function OrientationHint() {
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });

  if (dismissed) return null;

  const dismiss = () => {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // ignore storage failures (private mode, etc.)
    }
    setDismissed(true);
  };

  return (
    <div
      className="absolute left-1/2 -translate-x-1/2 top-3 flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs shadow-sm"
      style={{
        zIndex: zIndex.hint,
        backgroundColor: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        color: "var(--text-secondary)",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <span>Click a state to explore its trade power</span>
      <button
        onClick={dismiss}
        aria-label="Dismiss"
        className="cursor-pointer leading-none"
        style={{ color: "var(--text-muted)" }}
      >
        ✕
      </button>
    </div>
  );
}
