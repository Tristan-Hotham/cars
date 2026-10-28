"""Step 3. Analysis: cars by postcode area, county or unitary authority, nation and Great Britain.

Inputs: the three browser-gathered bundles (see README) and data/area_county_weights.csv from step 2.
Outputs: data/*.csv tables, data/results.json (every number used in the page, paper, blog and collage)
and work/site_units.json (the per-place data the page embeds).
Run: python3 code/03_analyse.py
"""
import json, csv, os, collections, math
from common import load_gz, DATA, WORK, fuel_group, title, AREA_NAME, is_van

M = load_gz("cars_mot2025_v2.json.gz")
G = load_gz("cars_onspd_geo.json.gz")
V = load_gz("cars_dft_veh.json.gz")
CTY = json.load(open(os.path.join(WORK, "counties_meta.json")))
LK = {r["LAD26CD"]: r for r in G["lookup"]}
NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"]
FUELS = ["Petrol", "Diesel", "Hybrid", "Electric", "Other"]
COLOUR_ORDER = None

def num(x):
    try: return float(x)
    except Exception: return 0.0

# ---------- display names ----------
def make_name(m):
    return {"MERCEDES-BENZ": "Mercedes-Benz", "SMART (MCC)": "Smart", "ALFA ROMEO": "Alfa Romeo", "LAND ROVER": "Land Rover",
            "ASTON MARTIN": "Aston Martin", "ROLLS ROYCE": "Rolls-Royce", "DS": "DS", "MG": "MG", "BMW": "BMW", "SEAT": "SEAT",
            "MINI": "Mini", "KIA": "Kia", "SKODA": "Skoda", "CITROEN": "Citroen"}.get(m, title(m))
def fam_name(make, fam):
    if make == "MINI" and fam == "HATCH": return "Mini hatch"
    if make == "HYUNDAI" and fam[:1] == "I" and fam[1:2].isdigit(): return "Hyundai i" + fam[1:]
    if make == "TOYOTA" and fam == "RAV4": return "Toyota RAV4"
    return make_name(make) + " " + title(fam).replace("Id.3", "ID.3")
COLOUR_HEX = {"BLACK": "#1d1d1f", "WHITE": "#f4f4f2", "GREY": "#8a8d91", "BLUE": "#2f5fa8", "SILVER": "#c3c7cc", "RED": "#c7322b",
              "GREEN": "#3f7d3b", "ORANGE": "#e3801f", "BROWN": "#6e4a2e", "YELLOW": "#efc61f", "BEIGE": "#d8c7a4", "PURPLE": "#6d3f8f",
              "BRONZE": "#9c6b30", "GOLD": "#c9a43a", "TURQUOISE": "#2aa3a3", "CREAM": "#efe6cc", "PINK": "#e58fb1", "MAROON": "#6e1f2b",
              "MULTI-COLOUR": "#999999"}

# ---------- MOT: per postcode area (cars only) ----------
A = {a: v for a, v in M["areas"].items() if a not in ("XX", "NA")}
areaFam = collections.defaultdict(dict)
for k, n in M["nat"]["areaFam"]:
    a, mk, fm = k.split("|"); areaFam[a][mk + "|" + fm] = n
areaFamCol = collections.defaultdict(dict)
for k, n in M["nat"]["areaFamColour"]:
    a, mk, fm, c = k.split("|"); areaFamCol[a][(mk + "|" + fm, c)] = n

def fuel_groups(d):
    out = collections.Counter()
    for k, n in d.items(): out[fuel_group(k)] += n
    return out

def unit_from_area(a):
    c = A[a]["car"]
    return dict(n=c["n"], make=collections.Counter(c["make"]), colour=collections.Counter({k: v for k, v in c["colour"].items() if k not in ("NA", "NOT STATED")}),
                fuel=fuel_groups(c["fuel"]), fy=collections.Counter(c["fy"]), fam=collections.Counter(areaFam[a]),
                famcol=collections.Counter(areaFamCol[a]), ageSum=c["ageSum"], ageN=c["ageN"], ccSum=c["ccSum"], ccN=c["ccN"],
                vans=A[a]["van"]["n"], vancol=collections.Counter(A[a]["van"]["colour"]))

def scale(u, w):
    o = {}
    for k, v in u.items():
        if isinstance(v, collections.Counter): o[k] = collections.Counter({kk: vv * w for kk, vv in v.items()})
        else: o[k] = v * w
    return o
def add(u, v):
    if u is None: return {k: (collections.Counter(x) if isinstance(x, collections.Counter) else x) for k, x in v.items()}
    for k, x in v.items():
        if isinstance(x, collections.Counter): u[k].update(x)
        else: u[k] += x
    return u

