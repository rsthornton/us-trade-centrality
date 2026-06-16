export interface SliderProps {
  min: number;
  max: number;
  step?: number;
  value: number;
  onChange: (value: number) => void;
  width?: number;
}

export default function Slider({ min, max, step = 1, value, onChange, width = 140 }: SliderProps) {
  return (
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      className="cursor-pointer"
      style={{ accentColor: "var(--accent-blue)", width }}
    />
  );
}
