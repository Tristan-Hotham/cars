"""Step 7. Release files: release/blog/post.html and meta.json, release/zenodo/ (PDF, key CSVs, code and data zip, meta.json).
Run: python3 code/07_release.py (after steps 1 to 6)
"""
import json, os, re, shutil, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
src = open(os.path.join(HERE, "04_build_site.py")).read().split("# ---- facts the template")[0]
ns = {"__file__": os.path.join(HERE, "04_build_site.py")}; exec(compile(src, "b", "exec"), ns)
R, get, fmt, TOK = ns["R"], ns["get"], ns["fmt"], ns["TOK"]
sub = lambda m: m.group(0) if m.group(1).startswith("IMG") else fmt(get(m.group(1)), m.group(3))
rd = re.sub(TOK, lambda m: fmt(get(m.group(1)), m.group(3)), open(os.path.join(HERE, "readme_template.md"), encoding="utf-8").read())
for bad in ("\u2014", "\u2013", "--"): assert bad not in rd, bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(rd)
BLOG = os.path.join(ROOT, "release", "blog"); ZEN = os.path.join(ROOT, "release", "zenodo"); os.makedirs(ZEN, exist_ok=True)
post = re.sub(TOK, sub, open(os.path.join(HERE, "blog_template.html"), encoding="utf-8").read())
for img in re.findall(r"\{\{IMG\|([^|]+)\|", post): assert os.path.exists(os.path.join(BLOG, img)), img
vis = re.sub(r"<[^>]+>", " ", re.sub(r"<!--.*?-->", "", post, flags=re.S))
for bad in ("—", "–", "--"): assert bad not in vis, bad
open(os.path.join(BLOG, "post.html"), "w", encoding="utf-8").write(post)
F = R["facts"]
meta = {"title": "What Britain drives: makes, models and colours, county by county",
        "slug": "cars",
        "excerpt": f"I read all {R['meta']['rows']:,} MOT tests from 2025 to map the most popular car makes, models and colours in every county and postcode area. The average British car is a blue Ford Fiesta, Scotland prefers white, and Shetland loves Toyotas.",
        "seo_description": "The most popular car makes, models and colours by county and postcode area, from every 2025 MOT test, with electric cars across the UK.",
        "tags": ["cars", "MOT", "electric vehicles", "maps", "data", "Great Britain", "Northern Ireland", "open data"],
        "header_alt": f"Title card reading 'What Britain drives' in black on a pale paper background, beside a map of Britain's postcode areas coloured by most common car make: almost all Ford blue, with Vauxhall red around Glasgow and Dundee, Volkswagen teal near London and Toyota orange in Shetland, and Northern Ireland in grey. Text: the average car is a blue Ford Fiesta, {F['GB']['age']:.1f} years old."}
json.dump(meta, open(os.path.join(BLOG, "meta.json"), "w"), indent=2, ensure_ascii=False)
for v in meta.values():
    for bad in ("—", "–", "--"): assert bad not in str(v)
# zenodo
PDF = "Hotham_What_Britain_Drives.pdf"
shutil.copy(os.path.join(ROOT, "release", PDF), os.path.join(ZEN, PDF))
for f in ["postcode_areas.csv", "counties.csv", "nations.csv", "area_make_counts.csv", "area_model_counts.csv", "area_colour_fuel_counts.csv", "gb_colour_by_year.csv", "area_county_weights.csv"]:
    shutil.copy(os.path.join(ROOT, "data", f), os.path.join(ZEN, f))
with zipfile.ZipFile(os.path.join(ZEN, "cars_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, d))):
            p = os.path.join(ROOT, d, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): z.write(p, f"{d}/{f}")
    for f in ("README.md", "LICENSE"): z.write(os.path.join(ROOT, f), f)
abstract = open(os.path.join(ROOT, "release", "paper", "Hotham_What_Britain_Drives.tex")).read().split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
abstract = abstract.replace("\\%", "%").replace("\\&", "&").replace("\\_", "_")
zmeta = {"title": "What Britain Drives: Car Makes, Models, Colours and Ages by County and Postcode Area from the 2025 MOT Record",
         "description_html": f"<p>{abstract}</p><p>Interactive version: https://maps.tristanhotham.com/cars/. Data and code: https://github.com/Tristan-Hotham/cars. Blog post: to follow.</p>",
         "keywords": ["cars", "MOT test", "vehicle licensing", "car colour", "electric vehicles", "postcode areas", "counties", "Great Britain", "Northern Ireland", "open data"],
         "licence": "cc-by-4.0",
         "licence_note": "Text and figures CC BY 4.0; data files are derived from DVSA, DfT, ONS and OS data under the Open Government Licence v3.0; code MIT.",
         "related": [{"identifier": "https://github.com/Tristan-Hotham/cars", "relation": "issupplementedby", "resource_type": "software"},
                     {"identifier": "https://maps.tristanhotham.com/cars/", "relation": "issupplementedby", "resource_type": "other"},
                     {"identifier": "https://open.data.dvsa.gov.uk/mot-anonymised/index.html", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://www.gov.uk/government/statistical-data-sets/vehicle-licensing-statistics-data-files", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://geoportal.statistics.gov.uk/", "relation": "isderivedfrom", "resource_type": "dataset"}]}
json.dump(zmeta, open(os.path.join(ZEN, "meta.json"), "w"), indent=2, ensure_ascii=False)
assert "—" not in json.dumps(zmeta, ensure_ascii=False) and "–" not in json.dumps(zmeta, ensure_ascii=False) and "--" not in zmeta["description_html"]
print("words in post", len(vis.split()))
