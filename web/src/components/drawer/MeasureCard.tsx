import Card from "../ui/Card";
import Badge from "../ui/Badge";

function rankColor(rank: number, total = 51): string {
  const pct = rank / total;
  return pct <= 0.2
    ? "var(--accent-green)"
    : pct <= 0.5
      ? "var(--accent-blue)"
      : "var(--text-muted)";
}

export interface MeasureCardProps {
  label: string;
  /** Pre-formatted value string (dollars or centrality score). */
  value: string;
  rank: number;
  /** Optional color for the value text (used for measure accents). */
  valueColor?: string;
}

export default function MeasureCard({ label, value, rank, valueColor }: MeasureCardProps) {
  return (
    <Card>
      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--text-muted)" }}>
        {label}
      </div>
      <div className="flex justify-between items-center">
        <span className="font-mono text-lg" style={{ color: valueColor ?? "var(--text-primary)" }}>
          {value}
        </span>
        <Badge color={rankColor(rank)}>#{rank}</Badge>
      </div>
    </Card>
  );
}