AU = {a: unit_from_area(a) for a in A}

# ---------- weights: postcode area -> county; LSOA -> area; LSOA -> county ----------
W = collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(DATA, "area_county_weights.csv"))):
    W[r["postcode_area"]][r["ctyua_code"]] = float(r["share_of_area"])
lsoa_area = collections.defaultdict(collections.Counter); lsoa_cty = {}
area_nation_pc = collections.defaultdict(collections.Counter)
for a, lsoa, lad, cty, ctry, n, e, no in G["rows"]:
    if lad is None or lad not in LK: continue
    if lsoa: lsoa_area[lsoa][a] += n; lsoa_cty[lsoa] = LK[lad]["CTYUA26CD"]
    area_nation_pc[a][LK[lad]["CTRY26NM"]] += n
AREA_NATION = {a: c.most_common(1)[0][0] for a, c in area_nation_pc.items()}

CU = {}
for a, ws in W.items():
    if a not in AU: continue
    for c, w in ws.items():
        CU[c] = add(CU.get(c), scale(AU[a], w))
NU = {}
for c, u in CU.items():
    nat = CTY[c]["nation"]; NU[nat] = add(NU.get(nat), u)
GB = None
for nat in ("England", "Scotland", "Wales"): GB = add(GB, NU[nat])

# ---------- DfT licensing: licensed cars and plug-in vehicles by LSOA -> county, area, nation ----------
def lsoa_vals():
    out = {}
    for ls, d in V["veh0125"]["rows"].items():
        lic = d.get("Total|Licensed", ["0", "0"])
        out[ls] = {"cars": num(lic[1]), "cars26": num(lic[0]), "pcars": num(d.get("Private|Licensed", ["0", "0"])[1])}
    for ls, d in V["veh0145"]["rows"].items():
        o = out.setdefault(ls, {"cars": 0, "cars26": 0, "pcars": 0})
        o["pbev"] = num(d.get("Battery electric|Private", ["0", "0"])[1]); o["ppiv"] = num(d.get("Total|Private", ["0", "0"])[1])
        o["piv"] = num(d.get("Total|Total", ["0", "0"])[1]); o["bev"] = num(d.get("Battery electric|Total", ["0", "0"])[1])
        o["phev"] = num(d.get("Plug-in hybrid electric (petrol)|Total", ["0", "0"])[1]) + num(d.get("Plug-in hybrid electric (diesel)|Total", ["0", "0"])[1])
    return out
LV = lsoa_vals()
DC = collections.defaultdict(lambda: collections.Counter()); DA = collections.defaultdict(lambda: collections.Counter()); DN = collections.defaultdict(lambda: collections.Counter())
unplaced = collections.Counter()
for ls, v in LV.items():
    vv = {k: v.get(k, 0) for k in ("cars", "cars26", "pcars", "piv", "bev", "phev", "pbev", "ppiv")}
    c = lsoa_cty.get(ls)
    if c is None: unplaced.update(vv); continue
    DC[c].update(vv); DN[CTY[c]["nation"]].update(vv)
    tot = sum(lsoa_area[ls].values())
    for a, n in lsoa_area[ls].items(): DA[a].update({k: x * n / tot for k, x in vv.items()})
print("DfT LSOAs not placed:", dict(unplaced))

# NI and GB makes and models from VEH0120 (UK minus GB = Northern Ireland)
def veh120(rows):
    mk, md, fu = collections.Counter(), collections.Counter(), collections.Counter()
    for make, gen, model, fuel, q26, q25 in rows:
        n = num(q25); g = gen[len(make) + 1:] if gen.startswith(make + " ") else gen
        mk[make] += n; md[(make, g)] += n; fu[fuel] += n
    return mk, md, fu
uk = veh120(V["veh0120_uk"]["rows"]); gb = veh120(V["veh0120_gb"]["rows"])
ni = tuple(collections.Counter({k: uk[i][k] - gb[i].get(k, 0) for k in uk[i] if uk[i][k] - gb[i].get(k, 0) > 0}) for i in range(3))

# ---------- summaries ----------
def share(c, k, tot): return c.get(k, 0) / tot if tot else 0
def top(c, n=1): return c.most_common(n)
def fam_disp(k):
    mk, fm = k.split("|"); return fam_name(mk, fm)
def car_fams(c):
    return collections.Counter({k: v for k, v in c.items() if not is_van(*k.split("|"))})

MAKES_KEEP = [m for m, _ in GB["make"].most_common(40)]
COLOURS = [c for c, _ in GB["colour"].most_common() if c in COLOUR_HEX]
FY_MIN = 1960

