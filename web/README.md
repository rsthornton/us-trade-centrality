# US Interstate Trade Centrality — Web Dashboard

React + Vite + Tailwind frontend replacing the Plotly Dash app at us-trade.plotly.app.

## Stack

- React 19 + Vite 8 + Tailwind 4 (mirrors gov-graphs)
- Custom SVG Albers USA projection (no D3)
- Static JSON data (no runtime server)

## Quick Start

```bash
cd web
npm install
npm run dev        # → localhost:5180
```

## Data Pipeline

All data is pre-computed by the Python toolkit. To regenerate JSON from CSVs:

```bash
cd ..
source .venv/bin/activate
python scripts/export_viz_data.py
```

Output lands in `web/public/data/`. The React app fetches these at runtime.

## Architecture

```
web/
├── public/data/          # Static JSON (centralities, edges, coords, metadata)
├── src/
│   ├── App.jsx           # Top-level state: measure, selected state, network type
│   ├── components/
│   │   ├── TradeMap.jsx       # Custom SVG choropleth (Albers USA projection)
│   │   ├── CentralityPills.jsx # Eigenvector / Betweenness / Out-Degree toggle
│   │   ├── StateDrawer.jsx    # Right-panel state detail on click
│   │   └── ColorLegend.jsx    # Viridis gradient bar
│   ├── data/loader.js    # Fetch + cache JSON
│   └── lib/
│       ├── geo.js         # Albers USA projection (pure math, ~80 lines)
│       ├── topo.js        # TopoJSON → GeoJSON decoder (no npm dep)
│       └── colors.js      # Viridis + PRGn color scales
└── package.json
```

## Status

Phase 0 complete (scaffold + first render). Phase 1 (interactions, polish, deploy) is post-trip.
