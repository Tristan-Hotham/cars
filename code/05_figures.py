"""Step 5. Static figures for the paper (release/paper/fig_*.png) and blog (release/blog/b_*.png), and header.png.
Maps are drawn from the project's own polygons (British National Grid), no web tiles.
Run: python3 code/05_figures.py
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, Patch
from shapely.geometry import shape
from common import DATA, WORK, ROOT

FD = "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/"
HAVE = os.path.exists(FD + "FrauncesVar.ttf")
if HAVE:
    for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
        fm.fontManager.addfont(FD + f)
    DISP = fm.FontProperties(fname=FD + "FrauncesVar.ttf", weight=900); MONO = "IBM Plex Mono"; SER = "Source Serif 4"
else:
    DISP = fm.FontProperties(family="serif", weight="bold"); MONO = "monospace"; SER = "serif"
BG, FG, MUT, NA = "#F5F2EB", "#1C1B1F", "#625D66", "#D9D3C7"
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 200})

R = json.load(open(os.path.join(DATA, "results.json")))
U = json.load(open(os.path.join(DATA, "units.json")))
G = json.load(open(os.path.join(WORK, "geo_bng.json")))
MAKEPAL = {"FORD": "#1F4E9C", "VAUXHALL": "#C8322B", "VOLKSWAGEN": "#2C9C9C", "TOYOTA": "#E08A1E", "MERCEDES-BENZ": "#5D5A6E", "NISSAN": "#8E3E8F"}
CH = U["colour_hex"]
PAP = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAP, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
SEQ = {"green": ["#E8F1DE", "#B5D9A3", "#6DB37E", "#2E7D4F", "#11492C"], "grey": ["#EFEDE8", "#CFCAC0", "#A59E92", "#746D63", "#45403A"]}


def polys(geom):
    g = shape(geom)
    return list(g.geoms) if g.geom_type == "MultiPolygon" else [g]


def draw(ax, kind, colour_of, edge="white", lw=.35):
    for k, geom in G[kind].items():
        c = colour_of(k)
        for p in polys(geom):
            ec = "#8a8578" if c in ("#f4f4f2", "#efe6cc", "#c3c7cc") else edge
            ax.add_patch(MPoly(np.asarray(p.exterior.coords), closed=True, fc=c or NA, ec=ec, lw=lw, hatch=None if c else "////" if False else None))
    ax.set_xlim(-10000, 670000); ax.set_ylim(0, 1230000); ax.set_aspect("equal"); ax.axis("off")


LONDON = (503000, 563000, 152000, 202000)


def frame(size):
    fig = plt.figure(figsize=size)
    w, h = size; mw = min(0.6, (h * 0.97 * 680 / 1230) / w)
    ax = fig.add_axes([0.0, 0.015, mw, 0.97])
    ins = fig.add_axes([mw + 0.02, 0.03, 0.98 - mw - 0.02, 0.36])
    return fig, ax, ins, mw


def inset(ins, kind, col):
    draw(ins, kind, col, edge="white", lw=.6)
    ins.set_xlim(LONDON[0], LONDON[1]); ins.set_ylim(LONDON[2], LONDON[3]); ins.axis("on")
    ins.set_xticks([]); ins.set_yticks([])
    for sp in ins.spines.values(): sp.set_color("#8a8578"); sp.set_linewidth(.8)
    ins.set_title("London", fontsize=11, loc="left", family=MONO)


def save(fig, path):
    fig.savefig(path, facecolor="white"); plt.close(fig)


def cat_map(path, kind, field, pal, labels, size=(7.6, 7.4), counts=True, title=None):
    fig, ax, ins, mw = frame(size)
    D = U[kind]; gk = "areas" if kind == "area" else "counties"
    col = lambda k: pal(D[k][field]) if k in D and not D[k].get("ni") else None
    draw(ax, gk, col); inset(ins, gk, col)
    cnt = {}
    for d in D.values():
        if not d.get("ni"): cnt[d[field]] = cnt.get(d[field], 0) + 1
    hs = [Patch(fc=pal(k), ec="#8a8578", lw=.5, label=f"{labels(k)}  {cnt[k]}" if counts else labels(k)) for k in sorted(cnt, key=lambda k: -cnt[k])]
    hs.append(Patch(fc=NA, ec="none", label="No MOT data (NI)"))
    fig.legend(handles=hs, loc="upper left", bbox_to_anchor=(mw + 0.02, 0.97), frameon=False, prop={"family": MONO, "size": 11}, handlelength=1.2,
               title=title, title_fontproperties={"family": MONO, "size": 11}, alignment="left")
    save(fig, path)


def seq_map(path, kind, field, ramp, fmtv, unit_label, size=(7.6, 7.4)):
    fig, ax, ins, mw = frame(size)
    D = U[kind]; gk = "areas" if kind == "area" else "counties"
    vals = sorted(d[field] for d in D.values() if d.get(field) is not None)
    br = [vals[int(len(vals) * k / 5)] for k in (1, 2, 3, 4)]
    def col(k):
        d = D.get(k); x = d.get(field) if d else None
        if x is None: return None
        i = sum(x >= b for b in br); return SEQ[ramp][i]
    draw(ax, gk, col, edge="white", lw=.3); inset(ins, gk, col)
    edges = [vals[0]] + br + [vals[-1]]
    hs = [Patch(fc=SEQ[ramp][i], label=f"{fmtv(edges[i])} to {fmtv(edges[i + 1])}") for i in range(5)]
    fig.legend(handles=hs, loc="upper left", bbox_to_anchor=(mw + 0.02, 0.97), frameon=False, prop={"family": MONO, "size": 11}, title=unit_label,
               title_fontproperties={"family": MONO, "size": 11}, alignment="left")
    save(fig, path)


mk = lambda m: U["make_names"].get(m, m)
mdn = lambda k: U["model_names"].get(k, k)
cn = lambda c: c.capitalize()
MODPAL = {"FORD|FIESTA": "#1F4E9C", "VAUXHALL|CORSA": "#C8322B", "VOLKSWAGEN|GOLF": "#2C9C9C", "TOYOTA|PRIUS": "#E08A1E", "NISSAN|QASHQAI": "#8E3E8F", "TOYOTA|YARIS": "#D9B92E"}


def colour_trend(path, size=(8, 4.6)):
    T = R["colour_trend"]; ys = sorted(int(y) for y in T)
    fig, ax = plt.subplots(figsize=size)
    ends = []
    for c, lw in [("BLACK", 2.6), ("GREY", 2.6), ("WHITE", 2.6), ("BLUE", 2.6), ("SILVER", 2.6), ("RED", 2.6)]:
        v = [T[str(y)].get(c, 0) * 100 for y in ys]
        if c in ("WHITE", "SILVER"): ax.plot(ys, v, color="#8a8578", lw=lw + 1.2)
        ax.plot(ys, v, color=CH[c], lw=lw)
        ends.append([v[-1], cn(c)])
    ends.sort();
    for i in range(1, len(ends)):
        if ends[i][0] - ends[i - 1][0] < 1.4: ends[i][0] = ends[i - 1][0] + 1.4
    for y, t in ends: ax.text(ys[-1] + .5, y, t, va="center", fontsize=11)
    ax.set_ylabel("% of surviving cars"); ax.set_xlabel("Year of first use")
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color="#e5e0d6"); ax.set_xlim(ys[0], ys[-1] + 4)
    fig.savefig(path, bbox_inches="tight", facecolor="white"); plt.close(fig)


def fuel_trend(path, size=(8, 4.6)):
    T = R["fuel_trend"]; ys = sorted(int(y) for y in T)
    K = ["Petrol", "Diesel", "Hybrid", "Electric", "Other"]; C = ["#D9B36A", "#5D5A6E", "#6DB37E", "#1F4E9C", "#BBB4A8"]
    fig, ax = plt.subplots(figsize=size)
    V = np.array([[T[str(y)].get(k, 0) * 100 for y in ys] for k in K])
    ax.stackplot(ys, V, colors=C, labels=K, edgecolor="white", lw=.4)
    ax.set_ylim(0, 100); ax.set_xlim(ys[0], ys[-1]); ax.set_ylabel("% of surviving cars"); ax.set_xlabel("Year of first use")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(path, bbox_inches="tight", facecolor="white"); plt.close(fig)


def nation_bars(path, size=(8, 5.2)):
    fig, axs = plt.subplots(1, 4, figsize=size, sharex=True)
    for ax, nat in zip(axs, ["England", "Scotland", "Wales", "Northern Ireland"]):
        if nat == "Northern Ireland":
            rows = [(m, s) for m, s in R["ni"]["top_makes"][:6]]
        else:
            d = U["nation"][nat]; rows = sorted(zip(U["makes"], d["ms"]), key=lambda x: -x[1])[:6]
        rows = rows[::-1]
        ax.barh([mk(m) for m, _ in rows], [s * 100 for _, s in rows], color=[MAKEPAL.get(m, "#A39C8F") for m, _ in rows])
        for i, (m, s) in enumerate(rows): ax.text(s * 100 + .3, i, f"{s * 100:.1f}", va="center", fontsize=9)
        ax.set_title(nat, fontsize=12, loc="left"); ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=9.5)
        ax.set_xlim(0, 17)
    axs[0].set_xlabel("% of cars"); fig.tight_layout(w_pad=3.0)
    fig.savefig(path, bbox_inches="tight", facecolor="white"); plt.close(fig)


# ---- paper figures (print size) ----
cat_map(os.path.join(PAP, "fig1_make_area.png"), "area", "mk", lambda k: MAKEPAL.get(k, "#A39C8F"), mk, title="Most common make\n(postcode areas)")
cat_map(os.path.join(PAP, "fig2_colour_area.png"), "area", "co", lambda k: CH.get(k, "#999"), cn, title="Most common colour\n(postcode areas)")
cat_map(os.path.join(PAP, "fig3_model_area.png"), "area", "md", lambda k: MODPAL.get(k, "#A39C8F"), mdn, title="Most common model\n(postcode areas)")
colour_trend(os.path.join(PAP, "fig4_colour_trend.png"))
seq_map(os.path.join(PAP, "fig5_bev_county.png"), "county", "bev", "green", lambda x: f"{x:.1f}", "Battery electric per 100\nprivate cars (DfT, 2025)")
seq_map(os.path.join(PAP, "fig6_age_county.png"), "county", "age", "grey", lambda x: f"{x:.1f}", "Average age at test\n(years, MOT 2025)")
fuel_trend(os.path.join(PAP, "fig7_fuel_trend.png"))
nation_bars(os.path.join(PAP, "fig8_nations.png"))

# ---- blog figures, 1520 px wide (7.6 in at 200 dpi) ----
W = 7.6
cat_map(os.path.join(BLOG, "b_make_map.png"), "area", "mk", lambda k: MAKEPAL.get(k, "#A39C8F"), mk, title="Most common make\n(postcode areas)")
cat_map(os.path.join(BLOG, "b_colour_map.png"), "area", "co", lambda k: CH.get(k, "#999"), cn, title="Most common colour\n(postcode areas)")
colour_trend(os.path.join(BLOG, "b_colour_trend.png"), size=(W, 4.4))
fuel_trend(os.path.join(BLOG, "b_fuel_trend.png"), size=(W, 4.4))
seq_map(os.path.join(BLOG, "b_ev_map.png"), "county", "bev", "green", lambda x: f"{x:.1f}", "Battery electric per 100\nprivate cars (DfT, 2025)")
nation_bars(os.path.join(BLOG, "b_nations.png"), size=(W, 4.8))

# ---- header.png, 1200 x 630 ----
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([0.62, 0.02, 0.36, 0.96]); ax.set_facecolor(BG)
D = U["area"]
draw(ax, "areas", lambda k: MAKEPAL.get(D[k]["mk"], "#A39C8F") if k in D and not D[k].get("ni") else NA, edge=BG, lw=.4)
fig.text(0.05, 0.86, "DATA STUDY · CARS · 2025", family=MONO, fontsize=15, color="#C2362B")
fig.text(0.05, 0.62, "What Britain\ndrives", fontproperties=DISP, fontsize=64, color=FG, va="center", linespacing=.95)
F = R["facts"]["GB"]
fig.text(0.05, 0.33, f"The average car is a {F['top_model_colour']} {F['top_model']},\n{F['age']:.1f} years old. Makes, models and colours\nfor every county and postcode area.", family=SER, fontsize=19, color=FG, va="top", linespacing=1.35)
fig.text(0.05, 0.045, "Dr Tristan Hotham · maps.tristanhotham.com/cars", family=MONO, fontsize=13, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), facecolor=BG, dpi=100); plt.close(fig)
from PIL import Image
for f in os.listdir(BLOG):
    if f.startswith("b_") and f.endswith(".png"):
        im = Image.open(os.path.join(BLOG, f))
        if im.size[0] != 1520: im.resize((1520, round(im.size[1] * 1520 / im.size[0])), Image.LANCZOS).save(os.path.join(BLOG, f))
print("figures done")
