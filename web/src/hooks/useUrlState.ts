import { useEffect } from "react";
import type { Measure } from "../types";

const MEASURES: readonly string[] = ["betweenness", "eigenvector", "out_degree"];

/** Read the initial state/measure from the URL query (?state=TX&measure=betweenness). */
export function readInitialUrlState(): { state: string | null; measure: Measure | null } {
  if (typeof window === "undefined") return { state: null, measure: null };
  const params = new URLSearchParams(window.location.search);
  const state = params.get("state");
  const m = params.get("measure");
  const measure = m && MEASURES.includes(m) ? (m as Measure) : null;
  return { state: state || null, measure };
}

/** Keep the URL query in sync with the selected state + measure (shareable links). */
export function useSyncUrlState(state: string | null, measure: Measure): void {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (state) params.set("state", state);
    else params.delete("state");
    params.set("measure", measure);
    const qs = params.toString();
    const url = `${window.location.pathname}${qs ? `?${qs}` : ""}${window.location.hash}`;
    window.history.replaceState(null, "", url);
  }, [state, measure]);
}
