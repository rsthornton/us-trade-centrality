import { MEASURE_COLORS } from "../../lib/colors";

export interface WordmarkProps {
  /** Render only the network glyph (no text). */
  iconOnly?: boolean;
  size?: number;
}

/**
 * Text-based wordmark for the Interstate Power Observatory.
 * The glyph is a tiny three-node trade network drawn in the measure colors,
 * so the brand mark and the data viz share one visual language. No image asset.
 */
export default function Wordmark({ iconOnly = false, size = 22 }: WordmarkProps) {
  return (
    <span className="inline-flex items-center gap-2 select-none">
      <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
        <line x1="5" y1="17" x2="12" y2="6" stroke="var(--map-stroke)" strokeWidth="1.3" />
        <line x1="12" y1="6" x2="19" y2="15" stroke="var(--map-stroke)" strokeWidth="1.3" />
        <line x1="5" y1="17" x2="19" y2="15" stroke="var(--map-stroke)" strokeWidth="1.3" />
        <circle cx="12" cy="6" r="3" fill={MEASURE_COLORS.eigenvector} />
        <circle cx="5" cy="17" r="2.4" fill={MEASURE_COLORS.betweenness} />
        <circle cx="19" cy="15" r="2.4" fill={MEASURE_COLORS.out_degree} />
      </svg>
      {!iconOnly && (
        <span
          className="font-semibold tracking-tight text-sm whitespace-nowrap"
          style={{ color: "var(--text-primary)" }}
        >
          Interstate Power Observatory
        </span>
      )}
    </span>
  );
}
