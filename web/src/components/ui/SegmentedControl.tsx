export interface SegmentOption<T extends string> {
  value: T;
  label: string;
}

export interface SegmentedControlProps<T extends string> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  size?: "sm" | "md" | "lg";
}

const SIZES = {
  sm: "px-2.5 py-1 text-xs",
  md: "px-3 py-1.5 text-xs",
  lg: "px-4 py-1.5 text-sm",
} as const;

/**
 * Enclosed segmented control: one calm container, the active segment lifts on a
 * surface with a soft shadow. The single shared style for the view tabs, the
 * flow-direction toggle, and the commodity quick-picks.
 */
export default function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  size = "md",
}: SegmentedControlProps<T>) {
  return (
    <div
      className="inline-flex gap-0.5 p-0.5 rounded-lg"
      style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--hairline)" }}
    >
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`${SIZES[size]} rounded-md font-medium cursor-pointer transition-all duration-200`}
            style={{
              backgroundColor: active ? "var(--bg-secondary)" : "transparent",
              color: active ? "var(--text-primary)" : "var(--text-secondary)",
              boxShadow: active ? "var(--shadow-card)" : "none",
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
