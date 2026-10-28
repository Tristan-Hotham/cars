"""Step 2. Geography: postcode areas, counties and unitary authorities, and the weights that link them.

Inputs (gathered in the browser, see README):
  cars_onspd_geo.json.gz  ONS Postcode Directory (August 2026), live small-user postcodes counted by
                          postcode area x LSOA (data zone in Scotland, SDZ in Northern Ireland) x local authority,
                          with the mean grid reference of each group; plus the LAD to CTYUA lookup (May 2026)
                          and Counties and Unitary Authorities (December 2025) ultra generalised boundaries.
Outputs:
  data/area_county_weights.csv  share of each postcode area's live postcodes in each county or UA
  data/lsoa_county.csv          LSOA (or data zone / SDZ) to county or UA, for the DfT licensing tables
  work/counties_bng.json        county polygons (BNG) for figures
  data/counties.geojson         county polygons (WGS84, simplified) for the page
  data/postcode_areas.geojson   approximate postcode areas: Voronoi cells around the postcode group
                                centroids, merged by area and clipped to the land
Run: python3 code/02_geo.py
"""
import json, csv, os, collections
import numpy as np
from shapely.geometry import shape, mapping, Polygon, MultiPolygon, box
from shapely.ops import unary_union, transform
from scipy.spatial import Voronoi
from pyproj import Transformer
from common import load_gz, DATA, WORK

G = load_gz("cars_onspd_geo.json.gz")
rows = G["rows"]          # [area, lsoa, lad, cty, ctry, n, e, n]
LK = {r["LAD26CD"]: r for r in G["lookup"]}

# Northern Ireland grid references in the ONSPD are on the Irish Grid
ig2bng = Transformer.from_crs("EPSG:29903", "EPSG:27700", always_xy=True)
bng2wgs = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
wgs2bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

pts = []
w_area_cty = collections.defaultdict(float)
lsoa_cty = {}
unmatched = 0
for a, lsoa, lad, cty, ctry, n, e, no in rows:
    if lad is None or e is None:
        unmatched += n; continue
    lk = LK.get(lad)
    if lk is None:
        unmatched += n; continue
    if ctry == "N92000002":
        e, no = ig2bng.transform(e, no)
    pts.append((a, e, no, n))
    w_area_cty[(a, lk["CTYUA26CD"])] += n
    if lsoa: lsoa_cty[lsoa] = lk["CTYUA26CD"]
print("groups", len(pts), "postcodes", sum(p[3] for p in pts), "unmatched", unmatched)

CTY = {}
for lk in LK.values():
    CTY[lk["CTYUA26CD"]] = dict(name=lk["CTYUA26NM"], region=lk["RGN26NM"], nation=lk["CTRY26NM"])

tot = collections.defaultdict(float)
for (a, c), n in w_area_cty.items(): tot[a] += n
with open(os.path.join(DATA, "area_county_weights.csv"), "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["postcode_area", "ctyua_code", "ctyua_name", "nation", "live_postcodes", "share_of_area"])
    for (a, c), n in sorted(w_area_cty.items()):
        wr.writerow([a, c, CTY[c]["name"], CTY[c]["nation"], int(n), round(n / tot[a], 5)])
with open(os.path.join(DATA, "lsoa_county.csv"), "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["lsoa_code", "ctyua_code"])
    for k, v in sorted(lsoa_cty.items()): wr.writerow([k, v])

# counties: BNG polygons
cgeo = G["counties"]["features"]
cpoly = {}
for ft in cgeo:
    g = shape(ft["geometry"])
    g = transform(lambda x, y, z=None: wgs2bng.transform(x, y), g).buffer(0)
    cpoly[ft["properties"]["CTYUA25CD"]] = g
missing = set(CTY) - set(cpoly)
print("counties with polygons", len(cpoly), "lookup codes without polygon", missing)
land = unary_union(list(cpoly.values())).buffer(0)

# Voronoi of postcode-group centroids (jitter duplicates), merged by postcode area
P = np.array([[p[1], p[2]] for p in pts], float)
P += np.random.default_rng(1).normal(0, 1.0, P.shape)
lab = [p[0] for p in pts]
far = np.array([[-2e6, -2e6], [-2e6, 4e6], [3e6, -2e6], [3e6, 4e6]])
vor = Voronoi(np.vstack([P, far]))
cells = collections.defaultdict(list)
for i, reg_i in enumerate(vor.point_region[:len(P)]):
    reg = vor.regions[reg_i]
    if -1 in reg or not reg: continue
    cells[lab[i]].append(Polygon(vor.vertices[reg]))
areas = {}
for a, cs in cells.items():
    g = unary_union(cs).buffer(0).intersection(land)
    areas[a] = g
print("postcode areas", len(areas))


def to_wgs(g, tol):
    g = g.simplify(tol, preserve_topology=True)
    g = transform(lambda x, y, z=None: bng2wgs.transform(x, y), g)
    def rnd(o):
        if isinstance(o, (list, tuple)):
            if o and isinstance(o[0], float): return [round(o[0], 4), round(o[1], 4)]
            return [rnd(x) for x in o]
        return o
    m = mapping(g); m = {"type": m["type"], "coordinates": rnd(m["coordinates"])}
    return m


def drop_slivers(g, minarea=2e6):
    if isinstance(g, MultiPolygon):
        keep = [p for p in g.geoms if p.area >= minarea]
        return MultiPolygon(keep) if keep else g
    return g


feats = []
for a, g in sorted(areas.items()):
    g = drop_slivers(g)
    c = g.representative_point()
    lon, lat = bng2wgs.transform(c.x, c.y)
    feats.append({"type": "Feature", "properties": {"id": a, "lon": round(lon, 4), "lat": round(lat, 4)}, "geometry": to_wgs(g, 400)})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(DATA, "postcode_areas.geojson"), "w"), separators=(",", ":"))
feats = []
for c, g in sorted(cpoly.items()):
    p = g.representative_point(); lon, lat = bng2wgs.transform(p.x, p.y)
    feats.append({"type": "Feature", "properties": {"id": c, "lon": round(lon, 4), "lat": round(lat, 4)}, "geometry": to_wgs(g, 250)})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(DATA, "counties.geojson"), "w"), separators=(",", ":"))
# BNG copies for the static figures
json.dump({"counties": {c: mapping(g.simplify(300)) for c, g in cpoly.items()},
           "areas": {a: mapping(drop_slivers(g).simplify(300)) for a, g in areas.items()},
           "names": CTY}, open(os.path.join(WORK, "geo_bng.json"), "w"))
json.dump(CTY, open(os.path.join(WORK, "counties_meta.json"), "w"), indent=0)
print("done")
