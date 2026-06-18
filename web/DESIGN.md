# The Interstate Power Observatory — Design System

The public design contract for the web app. Read this before changing anything visual.
The `trade-observatory` Claude skill points here.

## Identity

**Product name:** The Interstate Power Observatory (matches the ResearchHub proposal title).
**Thesis:** GDP measures what a state produces; network centrality reveals the leverage it holds.
**Register:** editorial, analytical, credible. Light, warm, uncluttered. The map is the hero.

## Stack

React 19 + Vite 8 + TypeScript (strict) + Tailwind 4 (CSS-first `@theme`, no `tailwind.config.js`).
The choropleth map and flow arcs are **hand-rolled SVG with zero charting dependencies**
(`lib/geo.ts` Albers projection, `lib/topo.ts` TopoJSON decoder). This is deliberate — keep it.

## Tokens

Tokens live as CSS custom properties in `src/index.css` `:root` and are consumed in inline
styles via `var(--x)` (the dominant pattern here). A typed mirror in `src/tokens.ts` exists for
SVG presentation props and numeric props, where `var()` is not valid. **Change values in
`index.css` first**, then mirror into `tokens.ts` if JS needs them. Add new colors to `:root`
before using them in a component.

| Group | Tokens |
|---|---|
| Surface | `--bg-primary #f5f5fb` (faint indigo tint), `--bg-secondary #ffffff` (cards pop), `--bg-surface #ececf6` |
| Canvas stage | `--canvas-from #f6f5fd` → `--canvas-to #eeedf8` (gradient behind map + divergence panels) |
| Text | `--text-primary #1a1a2e`, `--text-secondary #4a4a6a`, `--text-muted #8888a8` |
| Accents | `--accent-blue #2266dd`, `--accent-green #1a9960`, `--accent-red #dd3344`, `--accent-orange #dd7722`, `--accent-purple #7744cc` |
| Borders | `--border #e4e1ec` (interactive elements), `--hairline #eeecf3` (faint dividers) |
| Map viz | `--map-selection #ffa94d`, `--map-dim #9ca3af`, `--map-empty #e8e8f0`, `--map-stroke #d0d0d8` |
| Radius | `--radius-sm 4`, `--radius-md 6`, `--radius-lg 8` (controls), `--radius-card 12` (cards/panels/drawer), `--radius-pill 9999` |
| Shadow | `--shadow-card`, `--shadow-card-hover`, `--shadow-drawer` |
| Z-index | `--z-drawer 10`, `--z-tooltip 20`, `--z-hint 30` |
| Motion | `--transition-fast 150ms`, `--transition-base 200ms`, `--transition-slow 300ms` |
| Fonts | `--font-sans` Inter, `--font-mono` JetBrains Mono (registered in `@theme`) |

**Data-viz palette** (`src/lib/colors.ts`): `VIRIDIS` (32-stop, perceptually uniform and
**colorblind-safe** — used for centrality choropleth), `PRGN` (17-stop divergence), and
`MEASURE_COLORS` (eigenvector `#44cc88`, betweenness `#4488ff`, out_degree `#ff9944`). Viridis
stays; do not swap it for a non-colorblind-safe ramp.

## UI primitives (`src/components/ui/`)

Composable, token-driven. Prefer these over new bespoke inline styles. View them live at
`#/components` (DEV only — `src/dev/Gallery.tsx`).

| Primitive | Props (key) | Notes |
|---|---|---|
| `Button` | `variant` ghost/outline/solid, `size` sm/md, `active`, `accent`, `mono` | toggle-style `active` tints with accent |
| `Pill` | `active`, `color`, `subtitle`, `onClick` | the centrality measure pills |
| `SegmentedControl<T>` | `options[]`, `value`, `onChange`, `accent` | direction toggle, commodity quick-picks |
| `Select` | `value`, `onChange`, `groups[]`, `leadingOption` | styled native select + custom chevron |
| `Slider` | `min`, `max`, `step`, `value`, `onChange` | styled range |
| `Card` | `surface` surface/secondary, `padded` | inset surface container |
| `Badge` | `tone` neutral/green/blue/red, `color`, `mono` | rank badges |
| `Tooltip` | `x`, `y`, `visible` | controlled floating box (map hover) |
| `tint(color, pct)` | — | translucent color helper (hex alpha or color-mix) |

## App components

