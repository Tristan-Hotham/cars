"""r/dataisbeautiful collage for 'What Britain drives'. Every number comes from data/results.json and data/units.json.
Run from the project root or anywhere: python3 reddit/collage.py
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, Rectangle
from shapely.geometry import shape

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
F = "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, NA, RED = "#F2EFE8", "#1C1B1F", "#655F68", "#DCD5C8", "#C2362B"

R = json.load(open(os.path.join(ROOT, "data", "results.json")))
U = json.load(open(os.path.join(ROOT, "data", "units.json")))
G = json.load(open(os.path.join(ROOT, "work", "geo_bng.json")))
FA = R["facts"]; CH = U["colour_hex"]
MAKEPAL = {"FORD": "#1F4E9C", "VAUXHALL": "#C8322B", "VOLKSWAGEN": "#2C9C9C", "TOYOTA": "#E08A1E", "MERCEDES-BENZ": "#5D5A6E", "NISSAN": "#8E3E8F"}
mk = lambda m: U["make_names"].get(m, m)


def polys(g):
    s = shape(g); return list(s.geoms) if s.geom_type == "MultiPolygon" else [s]


def draw(ax, kind, col, edge=BG, lw=.35, xl=(-10000, 670000), yl=(0, 1230000)):
    for k, g in G[kind].items():
        c = col(k)
        for p in polys(g):
            light = c in ("#f4f4f2", "#c3c7cc")
            ax.add_patch(MPoly(np.asarray(p.exterior.coords), closed=True, fc=c or NA, ec="#9a948a" if light else edge, lw=lw))
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.05, 0.968, "What does Britain drive?", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(0.05, 0.908, f"The most common car make in every postcode area of Great Britain, from {FA['GB']['cars']:,} cars\nthat had an MOT test in 2025, each counted once. The average car? A blue Ford Fiesta.",
         family=SER, fontsize=15.5, color=FG, va="top", linespacing=1.4)

# paint-chip strip: Britain's car colours
ax = fig.add_axes([0.05, 0.800, 0.90, 0.032]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
x = 0
cols = R["gb_colours"]
for c, s in cols:
    ax.add_patch(Rectangle((x, 0), s, 1, fc=CH.get(c, "#999"), ec=BG, lw=1.2))
    if s > 0.09: ax.text(x + s / 2, 0.5, f"{c.capitalize()} {s * 100:.0f}%", ha="center", va="center", family=MONO, fontsize=11.5,
                         color="white" if c in ("BLACK", "BLUE", "RED", "GREY") else FG)
    x += s
ax.add_patch(Rectangle((x, 0), 1 - x, 1, fc="#B9B2A6", ec=BG, lw=1.2))
fig.text(0.95, 0.837, f"Every colour, all {FA['GB']['cars'] / 1e6:.1f} million cars", family=MONO, fontsize=10.5, color=MUT, ha="right")
fig.text(0.05, 0.837, "BRITAIN'S CAR COLOURS", family=MONO, fontsize=10.5, color=MUT)

# hero map: most common make by postcode area
D = U["area"]
ax = fig.add_axes([0.0, 0.265, 0.56, 0.49])
draw(ax, "areas", lambda k: MAKEPAL.get(D[k]["mk"], "#A39C8F") if k in D and not D[k].get("ni") else None, lw=.4)
ax.text(70000, 560000, "Northern Ireland:\nno MOT data", family=MONO, fontsize=9.5, color=MUT, ha="center")
cnt = {}
for d in D.values():
    if not d.get("ni"): cnt[d["mk"]] = cnt.get(d["mk"], 0) + 1
order = sorted(cnt, key=lambda m: -cnt[m])
fig.text(0.05, 0.772, "TOP MAKE, NUMBER OF AREAS:", family=MONO, fontsize=10.5, color=MUT, va="center")
xx = 0.285
for m in order:
    fig.patches.append(Rectangle((xx, 0.766), 0.013, 0.011, transform=fig.transFigure, fc=MAKEPAL.get(m, "#A39C8F"), ec="none"))
    t = f"{mk(m)} {cnt[m]}"; fig.text(xx + 0.017, 0.772, t, family=MONO, fontsize=11, color=FG, va="center")
    xx += 0.017 + len(t) * 0.0080 + 0.013

# London inset
ins = fig.add_axes([0.41, 0.275, 0.17, 0.135])
draw(ins, "areas", lambda k: MAKEPAL.get(D[k]["mk"], "#A39C8F") if k in D and not D[k].get("ni") else None, lw=.7, xl=(503000, 563000), yl=(152000, 202000))
ins.axis("on"); ins.set_xticks([]); ins.set_yticks([])
for sp in ins.spines.values(): sp.set_color(FG); sp.set_linewidth(.9)
ins.text(0.03, 0.97, "London", transform=ins.transAxes, family=MONO, fontsize=11, color=FG, va="top", bbox=dict(fc=BG, ec="none", pad=2))

# right column: big numbers
tx = fig.add_axes([0.60, 0.27, 0.38, 0.47]); tx.axis("off")
notes = [(f"{FA['GB']['top_make_share'] * 100:.1f}%", f"of cars are Fords. Ford leads in {FA['areas_ford']} of\n{FA['areas_n']} postcode areas; the Fiesta, out of\nproduction since 2023, is still number one."),
         (f"{FA['a_ZE']['top_make_share'] * 100:.1f}%", f"of Shetland's cars are Toyotas, {FA['unusual_area'][0]['lq']:.1f} times\nScotland's share: Britain's most unusual area."),
         (f"{FA['grey2000'] * 100:.0f}% to {FA['grey2022'] * 100:.0f}%", "grey's share of surviving cars first used\nin 2000 and in 2022. Silver fell from\n" + f"{FA['silver2000'] * 100:.0f}% to {FA['silver2022'] * 100:.0f}%."),
         ("White", f"is Scotland's top colour ({FA['Scotland']['top_colour_share'] * 100:.1f}%) and the\nVauxhall Corsa its top model. England and\nWales prefer black.")]
for (big, small), y in zip(notes, [1.0, 0.75, 0.52, 0.27]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=30, color=RED, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.085, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# small multiples
SEQ_G = ["#E8F1DE", "#B5D9A3", "#6DB37E", "#2E7D4F", "#11492C"]; SEQ_K = ["#EFEDE8", "#CFCAC0", "#A59E92", "#746D63", "#45403A"]
def seq(field, ramp, kind="county"):
    DD = U[kind]; v = sorted(d[field] for d in DD.values() if d.get(field) is not None); br = [v[int(len(v) * k / 5)] for k in (1, 2, 3, 4)]
    return lambda k: (ramp[sum(DD[k][field] >= b for b in br)] if k in DD and DD[k].get(field) is not None else None), (v[0], v[-1])
SM = [("Most common colour", "postcode areas", "areas", lambda k: CH.get(D[k]["co"]) if k in D and not D[k].get("ni") else None,
       f"Black in {FA['areas_col_black']} areas\nwhite in {FA['areas_col_white']}\nblue in {FA['areas_col_blue']}"),
      ("Electric cars per 100", "private cars, DfT, UK", "counties", seq("bev", SEQ_G)[0],
       f"From {FA['bev_low'][0]['bev']:.1f} in\nFermanagh and Omagh\nto {FA['bev_top'][0]['bev']:.1f} in the\nCity of London"),
      ("Average age at test", "counties", "counties", seq("age", SEQ_K)[0],
       f"From {R['ranks']['youngest_counties'][0]['age']:.1f} years in\nNorth Lanarkshire\nto {R['ranks']['oldest_counties'][0]['age']:.1f} in Torbay")]
for i, (t1, t2, kind, col, note) in enumerate(SM):
    x0 = 0.03 + i * 0.32
    a = fig.add_axes([x0 + 0.13, 0.058, 0.17, 0.19]); draw(a, kind, col, lw=.25)
    fig.text(x0 + 0.005, 0.240, t1, family=MONO, fontsize=12.5, color=FG, weight="medium")
    fig.text(x0 + 0.005, 0.228, t2, family=MONO, fontsize=10, color=MUT)
    fig.text(x0 + 0.005, 0.205, note, family=MONO, fontsize=10, color=FG, va="top", linespacing=1.35)

fig.text(0.05, 0.040, "Data: DVSA anonymised MOT tests 2025; DfT vehicle licensing statistics (VEH0120, VEH0125, VEH0145); ONS Postcode Directory and", family=MONO, fontsize=9.5, color=MUT)
fig.text(0.05, 0.027, "boundaries (all Open Government Licence v3). Cars placed by testing garage; under-3s have no MOT; vans and pick-ups set aside.", family=MONO, fontsize=9.5, color=MUT)
fig.text(0.05, 0.014, "Analysis and chart: Tristan Hotham, with Python and matplotlib.  maps.tristanhotham.com/cars", family=MONO, fontsize=9.5, color=MUT)
out = os.path.join(HERE, "what_britain_drives.png")
fig.savefig(out, facecolor=BG); print(out)
