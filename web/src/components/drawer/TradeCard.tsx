import Card from "../ui/Card";
import { formatDollars } from "./format";
import { useCountUp } from "../../hooks/useCountUp";

export interface TradeCardProps {
  label: string;
  value: number;
}

/** A single trade-volume figure (inbound or outbound) in a surface card. */
export default function TradeCard({ label, value }: TradeCardProps) {
  const animated = useCountUp(value);
  return (
    <Card surface="secondary">
      <div className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--text-muted)" }}>
        {label}
      </div>
      <div className="font-mono text-lg tabular-nums" style={{ color: "var(--text-primary)" }}>
        {formatDollars(animated)}
      </div>
    </Card>
  );
}
