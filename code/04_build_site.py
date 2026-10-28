"""Step 4. Build index.html from code/page_template.html, and the small data files the page loads.

Every number in the text is a {{path|format}} token filled from data/results.json. The per-place data
(work/site_units.json from step 3) is packed into data/units.json; place names for search and labels
(OS Open Names cities, towns, villages and suburbs, each tagged with its postcode area and county by
point in polygon) go to data/places.json.
Run: python3 code/04_build_site.py
"""
import json, os, re, csv
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import DATA, WORK, ROOT, HERE

R = json.load(open(os.path.join(DATA, "results.json"), encoding="utf-8"))
U = json.load(open(os.path.join(WORK, "site_units.json"), encoding="utf-8"))


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "x1": return f"{v:.1f}"
    if f == "m": return f"{v / 1e6:.1f} million"
    if f == "lc": return str(v).lower()
    raise ValueError(f)


TOK = r"\{\{([^}|]+)(\|(\w+))?\}\}"
sub = lambda m: fmt(get(m.group(1)), m.group(3))

# ---- facts the template states in words: check them against the data ----
F = R["facts"]
assert F["GB"]["top_make"] == "Ford" and F["GB"]["top_colour"] == "black" and F["GB"]["top_model"] == "Ford Fiesta" and F["GB"]["top_model_colour"] == "blue"
assert F["Scotland"]["top_colour"] == "white" and F["Scotland"]["top_model"] == "Vauxhall Corsa" and F["Scotland"]["make2"] == "Vauxhall"
assert F["Wales"]["top_colour"] == "black" and F["England"]["top_colour"] == "black" and F["England"]["colour2"] == "grey"
assert F["NI"]["m1"] == "Volkswagen" and F["NI"]["m2"] == "Audi" and F["NI"]["mod1"] == "Volkswagen Golf"
assert F["a_ZE"]["top_make"] == "Toyota" and F["a_E"]["top_model"] == "Toyota Prius" and F["a_LU"]["top_make"] == "Vauxhall"
assert F["unusual"]["England"][0]["name"] == "Camden" and F["unusual"]["Scotland"][0]["name"] == "Scottish Borders" and F["unusual"]["Wales"][0]["name"] == "Flintshire"
assert F["unusual_area"][0]["code"] == "ZE"
assert [x["name"] for x in F["bev_top"][:3]] == ["City of London", "Camden", "Westminster"] and F["bev_low"][0]["name"] == "Fermanagh and Omagh"
assert F["Scotland"]["age"] < F["Wales"]["age"] < F["England"]["age"]
assert R["ranks"]["oldest_counties"][0]["name"] == "Torbay" and R["ranks"]["youngest_areas"][0]["name"] == "Motherwell"
assert F["diesel_peak_year"] == 2014
assert F["bev_low_gb"][0]["name"] == "Na h-Eileanan Siar" and F["bev_scot"][1]["name"] == "Orkney Islands"

# ---- pack per-place data ----
MK, CO = U["makes"], [c for c in U["colours"] if c != "MULTI-COLOUR"]
FU = ["Petrol", "Diesel", "Hybrid", "Electric", "Other"]
r3 = lambda x: None if x is None else round(x, 4)
def pack(s):
    o = dict(n=s["name"], nat=s.get("nation"), dft=s.get("dft_cars"), bev=r3(s.get("bev_per100")), piv=r3(s.get("piv_per100")))
    if s.get("ni") or "make_shares" not in s:
        o["ni"] = 1; return o
    o.update(c=s["cars"], mk=s["top_make"], mks=r3(s["top_make_share"]), m2=s["make2"], m2s=r3(s["make2_share"]),
             co=s["top_colour"], cos=r3(s["top_colour_share"]), c2=s["colour2"], c2s=r3(s["colour2_share"]),
             md=s["top_model"], mds=r3(s["top_model_share"]), mdc=s["top_model_colour"], mods=[[k, r3(v)] for k, v in s["models"]],
             age=round(s["age"], 2), cc=round(s["cc"]), o20=r3(s["old20"]), fu=[r3(s["fuel"][f]) for f in FU],
             ms=[r3(s["make_shares"][m]) for m in MK], cs=[r3(s["colour_shares"][c]) for c in CO],
             sig=s.get("sig_make"), sigq=r3(s.get("sig_lq")), sgc=s.get("sig_colour"), sgcq=r3(s.get("sig_colour_lq")), dis=r3(s.get("dissim")))
    return o
units = dict(makes=MK, colours=CO, fuels=FU, make_names=U["make_names"], model_names=U["model_names"], colour_hex=R["colour_hex"],
             area={k: pack(s) for k, s in U["areas"].items()}, county={k: pack(s) for k, s in U["counties"].items()},
             nation={k: pack(s) for k, s in U["nations"].items()}, gb=pack(U["gb"]), ni=U["ni"])
json.dump(units, open(os.path.join(DATA, "units.json"), "w"), separators=(",", ":"))

# ---- places: OS Open Names, tagged with postcode area and county ----
def polys(path):
    gj = json.load(open(os.path.join(DATA, path)))
    return [(f["properties"]["id"], shape(f["geometry"])) for f in gj["features"]]
AP, CP = polys("postcode_areas.geojson"), polys("counties.geojson")
def locator(P):
    tree = STRtree([g for _, g in P])
    def f(pt):
        for i in tree.query(pt):
            if P[i][1].contains(pt): return P[i][0]
        # nearest (coastal points can sit just outside the generalised polygons)
        i = tree.nearest(pt); return P[i][0]
    return f
loc_a, loc_c = locator(AP), locator(CP)
RANK = {"City": 3, "Town": 2, "Village": 1, "Suburban Area": 0}
places = []
for r in csv.DictReader(open("/home/claude/hist/osnames_gb.tsv", encoding="utf-8"), delimiter="\t"):
    if r["type"] != "populatedPlace" or r["local_type"] not in RANK: continue
    lat, lon = float(r["lat"]), float(r["lon"]); pt = Point(lon, lat)
    nm = r["name2"] if r["lang2"] == "eng" and r["name2"] else r["name1"]
    alt = r["name1"] if nm != r["name1"] else (r["name2"] or "")
    places.append([nm, round(lat, 4), round(lon, 4), RANK[r["local_type"]], loc_a(pt), loc_c(pt), r["county"] or r["district"], alt])
places.sort(key=lambda p: (-p[3], p[0]))
json.dump(dict(source="OS Open Names (OGL v3), cities, towns, villages and suburban areas", cols=["name", "lat", "lon", "rank", "postcode_area", "ctyua", "county_or_district", "other_language_name"], places=places),
          open(os.path.join(DATA, "places.json"), "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
print("places", len(places))

# ---- page ----
tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
html = re.sub(TOK, sub, tpl)
slim = {k: R[k] for k in ["colour_trend", "fuel_trend", "gb_models", "gb_makes", "gb_colours", "make_colour"]}
slim["ranks"] = {k: R["ranks"][k] for k in ["oldest_counties", "youngest_counties", "oldest_areas", "youngest_areas", "bev_counties", "bev_low_counties", "unusual", "unusual_areas"]}
slim["ni"] = R["ni"]; slim["gb_veh"] = R["gb_veh"]
html = html.replace("/*RESULTS*/", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
assert "{{" not in html
vis = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S))
for bad in ("—", "–", "--"):
    assert bad not in vis, bad
js = re.search(r"<script>\nconst R =.*?</script>", html, flags=re.S).group(0)
for bad in ("—", "–"): assert bad not in js, bad
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
print("index.html", len(html.encode()), "bytes")