def dft_rates(d):
    """Battery-electric and all plug-in vehicles per 100 licensed cars, private keepers only (company fleets are
    registered at head-office addresses, which piles lease cars into a few places); all-keeper rate kept for reference."""
    return dict(dft_cars=round(d["cars"]), dft_private_cars=round(d["pcars"]),
                bev_per100=100 * d["pbev"] / d["pcars"] if d["pcars"] else None,
                piv_per100=100 * d["ppiv"] / d["pcars"] if d["pcars"] else None,
                bev_all_per100=100 * d["bev"] / d["cars"] if d["cars"] else None)

def summary(u, name, kind, code=None, nation=None, dft=None):
    n = u["n"]; fams = car_fams(u["fam"])
    tm = top(u["make"], 3); tc = top(u["colour"], 3); tf = top(fams, 5)
    # colour of the most common model in this place
    k0 = tf[0][0]
    fc = collections.Counter({c: v for (k, c), v in u["famcol"].items() if k == k0 and c in COLOUR_HEX})
    fy = u["fy"]; old20 = sum(v for y, v in fy.items() if y.isdigit() and int(y) <= 2005)
    pre2000 = sum(v for y, v in fy.items() if y.isdigit() and int(y) < 2000)
    fyt = sum(fy.values())
    fuel = u["fuel"]; ft = sum(fuel.values())
    s = dict(code=code, name=name, kind=kind, nation=nation, cars=round(n), vans=round(u["vans"]),
             top_make=tm[0][0], top_make_share=tm[0][1] / n, make2=tm[1][0], make2_share=tm[1][1] / n,
             top_colour=tc[0][0], top_colour_share=tc[0][1] / n, colour2=tc[1][0], colour2_share=tc[1][1] / n,
             top_model=k0, top_model_name=fam_disp(k0), top_model_share=tf[0][1] / n,
             top_model_colour=fc.most_common(1)[0][0] if fc else tc[0][0],
             models=[[k, round(v / n, 5)] for k, v in tf],
             age=u["ageSum"] / u["ageN"], cc=u["ccSum"] / u["ccN"], old20=old20 / fyt, pre2000=pre2000 / fyt,
             fuel={f: fuel.get(f, 0) / ft for f in FUELS},
             make_shares={m: round(u["make"].get(m, 0) / n, 5) for m in MAKES_KEEP},
             colour_shares={c: round(u["colour"].get(c, 0) / n, 5) for c in COLOURS})
    s["top_fuel"] = max(FUELS, key=lambda f: s["fuel"][f])
    if dft:
        s.update(dft_rates(dft))
    return s

areas = {a: summary(AU[a], AREA_NAME.get(a, a), "area", a, AREA_NATION.get(a), DA.get(a)) for a in AU}
counties = {c: summary(CU[c], CTY[c]["name"], "county", c, CTY[c]["nation"], DC.get(c)) for c in CU}
nations = {k: summary(NU[k], k, "nation", None, k, DN.get(k)) for k in ("England", "Scotland", "Wales")}
gbs = summary(GB, "Great Britain", "gb", None, None, None)
gb_dft = DN["England"] + DN["Scotland"] + DN["Wales"]
gbs.update(dft_rates(gb_dft))
uk_dft = gb_dft + DN["Northern Ireland"]

# Northern Ireland: DfT only (no MOT data, NI tests are run by DVA)
nid = DN["Northern Ireland"]
ni_unit = dict(name="Northern Ireland", kind="nation", nation="Northern Ireland", **dft_rates(nid),
               top_makes=[[m, v / sum(ni[0].values())] for m, v in ni[0].most_common(10)],
               top_models=[[mk + "|" + g, v / sum(ni[0].values())] for (mk, g), v in ni[1].most_common(10)],
               fuels={f: v / sum(ni[2].values()) for f, v in ni[2].most_common()})
gb_veh = dict(top_makes=[[m, v / sum(gb[0].values())] for m, v in gb[0].most_common(10)],
              top_models=[[mk + "|" + g, v / sum(gb[0].values())] for (mk, g), v in gb[1].most_common(10)],
              fuels={f: v / sum(gb[2].values()) for f, v in gb[2].most_common()}, cars=sum(gb[0].values()))
# NI counties (LGDs): DfT fields only
for c, d in DC.items():
    if CTY[c]["nation"] == "Northern Ireland":
        counties[c] = dict(code=c, name=CTY[c]["name"], kind="county", nation="Northern Ireland", ni=True, **dft_rates(d))
if "BT" in DA:
    d = DA["BT"]
    areas["BT"] = dict(code="BT", name="Belfast", kind="area", nation="Northern Ireland", ni=True, **dft_rates(d))

