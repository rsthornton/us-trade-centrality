import { tint } from "./style";

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
}

export interface SegmentedControlProps<T extends string> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  /** Accent color for the active segment (hex or CSS var). */
  accent?: string;
  size?: "sm" | "md";
}

const SIZES = {
  sm: "px-2 py-1 text-xs",
  md: "px-2.5 py-1 text-xs",
} as const;

export default function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  accent = "var(--accent-blue)",
  size = "md",
}: SegmentedControlProps<T>) {
  return (
    <div className="flex items-center gap-1.5">
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`${SIZES[size]} rounded font-medium cursor-pointer border transition-all duration-200`}
            style={{
              backgroundColor: active ? tint(accent, 12) : "transparent",
              borderColor: active ? accent : "var(--border)",
              color: active ? accent : "var(--text-secondary)",
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
