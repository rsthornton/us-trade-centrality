import { formatDollars, type Partner } from "./format";

export interface PartnersListProps {
  title: string;
  partners: Partner[];
}

/** Ranked list of a state's top trade partners (inbound or outbound). */
export default function PartnersList({ title, partners }: PartnersListProps) {
  if (partners.length === 0) return null;
  return (
    <div className="mt-4">
      <div className="text-xs uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
        {title}
      </div>
      <div className="rounded-lg overflow-hidden" style={{ border: "1px solid var(--border)" }}>
        {partners.map((p, i) => (
          <div
            key={p.partner}
            className="flex items-center justify-between px-3 py-2"
            style={{
              backgroundColor: i % 2 === 0 ? "var(--bg-surface)" : "var(--bg-secondary)",
              borderTop: i > 0 ? "1px solid var(--border)" : "none",
            }}
          >
            <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
              <span
                className="text-xs w-4 text-right flex-shrink-0"
                style={{ color: "var(--text-muted)" }}
              >
                {i + 1}
              </span>
              <span className="text-sm truncate" style={{ color: "var(--text-primary)" }}>
                {p.partner}
              </span>
            </div>
            <span
              className="font-mono text-sm flex-shrink-0"
              style={{ color: "var(--text-secondary)" }}
            >
              {formatDollars(p.weight)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