# ---------- unusualness: how far a place's make mix is from its nation's ----------
def dissim(u, ref):
    n, rn = u["n"], ref["n"]
    keys = set(u["make"]) | set(ref["make"])
    return 0.5 * sum(abs(u["make"].get(k, 0) / n - ref["make"].get(k, 0) / rn) for k in keys)
def signature(u, ref, minshare=0.01):
    n, rn = u["n"], ref["n"]; best = None
    for k, v in u["make"].items():
        s = v / n; r = ref["make"].get(k, 0) / rn
        if s >= minshare and r > 0:
            lq = s / r
            if best is None or lq > best[1]: best = (k, lq, s, r)
    return best
def col_signature(u, ref):
    n, rn = u["n"], ref["n"]; best = None
    for k, v in u["colour"].items():
        if k not in COLOUR_HEX: continue
        s = v / n; r = ref["colour"].get(k, 0) / rn
        if s >= 0.01 and r > 0:
            lq = s / r
            if best is None or lq > best[1]: best = (k, lq, s, r)
    return best
for c, s in counties.items():
    if s.get("ni"): continue
    u = CU[c]; ref = NU[s["nation"]]
    s["dissim"] = dissim(u, ref); sig = signature(u, ref); s["sig_make"], s["sig_lq"], s["sig_share"], s["sig_nat_share"] = sig
    cs = col_signature(u, ref); s["sig_colour"], s["sig_colour_lq"] = cs[0], cs[1]
for a, s in areas.items():
    if s.get("ni"): continue
    u = AU[a]; ref = NU[s["nation"]] if s["nation"] in NU else GB
    s["dissim"] = dissim(u, ref); sig = signature(u, ref); s["sig_make"], s["sig_lq"], s["sig_share"], s["sig_nat_share"] = sig
    cs = col_signature(u, ref); s["sig_colour"], s["sig_colour_lq"] = cs[0], cs[1]
for k, s in nations.items():
    s["dissim_vs_gb"] = dissim(NU[k], GB); sig = signature(NU[k], GB, 0.005); s["sig_make"], s["sig_lq"] = sig[0], sig[1]

# ---------- national trend tables ----------
cfy = collections.defaultdict(collections.Counter)
for k, n in M["nat"]["colourFy"]:
    c, y = k.split("|")
    if y.isdigit() and 1990 <= int(y) <= 2022 and c in COLOUR_HEX: cfy[int(y)][c] += n
colour_trend = {y: {c: v / sum(cc.values()) for c, v in cc.items()} for y, cc in sorted(cfy.items())}
ffy = collections.defaultdict(collections.Counter)
for k, n in M["nat"]["fuelFy"]:
    f, y = k.split("|")
    if y.isdigit() and 1990 <= int(y) <= 2022: ffy[int(y)][fuel_group(f)] += n
fuel_trend = {y: {f: v / sum(cc.values()) for f, v in cc.items()} for y, cc in sorted(ffy.items())}
fy_all = collections.Counter()
for k, n in M["nat"]["colourFy"]:
    c, y = k.split("|")
    if y.isdigit(): fy_all[int(y)] += n
# colour by make (GB, cars)
mc = collections.defaultdict(collections.Counter)
for k, n in M["nat"]["makeColour"]:
    m, c = k.split("|"); mc[m][c] += n
make_colour = {m: {c: v / sum(mc[m].values()) for c, v in mc[m].most_common(6)} for m in MAKES_KEEP[:20]}
# rarest survivors: the oldest common models
oldest_fy = sorted([(y, n) for y, n in fy_all.items() if y < 1960 and y > 1880])

