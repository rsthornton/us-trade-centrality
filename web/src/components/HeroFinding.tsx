import { useMemo, useState, useEffect } from "react";
import type { CentralityRow, Measure } from "../types";

const PLAIN: Record<Measure, string> = {
  betweenness: "bridge position",
  eigenvector: "trade prestige",
  out_degree: "export reach",
};

interface HeroFindingProps {
  centralities: CentralityRow[];
}

/** A rotating, data-driven line that proves the thesis on landing: real states
 *  whose network rank diverges sharply from their GDP rank. */
export default function HeroFinding({ centralities }: HeroFindingProps) {
  const findings = useMemo(() => {
    if (!centralities.length) return [];
    const out: string[] = [];
    const measures: Measure[] = ["betweenness", "eigenvector", "out_degree"];
    for (const m of measures) {
      const rk = `rank_${m}` as const;
      const rows = centralities.map((r) => ({
        name: r.state_name,
        gdp: r.gdp_rank,
        net: r[rk],
        d: r.gdp_rank - r[rk],
      }));
      const over = rows.reduce((a, b) => (b.d > a.d ? b : a));
      const under = rows.reduce((a, b) => (b.d < a.d ? b : a));
      if (over.d >= 5) {
        out.push(`${over.name} ranks #${over.gdp} by GDP but #${over.net} in ${PLAIN[m]}.`);
      }
      if (under.d <= -5) {
        out.push(`${under.name} ranks #${under.gdp} by GDP but only #${under.net} in ${PLAIN[m]}.`);
      }
    }
    return out;
  }, [centralities]);

  const [i, setI] = useState(0);
  useEffect(() => {
    if (findings.length < 2) return;
    const t = setInterval(() => setI((p) => (p + 1) % findings.length), 5000);
    return () => clearInterval(t);
  }, [findings.length]);

  if (!findings.length) return null;

  return (
    <div className="mt-3 text-sm min-h-5" style={{ color: "var(--text-secondary)" }}>
      <span key={i} style={{ animation: "ipo-finding-in 0.6s ease", display: "inline-block" }}>
        <span className="font-mono text-xs mr-2" style={{ color: "var(--accent-purple)" }}>
          FINDING
        </span>
        {findings[i % findings.length]}
      </span>
    </div>
  );
}
