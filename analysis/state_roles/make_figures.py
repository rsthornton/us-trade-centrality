"""
Figures for the state role taxonomy, drawn from output/state_roles.json.

  gap-undervalued      places above GDP rank, 2012-2022, for the thesis's
                       eight structurally undervalued states
  periodic-table-2017  one tile per state, grouped by 2017 role
  tile-map-decade      tile-grid map coloured by decade role
  role-stability       role per state in each survey year

Writes PNG and SVG to figures/.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
DATA = json.loads((HERE / "output" / "state_roles.json").read_text())
STATES = {s["state"]: s for s in DATA["states"]}
YEARS = ["2012", "2017", "2022"]

ORDER = ["Engine", "Sustainer", "Router", "Generalist", "Specialist", "Market"]
LABEL = {r: r + "s" for r in ORDER}
FILL = {
    "Engine": "#23262f",
    "Sustainer": "#9a4a12",
    "Router": "#1f5f7a",
    "Generalist": "#e6e3dc",
    "Specialist": "#55661f",
    "Market": "#e3b04b",
}
INK = {r: ("#1a1a1a" if r in ("Generalist", "Market") else "#ffffff") for r in ORDER}
GROUND, TEXT, MUTED, RULE = "#fafaf8", "#141414", "#5a5a5a", "#d8d6d0"

SHORT = {
    "Coal and Petroleum Products, n.e.c.": "Petroleum prod.",
    "Transportation Equipment, n.e.c.": "Transport equip.",
    "Gravel and Crushed Stone": "Gravel",
    "Live Animals and Fish": "Livestock",
    "Pharmaceutical Products": "Pharma",
    "Nonmetallic Mineral Products": "Mineral prod.",
    "Nonmetallic Minerals": "Minerals",
    "Motorized and Other Vehicles": "Vehicles",
    "Motorized Vehicles": "Vehicles",
    "Alcoholic Beverages": "Beverages",
    "Natural Sands": "Sand",
    "Logs and Wood": "Timber",
    "Milled Grain Products": "Milled grain",
    "Articles of Base Metal": "Metal goods",
    "Textiles/Leather": "Textiles",
    "Meat/Seafood": "Meat",
    "Cereal Grains": "Grain",
    "Tobacco Products": "Tobacco",
    "Transportation Equipment": "Transport equip.",
    "Coal and Petroleum Products": "Petroleum prod.",
    "Building Stone": "Stone",
    "Basic Chemicals": "Chemicals",
    "Wood Products": "Wood products",
    "Animal Feed": "Animal feed",
    "Fertilizers": "Fertilizer",
    "Metallic Ores": "Metal ores",
    "Fuel Oils": "Fuel oils",
}

TILE_POS = {
    "AK": (1, 1),
    "ME": (11, 1),
    "WI": (6, 2),
    "VT": (10, 2),
    "NH": (11, 2),
    "WA": (1, 3),
    "ID": (2, 3),
    "MT": (3, 3),
    "ND": (4, 3),
    "MN": (5, 3),
    "IL": (6, 3),
    "MI": (7, 3),
    "NY": (9, 3),
    "MA": (10, 3),
    "OR": (1, 4),
    "NV": (2, 4),
    "WY": (3, 4),
    "SD": (4, 4),
    "IA": (5, 4),
    "IN": (6, 4),
    "OH": (7, 4),
    "PA": (8, 4),
    "NJ": (9, 4),
    "CT": (10, 4),
    "RI": (11, 4),
    "CA": (1, 5),
    "UT": (2, 5),
    "CO": (3, 5),
    "NE": (4, 5),
    "MO": (5, 5),
    "KY": (6, 5),
    "WV": (7, 5),
    "VA": (8, 5),
    "MD": (9, 5),
    "DE": (10, 5),
    "AZ": (2, 6),
    "NM": (3, 6),
    "KS": (4, 6),
    "AR": (5, 6),
    "TN": (6, 6),
    "NC": (7, 6),
    "SC": (8, 6),
    "DC": (9, 6),
    "OK": (4, 7),
    "LA": (5, 7),
    "MS": (6, 7),
    "AL": (7, 7),
    "GA": (8, 7),
    "HI": (1, 8),
    "TX": (4, 8),
    "FL": (9, 8),
}

plt.rcParams.update(
    {
        "font.family": ["IBM Plex Sans", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "figure.facecolor": GROUND,
        "axes.facecolor": GROUND,
        "savefig.facecolor": GROUND,
        "text.color": TEXT,
        "axes.labelcolor": MUTED,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "svg.fonttype": "none",
    }
)


def short(name):
    if not name:
        return ""
    return SHORT.get(name, name if len(name) <= 13 else name[:12] + ".")


def save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=200, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


CODE = {
    "Engine": "En",
    "Sustainer": "Su",
    "Router": "Ro",
    "Generalist": "Ge",
    "Specialist": "Sp",
    "Market": "Ma",
}


def title(ax, text, sub, gap=0.0):
    ax.text(
        0.0,
        1.0 + gap + 0.07,
        text,
        fontsize=17,
        weight="bold",
        ha="left",
        va="bottom",
        transform=ax.transAxes,
    )
    ax.text(
        0.0,
        1.0 + gap + 0.025,
        sub,
        fontsize=10.5,
        color=MUTED,
        ha="left",
        va="bottom",
        transform=ax.transAxes,
    )


def gap_undervalued():
    eight = ["KY", "MS", "IN", "LA", "TN", "MI", "MT", "SC"]
    durable = {"KY", "MS", "IN", "LA", "TN", "MI"}
    fig, ax = plt.subplots(figsize=(8, 5.2))
    xs = [0, 1, 2]
    ax.axhspan(-2, 5, color="#efede8", zorder=0)
    ax.axhline(5, color=MUTED, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.text(-0.1, 4.55, "threshold: 5 places", va="top", fontsize=8.5, color=MUTED)
    ends = []
    for s in eight:
        ys = [STATES[s]["years"][y]["places_above_gdp"] for y in YEARS]
        color = FILL["Sustainer"] if s in durable else "#9a9890"
        ax.plot(xs, ys, color=color, lw=2.2 if s in durable else 1.6, marker="o", ms=5, zorder=3)
        ends.append([ys[-1], s, color])
    ends.sort()
    for i in range(1, len(ends)):
        if ends[i][0] - ends[i - 1][0] < 0.9:
            ends[i][0] = ends[i - 1][0] + 0.9
    for y_end, s, color in ends:
        ax.text(2.12, y_end, s, va="center", fontsize=10, weight="bold", color=color)
    ax.set_xticks(xs, YEARS)
    ax.set_xlim(-0.15, 2.6)
    ax.set_ylim(-1, 16)
    ax.set_ylabel("Network rank minus GDP rank (places)")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(RULE)
    ax.spines["bottom"].set_color(RULE)
    title(
        ax,
        "Structural undervaluation is durable for six of eight states",
        "Places a state ranks higher in the interstate network than in GDP, by survey year",
    )
    ax.text(
        -0.12,
        -0.12,
        "Source: CFS 2012, 2017, 2022 (SCTG 16 excluded); BEA state GDP. "
        "Eigenvector rank vs GDP rank.",
        fontsize=8,
        color=MUTED,
        transform=ax.transAxes,
    )
    save(fig, "gap-undervalued")


def tile(ax, x, y, w, h, s, role, top_left, top_right, bottom, faded=False):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0,rounding_size=0.04",
            fc=FILL[role],
            ec="none",
            alpha=0.55 if faded else 1,
        )
    )
    ink = INK[role]
    ax.text(x + 0.07, y + h - 0.1, top_left, fontsize=6.5, color=ink, va="top", family="monospace")
    ax.text(
        x + w - 0.07,
        y + h - 0.1,
        top_right,
        fontsize=6.5,
        color=ink,
        va="top",
        ha="right",
        family="monospace",
    )
    ax.text(x + 0.07, y + h * 0.5, s, fontsize=15, weight="bold", color=ink, va="center")
    ax.text(x + 0.07, y + 0.1, bottom, fontsize=5.6, color=ink, va="bottom")


def periodic_table():
    year = "2017"
    cols = {"Engine": 1, "Sustainer": 2, "Router": 1, "Generalist": 3, "Specialist": 1, "Market": 2}
    groups = {
        r: sorted(
            [s for s in STATES if STATES[s]["years"][year]["role"] == r],
            key=lambda s: STATES[s]["years"][year]["rank_eigenvector"],
        )
        for r in ORDER
    }
    w, h, gap, group_gap = 1.0, 1.05, 0.1, 0.45
    fig, ax = plt.subplots(figsize=(14, 8.4))
    x0 = 0.0
    for r in ORDER:
        n = cols[r]
        ax.add_patch(Rectangle((x0, 0.25), n * w + (n - 1) * gap, 0.06, fc=FILL[r], ec="none"))
        ax.text(x0, 0.75, LABEL[r], fontsize=11, weight="bold", va="bottom")
        ax.text(x0, 0.42, f"{len(groups[r])} states", fontsize=8.5, color=MUTED, va="bottom")
        for i, s in enumerate(groups[r]):
            e = STATES[s]["years"][year]
            cx = x0 + (i % n) * (w + gap)
            cy = -((i // n) + 1) * (h + gap)
            g = e["places_above_gdp"]
            tile(
                ax,
                cx,
                cy,
                w,
                h,
                s,
                r,
                str(e["rank_eigenvector"]),
                (f"+{g}" if g > 0 else (f"−{abs(g)}" if g < 0 else "·")),
                short(e["signature"]),
            )
        x0 += n * w + (n - 1) * gap + group_gap
    ax.set_xlim(-0.1, x0)
    ax.set_ylim(-7 * (h + gap) - 0.1, 1.3)
    ax.set_aspect("equal")
    ax.axis("off")
    title(
        ax,
        "A periodic table of state power, 2017",
        "Each tile: network rank (top left), places above GDP rank (top right), "
        "signature commodity",
    )
    save(fig, "periodic-table-2017")


def tile_map():
    fig, ax = plt.subplots(figsize=(11, 7.6))
    w, h = 0.94, 0.94
    for s, (c, r) in TILE_POS.items():
        d = STATES[s]["decade"]
        role = d["role"]
        x, y = c - 1, -(r - 1)
        consistent = d["consistent"]
        ax.add_patch(
            FancyBboxPatch(
                (x, y - h),
                w,
                h,
                boxstyle="round,pad=0,rounding_size=0.04",
                fc=FILL[role],
                ec="none",
            )
        )
        if not consistent:
            ax.add_patch(
                Rectangle(
                    (x + 0.05, y - h + 0.05),
                    w - 0.1,
                    h - 0.1,
                    fc="none",
                    ec=INK[role],
                    lw=1,
                    ls=(0, (2, 2)),
                    alpha=0.8,
                )
            )
        ink = INK[role]
        ax.text(x + 0.08, y - 0.12, s, fontsize=13, weight="bold", color=ink, va="top")
        roles_by_year = [CODE[STATES[s]["years"][yy]["role"]] for yy in YEARS]
        ax.text(
            x + 0.1,
            y - h + 0.12,
            " ".join(roles_by_year),
            fontsize=6.5,
            color=ink,
            va="bottom",
            family="monospace",
        )
    for i, r in enumerate(ORDER):
        ax.add_patch(Rectangle((i * 1.9, -8.6), 0.3, 0.3, fc=FILL[r], ec=RULE, lw=0.5))
        ax.text(i * 1.9 + 0.42, -8.45, LABEL[r], fontsize=9.5, va="center")
    ax.text(
        0,
        -9.15,
        "Codes give the role in 2012, 2017, 2022 (En Su Ro Ge Sp Ma). "
        "Dashed outline: role changed during the decade.",
        fontsize=8.5,
        color=MUTED,
    )
    ax.set_xlim(-0.1, 11.1)
    ax.set_ylim(-9.4, 0.1)
    ax.set_aspect("equal")
    ax.axis("off")
    title(
        ax,
        "How each state powers the interstate network, 2012-2022",
        "Decade role: the role a state held most often across the three survey years",
    )
    save(fig, "tile-map-decade")


def role_stability():
    order = sorted(
        STATES,
        key=lambda s: (
            ORDER.index(STATES[s]["decade"]["role"]),
            STATES[s]["years"]["2017"]["rank_eigenvector"],
        ),
    )
    fig, ax = plt.subplots(figsize=(6.2, 13))
    for i, s in enumerate(order):
        y = -i
        for j, yy in enumerate(YEARS):
            role = STATES[s]["years"][yy]["role"]
            ax.add_patch(Rectangle((j, y - 0.9), 0.94, 0.86, fc=FILL[role], ec="none"))
        ax.text(-0.15, y - 0.47, s, ha="right", va="center", fontsize=8.5, weight="bold")
        ax.text(
            3.05,
            y - 0.47,
            STATES[s]["decade"]["role"] if STATES[s]["decade"]["consistent"] else "",
            va="center",
            fontsize=7.5,
            color=MUTED,
        )
    for j, yy in enumerate(YEARS):
        ax.text(j + 0.47, 0.35, yy, ha="center", fontsize=9.5, color=MUTED)
    for i, r in enumerate(ORDER):
        x, y = (i % 3) * 1.6 - 0.6, -len(order) - 1.2 - (i // 3) * 0.8
        ax.add_patch(Rectangle((x, y), 0.3, 0.5, fc=FILL[r], ec=RULE, lw=0.5))
        ax.text(x + 0.4, y + 0.25, LABEL[r], fontsize=8.5, va="center")
    ax.set_xlim(-0.8, 4.2)
    ax.set_ylim(-len(order) - 3.0, 0.9)
    ax.axis("off")
    title(
        ax,
        "Role by survey year",
        "Sorted by decade role; right-hand label marks states with the same role "
        "in all three years",
        gap=0.005,
    )
    save(fig, "role-stability")


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    gap_undervalued()
    periodic_table()
    tile_map()
    role_stability()
