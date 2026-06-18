export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectGroup {
  label: string;
  options: SelectOption[];
}

export interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  groups: SelectGroup[];
  /** A leading ungrouped option (e.g. "All"). */
  leadingOption?: SelectOption;
  className?: string;
}

/**
 * A styled wrapper over a native <select> — keeps native keyboard/a11y behavior
 * while matching the observatory's control aesthetic (custom chevron, tokens).
 */
export default function Select({
  value,
  onChange,
  groups,
  leadingOption,
  className = "",
}: SelectProps) {
  return (
    <div className={`relative inline-flex items-center ${className}`}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none text-xs rounded border pl-2.5 pr-7 py-1.5 cursor-pointer min-w-[180px]"
        style={{
          backgroundColor: "var(--bg-surface)",
          borderColor: "var(--border)",
          color: "var(--text-primary)",
          outline: "none",
        }}
      >
        {leadingOption && <option value={leadingOption.value}>{leadingOption.label}</option>}
        {groups.map((group) => (
          <optgroup key={group.label} label={group.label}>
            {group.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      <span
        className="pointer-events-none absolute right-2 text-[10px]"
        style={{ color: "var(--text-muted)" }}
      >
        ▼
      </span>
    </div>
  );
}
