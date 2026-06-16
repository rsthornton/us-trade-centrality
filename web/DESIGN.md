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
| Surface | `--bg-primary #fafafa`, `--bg-secondary #ffffff`, `--bg-surface #f0f0f5` |
| Text | `--text-primary #1a1a2e`, `--text-secondary #4a4a6a`, `--text-muted #8888a8` |
| Accents | `--accent-blue #2266dd`, `--accent-green #1a9960`, `--accent-red #dd3344`, `--accent-orange #dd7722`, `--accent-purple #7744cc`, `--border #d8d8e8` |
| Map viz | `--map-selection #ffa94d`, `--map-dim #9ca3af`, `--map-empty #e8e8f0`, `--map-stroke #d0d0d8` |
| Radius | `--radius-sm 4`, `--radius-md 6`, `--radius-lg 8`, `--radius-button 24`, `--radius-pill 9999` |
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
- `drawer/` — `StateDrawer` + `TradeCard`, `MeasureCard`, `PartnersList`, `format.ts`.
- `rankings/` — `RankingsTable` + `DivergenceScatter`, `DivergenceTable`, `constants.ts`.
- `hooks/useUrlState.ts` — deep-link read on mount + sync on change.

## Layout

Brand bar (wordmark + nav) → hero (eyebrow, title, dek) → control bar (pills, commodity, network/flows) → flow controls (top-N, direction) → map + state drawer → legend + network stats → rankings (collapsible) → footer.

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
`Metadata`, `CoreData`). Presentation changes never touch data shape. To change a field you change
the export script, the consuming component, and `src/types.ts` together.

## Verify

`npm run typecheck && npm run lint && npm run build`, then screenshot the preview at desktop
(1440) and mobile (390). Frozen pipeline note: never touch `../evolution/` — it is a registered
pre-registration artifact.
