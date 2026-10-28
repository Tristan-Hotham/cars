"""Step 6. Build the paper PDF: fill code/paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_What_Britain_Drives.tex and compile it with xelatex (figures from step 5).
Run: python3 code/06_paper.py
"""
import importlib.util, json, os, re, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py"))
# reuse get/fmt without rebuilding the site
src = open(os.path.join(HERE, "04_build_site.py")).read().split("# ---- facts the template")[0]
b = type("B", (), {})(); ns = {"__file__": os.path.join(HERE, "04_build_site.py")}; exec(compile(src, "b", "exec"), ns)
R, get, fmt = ns["R"], ns["get"], ns["fmt"]
U = json.load(open(os.path.join(ROOT, "data", "units.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_What_Britain_Drives"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
sub = lambda m: tex(fmt(get(m.group(1)), m.group(3)))
mk = lambda m: U["make_names"].get(m, m)
md = lambda k: U["model_names"].get(k, k)
F = R["facts"]

# Table 1: nations
cols = [("England", F["England"]), ("Scotland", F["Scotland"]), ("Wales", F["Wales"]), ("Great Britain", F["GB"])]
p1 = lambda x: f"{x * 100:.1f}\\%"
rows = [("Cars tested (MOT 2025)", [f"{c['cars']:,}" for _, c in cols] + [""]),
        ("Licensed cars (DfT, end 2025)", [f"{R['nations'][n]['dft_cars']:,}" for n in ("England", "Scotland", "Wales")] + [f"{R['gb']['dft_cars']:,}", f"{F['NI']['cars']:,}"]),
        ("Top make", [f"{c['top_make']} {p1(c['top_make_share'])}" for _, c in cols] + [f"{F['NI']['m1']} {p1(F['NI']['m1s'])}"]),
        ("Second make", [f"{c['make2']} {p1(c['make2_share'])}" for _, c in cols] + [f"{F['NI']['m2']} {p1(F['NI']['m2s'])}"]),
        ("Top model", [f"{c['top_model']}" for _, c in cols] + [F["NI"]["mod1"]]),
        ("Top colour", [f"{c['top_colour'].capitalize()} {p1(c['top_colour_share'])}" for _, c in cols] + ["n/a"]),
        ("Mean age (years)", [f"{c['age']:.1f}" for _, c in cols] + ["n/a"]),
        ("Mean engine (cc)", [f"{c['cc']:,.0f}" for _, c in cols] + ["n/a"]),
        ("Diesel (tested cars)", [p1(c["diesel"]) for _, c in cols] + [""]),
        ("Diesel (licensed cars)", ["", "", "", p1(F["GB"]["dft_diesel"]), p1(F["NI"]["diesel"])]),
        ("Battery electric per 100", [f"{c['bev']:.2f}" for _, c in cols] + [f"{F['NI']['bev']:.2f}"])]
body = "".join(tex(r[0]) + " & " + " & ".join(r[1]) + "\\\\\n" for r in rows)
T1 = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The nations. MOT rows: cars tested in 2025. Northern Ireland: DfT licensed cars (VEH0120, UK minus Great Britain). "
      "Battery electric per 100: DfT VEH0145 and VEH0125, private keepers, end of 2025.}\\label{tab:nat}\\setlength{\\tabcolsep}{4pt}"
      "\\begin{tabular}{>{\\raggedright\\arraybackslash}p{3.1cm}>{\\raggedright\\arraybackslash}p{2.35cm}>{\\raggedright\\arraybackslash}p{2.35cm}>{\\raggedright\\arraybackslash}p{2.35cm}>{\\raggedright\\arraybackslash}p{2.35cm}>{\\raggedright\\arraybackslash}p{2.35cm}}\\toprule & England & Scotland & Wales & Great Britain & N. Ireland\\\\\\midrule\n" + body + "\\bottomrule\\end{tabular}\\end{table}")

# Table 2: unusual counties
body = ""
for nat in ("England", "Scotland", "Wales"):
    for x in R["ranks"]["unusual"][nat][:3]:
        body += f"{nat} & {tex(x['name'])} & {x['dissim']:.3f} & {tex(mk(x['sig_make']))} & {x['sig_lq']:.1f} & {p1(x['sig_share'])} \\\\\n"
T2 = ("\\begin{table}[tbp]\\centering\\small\\caption{The three most unusual counties and unitary authorities in each nation (dissimilarity of make shares from the nation's), with the most over-represented make, its ratio to the national share and its local share. Places with at least 15,000 tested cars.}\\label{tab:odd}"
      "\\begin{tabular}{llrlrr}\\toprule Nation & Place & Dissim. & Stands out & Ratio & Share\\\\\\midrule\n" + body + "\\bottomrule\\end{tabular}\\end{table}")

# Table 3: electric
top, low = R["ranks"]["bev_counties"][:8], R["ranks"]["bev_low_counties"][:8]
body = "".join(f"{tex(a['name'])} & {a['bev']:.2f} & {tex(c['name'])} & {c['bev']:.2f}\\\\\n" for a, c in zip(top, low))
T3 = ("\\begin{table}[tbp]\\centering\\small\\caption{Battery electric vehicles per 100 privately kept licensed cars, end of 2025: the eight highest and lowest counties and unitary authorities of the United Kingdom (DfT VEH0145 and VEH0125).}\\label{tab:bev}"
      "\\begin{tabular}{lrlr}\\toprule Highest & Per 100 & Lowest & Per 100\\\\\\midrule\n" + body + "\\bottomrule\\end{tabular}\\end{table}")

t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", sub, t).replace("{{TABLE_NAT}}", T1).replace("{{TABLE_ODD}}", T2).replace("{{TABLE_BEV}}", T3)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print(r.stdout[-600:] if r.returncode else "compiled")
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
txt = subprocess.run(["pdftotext", os.path.join(ROOT, "release", NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
print("words", len(txt.split()), "dashes", txt.count("—") + txt.count("–") + txt.count("--"))