# ---------- write tables ----------
def wcsv(path, rows, cols):
    with open(os.path.join(DATA, path), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in rows: w.writerow([r.get(c, "") if not isinstance(r.get(c), float) else round(r.get(c), 5) for c in cols])
COLS = ["code", "name", "kind", "nation", "cars", "vans", "top_make", "top_make_share", "make2", "make2_share", "top_model_name", "top_model_share",
        "top_colour", "top_colour_share", "colour2", "colour2_share", "top_model_colour", "age", "cc", "old20", "pre2000", "top_fuel",
        "dft_cars", "dft_private_cars", "bev_per100", "piv_per100", "bev_all_per100", "dissim", "sig_make", "sig_lq", "sig_colour", "sig_colour_lq"]
def flat(s):
    r = dict(s)
    if "fuel" in s:
        for f in FUELS: r["fuel_" + f.lower()] = s["fuel"][f]
    return r
FC = ["fuel_" + f.lower() for f in FUELS]
wcsv("postcode_areas.csv", [flat(s) for _, s in sorted(areas.items())], COLS + FC)
wcsv("counties.csv", [flat(s) for _, s in sorted(counties.items(), key=lambda x: (x[1]["nation"], x[1]["name"]))], COLS + FC)
wcsv("nations.csv", [flat(s) for s in list(nations.values()) + [gbs]], COLS + FC)
with open(os.path.join(DATA, "area_make_counts.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["postcode_area", "make", "cars"])
    for a in sorted(AU):
        for m, n in AU[a]["make"].most_common(): w.writerow([a, m, n])
with open(os.path.join(DATA, "area_model_counts.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["postcode_area", "make", "model_family", "cars", "van_or_pickup"])
    for a in sorted(AU):
        for k, n in AU[a]["fam"].most_common():
            if n < 5: continue
            mk, fm = k.split("|"); w.writerow([a, mk, fm, n, int(is_van(mk, fm))])
with open(os.path.join(DATA, "area_colour_fuel_counts.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["postcode_area", "variable", "value", "cars"])
    for a in sorted(A):
        for c, n in sorted(A[a]["car"]["colour"].items()): w.writerow([a, "colour", c, n])
        for c, n in sorted(A[a]["car"]["fuel"].items()): w.writerow([a, "fuel_code", c, n])
        for c, n in sorted(A[a]["car"]["fy"].items()): w.writerow([a, "first_use_year", c, n])
with open(os.path.join(DATA, "gb_colour_by_year.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["first_use_year", "colour", "share_of_cars"])
    for y, d in colour_trend.items():
        for c, v in sorted(d.items()): w.writerow([y, c, round(v, 5)])

# ---------- results.json ----------
def rk(d, key, rev=True, n=10, flt=lambda s: True):
    L = [s for s in d.values() if key in s and s[key] is not None and flt(s)]
    return sorted(L, key=lambda s: s[key], reverse=rev)[:n]
def slim(s, keys=("code", "name", "nation", "cars")):
    return {k: s.get(k) for k in keys}
big = lambda s: s.get("cars", 0) >= 15000
R = dict(
    meta=dict(year=2025, rows=M["stats"]["rows"], cls4=M["stats"]["cls4"], vehicles=M["stats"]["uniq"], cars=M["stats"]["cars"], vans=M["stats"]["vans"],
              van_share=M["stats"]["vans"] / M["stats"]["uniq"], areas=len(AU), counties=len(counties), retests=M["stats"]["dups"],
              postcodes=sum(p[5] for p in G["rows"]), gb_licensed_cars=round(gb_dft["cars"]), uk_licensed_cars=round(uk_dft["cars"]),
              mot_vs_licensed=M["stats"]["cars"] / gb_dft["cars"]),
    gb=gbs, nations=nations, ni=ni_unit, gb_veh=gb_veh,
    uk=dft_rates(uk_dft),
    ranks=dict(
        oldest_areas=[dict(slim(s), age=s["age"], old20=s["old20"]) for s in rk(areas, "age")],
        youngest_areas=[dict(slim(s), age=s["age"]) for s in rk(areas, "age", False)],
        oldest_counties=[dict(slim(s), age=s["age"], old20=s["old20"]) for s in rk(counties, "age", flt=big)],
        youngest_counties=[dict(slim(s), age=s["age"]) for s in rk(counties, "age", False, flt=big)],
        bev_counties=[dict(slim(s, ("code", "name", "nation", "dft_cars")), bev=s["bev_per100"]) for s in rk(counties, "bev_per100")],
        bev_low_counties=[dict(slim(s, ("code", "name", "nation", "dft_cars")), bev=s["bev_per100"]) for s in rk(counties, "bev_per100", False)],
        bev_areas=[dict(slim(s, ("code", "name", "nation", "dft_cars")), bev=s["bev_per100"]) for s in rk(areas, "bev_per100")],
        mot_ev_areas=[dict(slim(s), ev=s["fuel"]["Electric"]) for s in sorted([x for x in areas.values() if "fuel" in x], key=lambda s: -s["fuel"]["Electric"])[:10]],
        cc_areas=[dict(slim(s), cc=s["cc"]) for s in rk(areas, "cc")],
        cc_low_areas=[dict(slim(s), cc=s["cc"]) for s in rk(areas, "cc", False)],
        diesel_areas=[dict(slim(s), diesel=s["fuel"]["Diesel"]) for s in sorted([x for x in areas.values() if "fuel" in x], key=lambda s: -s["fuel"]["Diesel"])[:10]],
        unusual={nat: [dict(slim(s), dissim=s["dissim"], sig_make=s["sig_make"], sig_lq=s["sig_lq"], sig_share=s["sig_share"], sig_nat_share=s["sig_nat_share"],
                            sig_colour=s["sig_colour"], sig_colour_lq=s["sig_colour_lq"], top_make=s["top_make"], top_colour=s["top_colour"])
                       for s in rk(counties, "dissim", n=6, flt=lambda s, nat=nat: s["nation"] == nat and big(s))] for nat in ("England", "Scotland", "Wales")},
        unusual_areas=[dict(slim(s), dissim=s["dissim"], sig_make=s["sig_make"], sig_lq=s["sig_lq"], sig_share=s["sig_share"]) for s in rk(areas, "dissim", n=10)],
        nonford_areas=[dict(slim(s), top_make=s["top_make"], share=s["top_make_share"]) for s in areas.values() if "top_make" in s and s["top_make"] != "FORD"],
        nonford_counties=[dict(slim(s), top_make=s["top_make"], share=s["top_make_share"]) for s in counties.values() if "top_make" in s and s["top_make"] != "FORD"],
        colour_areas={c: [dict(slim(s), share=s["colour_shares"][c]) for s in sorted([x for x in areas.values() if "colour_shares" in x], key=lambda s: -s["colour_shares"][c])[:5]] for c in COLOURS[:8]},
        top_colour_counts=collections.Counter(s["top_colour"] for s in areas.values() if "top_colour" in s),
        top_colour_counts_cty=collections.Counter(s["top_colour"] for s in counties.values() if "top_colour" in s),
        top_make_counts=collections.Counter(s["top_make"] for s in areas.values() if "top_make" in s),
        top_make_counts_cty=collections.Counter(s["top_make"] for s in counties.values() if "top_make" in s),
        top_model_counts=collections.Counter(s["top_model"] for s in areas.values() if "top_model" in s),
        top_model_counts_cty=collections.Counter(s["top_model"] for s in counties.values() if "top_model" in s),
    ),
    colour_trend=colour_trend, fuel_trend=fuel_trend, make_colour=make_colour,
    gb_models=[[k, v / GB["n"], fam_disp(k)] for k, v in car_fams(GB["fam"]).most_common(15)],
    gb_makes=[[m, v / GB["n"], make_name(m)] for m, v in GB["make"].most_common(15)],
    gb_colours=[[c, v / GB["n"]] for c, v in GB["colour"].most_common(12)],
    van_colours=[[c, v / sum(GB["vancol"].values())] for c, v in GB["vancol"].most_common(5)],
    first_use=dict(pre1960=sum(n for y, n in fy_all.items() if y < 1960), pre1980=sum(n for y, n in fy_all.items() if y < 1980),
                   y2005_or_older=sum(n for y, n in fy_all.items() if y <= 2005), total=sum(fy_all.values()),
                   modal_year=max(((y, n) for y, n in fy_all.items() if y <= 2022), key=lambda x: x[1])[0]),
    unplaced_dft=dict(unplaced), colour_hex=COLOUR_HEX,
)
# a few derived headline facts
R["gb"]["grey_rise"] = dict(y2000=colour_trend[2000].get("GREY", 0), y2010=colour_trend[2010].get("GREY", 0), y2022=colour_trend[2022].get("GREY", 0),
                             silver2000=colour_trend[2000].get("SILVER", 0), silver2022=colour_trend[2022].get("SILVER", 0))
R["gb"]["diesel_peak"] = max(((y, d.get("Diesel", 0)) for y, d in fuel_trend.items()), key=lambda x: x[1])
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, default=lambda o: dict(o) if isinstance(o, collections.Counter) else str(o))

# ---------- site units ----------
json.dump(dict(areas=areas, counties=counties, nations=nations, gb=gbs, ni=ni_unit, makes=MAKES_KEEP, colours=COLOURS,
               make_names={m: make_name(m) for m in set(MAKES_KEEP) | {s.get("top_make") for s in list(areas.values()) + list(counties.values()) if s.get("top_make")} | {s.get("sig_make") for s in list(areas.values()) + list(counties.values()) if s.get("sig_make")} | {m for m, _ in ni[0].most_common(10)}},
               model_names={k: fam_disp(k) for s in list(areas.values()) + list(counties.values()) + list(nations.values()) + [gbs] for k, _ in s.get("models", [])}),
          open(os.path.join(WORK, "site_units.json"), "w"), default=str)
print("GB cars", GB["n"], "top make", gbs["top_make"], round(gbs["top_make_share"], 4), "colour", gbs["top_colour"], round(gbs["top_colour_share"], 4), "model", gbs["top_model_name"])
for k, s in nations.items(): print(k, s["cars"], s["top_make"], round(s["top_make_share"], 3), s["top_colour"], round(s["top_colour_share"], 3), s["top_model_name"], round(s["age"], 2), round(s["bev_per100"], 2), s["sig_make"], round(s["sig_lq"], 2))
print("NI", ni_unit["dft_cars"], ni_unit["top_makes"][:3], ni_unit["top_models"][:3], round(ni_unit["bev_per100"], 2))
print("GB age", round(gbs["age"], 2), "cc", round(gbs["cc"]), "bev", round(gbs["bev_per100"], 2))

# ---------- flat facts for the text ----------
def pct(x): return x
F = {}
F["areas_ford"] = R["ranks"]["top_make_counts"].get("FORD", 0); F["areas_n"] = len([s for s in areas.values() if "top_make" in s])
F["counties_n_gb"] = len([s for s in counties.values() if "top_make" in s]); F["counties_ford"] = R["ranks"]["top_make_counts_cty"].get("FORD", 0)
for m in ("VAUXHALL", "VOLKSWAGEN", "TOYOTA", "MERCEDES-BENZ", "NISSAN"):
    F["areas_" + m.lower().replace("-", "")] = R["ranks"]["top_make_counts"].get(m, 0)
for c in ("BLACK", "WHITE", "BLUE", "GREY"):
    F["areas_col_" + c.lower()] = R["ranks"]["top_colour_counts"].get(c, 0); F["cty_col_" + c.lower()] = R["ranks"]["top_colour_counts_cty"].get(c, 0)
for k in ("FORD|FIESTA", "VAUXHALL|CORSA", "VOLKSWAGEN|GOLF", "TOYOTA|PRIUS"):
    F["areas_mod_" + k.split("|")[1].lower()] = R["ranks"]["top_model_counts"].get(k, 0)
for a in ("SR", "LU", "CH", "ZE", "NW", "E", "BT"):
    if a in areas and "make_shares" in areas[a]:
        s = areas[a]; F["a_" + a] = dict(name=s["name"], cars=s["cars"], top_make=make_name(s["top_make"]), top_make_share=s["top_make_share"],
                                         nissan=s["make_shares"].get("NISSAN", 0), vauxhall=s["make_shares"].get("VAUXHALL", 0), toyota=s["make_shares"].get("TOYOTA", 0),
                                         lexus=s["make_shares"].get("LEXUS", 0), top_model=s["top_model_name"], top_model_share=s["top_model_share"], age=s["age"])
for nat in ("England", "Scotland", "Wales"):
    s = nations[nat]
    F[nat] = dict(cars=s["cars"], top_make=make_name(s["top_make"]), top_make_share=s["top_make_share"], make2=make_name(s["make2"]), make2_share=s["make2_share"],
                  top_colour=s["top_colour"].lower(), top_colour_share=s["top_colour_share"], colour2=s["colour2"].lower(), colour2_share=s["colour2_share"],
                  top_model=s["top_model_name"], top_model_share=s["top_model_share"], age=s["age"], cc=s["cc"], bev=s["bev_per100"],
                  sig_make=make_name(s["sig_make"]), sig_lq=s["sig_lq"], diesel=s["fuel"]["Diesel"], electric=s["fuel"]["Electric"], hybrid=s["fuel"]["Hybrid"],
                  top_model_colour=s["top_model_colour"].lower(), black=s["colour_shares"]["BLACK"], white=s["colour_shares"]["WHITE"])
g = gbs
F["GB"] = dict(cars=g["cars"], top_make=make_name(g["top_make"]), top_make_share=g["top_make_share"], make2=make_name(g["make2"]), make2_share=g["make2_share"],
               top_colour=g["top_colour"].lower(), top_colour_share=g["top_colour_share"], colour2=g["colour2"].lower(), colour2_share=g["colour2_share"],
               top_model=g["top_model_name"], top_model_share=g["top_model_share"], age=g["age"], cc=g["cc"], bev=g["bev_per100"], old20=g["old20"],
               diesel=g["fuel"]["Diesel"], petrol=g["fuel"]["Petrol"], electric=g["fuel"]["Electric"], hybrid=g["fuel"]["Hybrid"], top_model_colour=g["top_model_colour"].lower(),
               fiesta_n=round(GB["fam"]["FORD|FIESTA"]), dft_diesel=gb_veh["fuels"].get("Diesel", 0), dft_bev=gb_veh["fuels"].get("Battery electric", 0))
F["NI"] = dict(cars=ni_unit["dft_cars"], bev=ni_unit["bev_per100"], diesel=ni_unit["fuels"].get("Diesel", 0), bev_share=ni_unit["fuels"].get("Battery electric", 0),
               m1=make_name(ni_unit["top_makes"][0][0]), m1s=ni_unit["top_makes"][0][1], m2=make_name(ni_unit["top_makes"][1][0]), m2s=ni_unit["top_makes"][1][1],
               m3=make_name(ni_unit["top_makes"][2][0]), m3s=ni_unit["top_makes"][2][1],
               mod1=fam_name(*ni_unit["top_models"][0][0].split("|")), mod1s=ni_unit["top_models"][0][1], mod2=fam_name(*ni_unit["top_models"][1][0].split("|")), mod2s=ni_unit["top_models"][1][1],
               gb_dft_m1=make_name(gb_veh["top_makes"][0][0]), gb_dft_m1s=gb_veh["top_makes"][0][1], gb_vw=dict(gb_veh["top_makes"]).get("VOLKSWAGEN", 0),
               gb_audi=dict(gb_veh["top_makes"]).get("AUDI", 0))
F["uk_bev"] = R["uk"]["bev_per100"]
F["grey2000"], F["grey2022"], F["silver2000"], F["silver2022"] = colour_trend[2000]["GREY"], colour_trend[2022]["GREY"], colour_trend[2000]["SILVER"], colour_trend[2022]["SILVER"]
F["diesel_peak_year"], F["diesel_peak_share"] = R["gb"]["diesel_peak"]
F["diesel2022"] = fuel_trend[2022].get("Diesel", 0); F["ev2022"] = fuel_trend[2022].get("Electric", 0); F["hy2022"] = fuel_trend[2022].get("Hybrid", 0)
F["van_white"] = R["van_colours"][0][1]
uk_ranks = R["ranks"]
F["bev_top"] = uk_ranks["bev_counties"][:5]; F["bev_low"] = uk_ranks["bev_low_counties"][:5]
gbonly = [s for s in uk_ranks["bev_low_counties"] if s["nation"] != "Northern Ireland"]
F["bev_low_gb"] = sorted([dict(name=s["name"], nation=s["nation"], bev=s["bev_per100"]) for s in counties.values() if not s.get("ni") and s.get("bev_per100") is not None], key=lambda x: x["bev"])[:5]
F["old_cty"] = uk_ranks["oldest_counties"][:5]; F["young_cty"] = uk_ranks["youngest_counties"][:5]
F["old_area"] = uk_ranks["oldest_areas"][:5]; F["young_area"] = uk_ranks["youngest_areas"][:5]
F["unusual"] = {nat: [dict(name=x["name"], dissim=x["dissim"], sig=make_name(x["sig_make"]), lq=x["sig_lq"], share=x["sig_share"], nshare=x["sig_nat_share"]) for x in L[:3]] for nat, L in uk_ranks["unusual"].items()}
F["unusual_area"] = [dict(code=x["code"], name=x["name"], dissim=x["dissim"], sig=make_name(x["sig_make"]), lq=x["sig_lq"], share=x["sig_share"]) for x in uk_ranks["unusual_areas"][:5]]
F["pre1980"] = R["first_use"]["pre1980"]; F["pre1960"] = R["first_use"]["pre1960"]; F["modal_year"] = R["first_use"]["modal_year"]
F["cc_top"] = uk_ranks["cc_areas"][:3]; F["cc_low"] = uk_ranks["cc_low_areas"][:3]
F["diesel_top"] = uk_ranks["diesel_areas"][:3]
F["ev_mot_top"] = uk_ranks["mot_ev_areas"][:3]
F["bev_scot"] = sorted([dict(name=s["name"], bev=s["bev_per100"]) for s in counties.values() if s["nation"] == "Scotland" and s.get("bev_per100") is not None], key=lambda x: -x["bev"])[:3]
F["bev_wales"] = sorted([dict(name=s["name"], bev=s["bev_per100"]) for s in counties.values() if s["nation"] == "Wales" and s.get("bev_per100") is not None], key=lambda x: -x["bev"])[:3]
F["bev_ni"] = sorted([dict(name=s["name"], bev=s["bev_per100"]) for s in counties.values() if s["nation"] == "Northern Ireland"], key=lambda x: -x["bev"])[:3]
_ds = sorted(x["dissim"] for x in counties.values() if "dissim" in x)
F["dissim_median"] = _ds[len(_ds) // 2]; F["dissim_lt10"] = sum(x < 0.10 for x in _ds) / len(_ds); F["dissim_n"] = len(_ds)
F["six_colours"] = sum(v for c, v in R["gb_colours"][:6])
F["bev_low_gb2"] = F["bev_low_gb"][1]
F["bev_scot_shet"] = counties["S12000027"]["bev_per100"]
assert counties["S12000027"]["name"] == "Shetland Islands"
R["facts"] = F
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, default=lambda o: dict(o) if isinstance(o, collections.Counter) else str(o))
print(json.dumps({k: v for k, v in F.items() if k not in ("unusual",)}, default=str)[:6000])
print(F["unusual"])
