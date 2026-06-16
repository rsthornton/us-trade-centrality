import { useState } from "react";
import { Badge, Button, Card, Pill, SegmentedControl, Select, Slider, Tooltip } from "../components/ui";

/**
 * DEV-only component gallery. Rendered by App when
 * `import.meta.env.DEV && location.hash === "#/components"`.
 * Lets you eyeball every primitive in isolation without Storybook.
 */
export default function Gallery() {
  const [seg, setSeg] = useState<"both" | "in" | "out">("both");
  const [pill, setPill] = useState("eigenvector");
  const [sel, setSel] = useState("01");
  const [slide, setSlide] = useState(50);

  return (
    <div className="min-h-screen p-10" style={{ background: "var(--bg-primary)" }}>
      <h1 className="text-2xl font-light mb-8" style={{ color: "var(--text-primary)" }}>
        UI Primitives Gallery
      </h1>

      <Section title="Button">
        <Button variant="outline">Outline</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="solid">Solid</Button>
        <Button variant="outline" active>
          Active
        </Button>
        <Button variant="outline" mono size="sm">
          51×51 Domestic
        </Button>
        <Button variant="outline" disabled>
          Disabled
        </Button>
      </Section>

      <Section title="Pill">
        {[
          { key: "eigenvector", label: "Eigenvector", sub: "Trade prestige", color: "#44cc88" },
          { key: "betweenness", label: "Betweenness", sub: "Bridge position", color: "#4488ff" },
          { key: "out_degree", label: "Out-Degree", sub: "Export reach", color: "#ff9944" },
        ].map((m) => (
          <Pill
            key={m.key}
            active={pill === m.key}
            color={m.color}
            subtitle={m.sub}
            onClick={() => setPill(m.key)}
          >
            {m.label}
          </Pill>
        ))}
      </Section>

      <Section title="SegmentedControl">
        <SegmentedControl
          options={[
            { value: "both", label: "Both" },
            { value: "in", label: "Inbound" },
            { value: "out", label: "Outbound" },
          ]}
          value={seg}
          onChange={setSeg}
        />
      </Section>

      <Section title="Select">
        <Select
          value={sel}
          onChange={setSel}
          leadingOption={{ value: "all", label: "All Commodities" }}
          groups={[
            {
              label: "Agriculture & Food",
              options: [
                { value: "01", label: "01 — Live Animals and Fish" },
                { value: "02", label: "02 — Cereal Grains" },
              ],
            },
          ]}
        />
      </Section>

      <Section title="Slider">
        <Slider min={10} max={200} step={10} value={slide} onChange={setSlide} />
        <span className="font-mono text-sm" style={{ color: "var(--accent-blue)" }}>
          {slide}
        </span>
      </Section>

      <Section title="Card">
        <Card>
          <div className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Outbound
          </div>
          <div className="font-mono text-lg" style={{ color: "var(--text-primary)" }}>
            $78.4B
          </div>
        </Card>
        <Card surface="secondary">Secondary surface</Card>
      </Section>

      <Section title="Badge">
        <Badge tone="green">#1</Badge>
        <Badge tone="blue">#12</Badge>
        <Badge tone="neutral">#40</Badge>
        <Badge tone="red">#51</Badge>
      </Section>

      <Section title="Tooltip (anchored sample)">
        <div className="relative h-16 w-full">
          <Tooltip x={0} y={0} visible>
            <div className="font-semibold">Texas</div>
            <div style={{ color: "var(--text-secondary)" }}>GDP #2 → Net #5 (+3)</div>
          </Tooltip>
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <div
        className="text-xs uppercase tracking-wider mb-3 font-mono"
        style={{ color: "var(--text-muted)" }}
      >
        {title}
      </div>
      <div className="flex items-center gap-3 flex-wrap">{children}</div>
    </div>
  );
}
