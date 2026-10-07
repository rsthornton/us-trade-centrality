import type { ReactNode } from "react";

const STUDY_URL =
  "https://github.com/rsthornton/us-trade-centrality/blob/main/evolution/results/evolution_20260808_093628/report.md";

interface ClaimProps {
  index: string;
  title: string;
  children: ReactNode;
}

function Claim({ index, title, children }: ClaimProps) {
  return (
    <div className="pt-3" style={{ borderTop: "1px solid var(--border)" }}>
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-[11px]" style={{ color: "var(--text-muted)" }}>
          {index}
        </span>
        <h2
          className="font-serif text-[19px] font-semibold leading-snug"
          style={{ color: "var(--text-primary)" }}
        >
          {title}
        </h2>
      </div>
      <div className="mt-1.5 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
        {children}
      </div>
    </div>
  );
}

/** The three points the site makes, stated once. The first is computed from
 *  the data for the active measure (passed as children). */
export default function ClaimStrip({ children }: { children: ReactNode }) {
  return (
    <div className="mt-6 grid gap-5 lg:grid-cols-3">
      <Claim index="01" title="Position is not size">
        {children}
      </Claim>
      <Claim index="02" title="The structure holds">
        In a pre-registered test on the 2012, 2017 and 2022 surveys, prestige and export reach
        rankings held (rank correlation 0.98 or higher). Bridge rankings moved more.{" "}
        <a
          href={STUDY_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium hover:opacity-70"
          style={{ color: "var(--accent-blue)" }}
        >
          Study results
        </a>
      </Claim>
      <Claim index="03" title="Six ways to matter">
        Engines, Sustainers, Routers, Specialists, Markets and Generalists: a view of the
        different roles states play is in progress.
      </Claim>
    </div>
  );
}