- `App.tsx` — orchestrator: header/hero, control bar, map + drawer, legend, rankings, footer; owns all state and the `?state=&measure=` URL sync.
- `brand/Wordmark.tsx` — network-glyph mark + wordmark (shares measure colors with the viz).
- `Footer.tsx` — data attribution + Halcyonic Systems.
- `OrientationHint.tsx` — dismissible first-visit nudge (localStorage).
- `TradeMap.tsx` — **the hero**; zero-dep SVG choropleth + Bézier flow arcs + hover tooltip. Props: `geojson, centralities, measure, selectedState, onSelectState, edges, showEdges, flowDirection`. The viz color literals inside are the viz contract.
- `CentralityPills.tsx`, `CommodityFilter.tsx`, `ColorLegend.tsx` — controls.
- `drawer/` — `StateDossier` (horizontal detail panel below the stage) + `TradeCard`, `PartnersList`, `format.ts`.
- `rankings/` — `DivergenceView` (the Divergence canvas) + `DivergenceDumbbell` (GDP-rank → network-rank gap per state, the hero chart), `DivergenceTable` (full 51-state list behind "show all"), `constants.ts`.
- `hooks/useUrlState.ts` — deep-link read on mount + sync on change.

## Layout

Brand bar (wordmark + nav) → hero (eyebrow, title, dek, rotating finding) → then a **two-column
console**: a **left control rail** beside the **canvas stage**.
- **Left rail** (`lg:w-[300px]`): Map / Divergence view tabs, the vertical measure selector, the
  commodity filter, and (map view only) the network/flows toggles + top-N slider + direction.
- **Stage:** the selected view fills the rest — Map (choropleth + flow arcs + legend) or Divergence
  (the dumbbell + "show all 51 states" table). When a state is selected, a **horizontal
  `StateDossier` opens below the stage content** (the map shrinks slightly to fit), keeping the
  detail with the data instead of over it or in the rail.

Below the console: a persistent mono status bar (nodes/edges/density) → footer. On `< lg` the rail
collapses to a stacked column above the stage. The two views are peers, switched by the tab control
(App `view` state); they share the measure + commodity controls.

## Craft principles (the polish rules)

- **Quiet chrome, loud data, colored surfaces.** Controls stay near-monochrome (greys + one blue
  for links). The *data* (map ramp, divergence green/red) owns saturated color. *Surfaces* carry
  tasteful low-saturation tint: a tinted page + soft violet glow, and a lavender "canvas stage"
  gradient behind the map and divergence panels. Tint ≠ chrome noise; don't accent-fill controls.
- **The active measure's hue threads the UI.** The canvas stage's 2.5px top accent and the measure
  selector dot use the active measure's color (eigenvector green / betweenness blue / out-degree
  orange). Switching measures retints the stage.
- **Color earns its place by meaning.** The divergence dumbbell's faint green/red background bands
  reinforce the overperform/underperform split. Prefer meaningful color washes over decorative ones.
- **Surfaces and hairlines over outlines.** Prefer whitespace, a `--bg-surface` fill, or a soft
  shadow to group things. Reach for `--hairline` for dividers and `--border` only on interactive
  elements. Avoid wrapping every control in its own outline.
- **One segmented language.** The enclosed `SegmentedControl` (surface container, active segment
  lifts on `--bg-secondary` + `--shadow-card`) is the shared style for view tabs, the direction
  toggle, the commodity quick-picks, and the measure selector. Reuse it; don't invent new toggles.
- **Measure color = a dot, not a border.** The measure's color appears as a small dot tying it to
  the map ramp, never as a full pill tint/outline.
- **Centered frame.** Content sits in a centered `max-w-[1240px]` column, not edge-to-edge.
- **Radius:** controls `--radius-lg` (8), cards/panels/drawer `--radius-card` (12), pills full.

## Do / Don't

- **DO** keep the map zero-dependency SVG. No D3, no Mapbox.
- **DO** keep Viridis (colorblind-safe) for centrality, PRGn for divergence.
- **DO** default to light mode. It is the only mode; do not add a dark toggle without sign-off.
- **DO** add new colors to `index.css` `:root` first, then reference via `var()`.
- **DON'T** use em dashes in user-facing UI copy. Use commas, periods, or "to". (`strategy/writing-style-guide.md`.)
- **DON'T** change the JSON shapes in `public/data/` from the design side — see the data contract.
- **DON'T** introduce a CSS framework theme layer or component library; compose the primitives.

## Data contract

The app reads static JSON from `public/data/`, produced by `scripts/export_viz_data.py`. Types
are in `src/types.ts` (`CentralityRow`, `CommodityCentralityRow`, `Edge`, `NetworkStats`,
`Metadata`, `StateTotals`, `CoreData`). Note: the state panel's Outbound/Inbound and top partners
come from `state_trade_totals.json` (true totals from the full bilateral matrix), NOT from the
top-N flows drawn on the map — don't recompute trade volume from the visible `edges`. Presentation changes never touch data shape. To change a field you change
the export script, the consuming component, and `src/types.ts` together.

## Verify

`npm run typecheck && npm run lint && npm run build`, then screenshot the preview at desktop
(1440) and mobile (390). Frozen pipeline note: never touch `../evolution/` — it is a registered
pre-registration artifact.
