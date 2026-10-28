"""Shared helpers: paths, model-family normalisation, fuel groups, van list, postcode area names."""
import os, re, gzip, json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = "/home/claude/hist/_data18/cars"
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(ROOT, "work")
os.makedirs(DATA, exist_ok=True); os.makedirs(WORK, exist_ok=True)

def load_gz(name):
    return json.load(gzip.open(os.path.join(RAW, name)))

# MOT fuel codes (DVSA user guide) grouped for the page
FUEL_GROUP = {"PE": "Petrol", "DI": "Diesel", "HY": "Hybrid", "HYBRID ELECTRIC (CLEAN)": "Hybrid", "ED": "Hybrid",
              "EL": "Electric", "ELECTRIC": "Electric"}
def fuel_group(code):
    return FUEL_GROUP.get(code, "Other")

TWO = {("TRANSIT", "CUSTOM"), ("TRANSIT", "CONNECT"), ("TRANSIT", "COURIER"), ("TOURNEO", "CONNECT"), ("TOURNEO", "CUSTOM"),
       ("DISCOVERY", "SPORT"), ("GRAND", "C-MAX"), ("GRAND", "SCENIC"), ("GRAND", "C4"), ("C4", "PICASSO"), ("C4", "CACTUS"),
       ("C3", "AIRCROSS"), ("C5", "AIRCROSS"), ("MODEL", "3"), ("MODEL", "Y"), ("MODEL", "S"), ("MODEL", "X"), ("ID.3",), ("UP",),
       ("SANTA", "FE"), ("ZAFIRA", "TOURER"), ("CROSSLAND", "X"), ("GRANDLAND", "X"), ("GRAND", "VITARA"), ("IONIQ", "5"),
       ("SPACE", "STAR"), ("PUNTO", "EVO"), ("GRANDE", "PUNTO"), ("NEW", "BEETLE"), ("POLO", "VIVO"), ("CEED",), ("XCEED",)}
MINI_HATCH = {"COOPER", "ONE", "MINI", "JOHN", "COOPERS"}

def model_family(make, model):
    t = model.replace("-", "-").split()
    if not t: return "UNKNOWN"
    if make == "MINI" and t[0] in MINI_HATCH: return "HATCH"
    if make == "LAND ROVER" and t[0] == "RANGE":
        if len(t) > 2 and t[2] in ("SPORT", "EVOQUE", "VELAR"): return "RANGE ROVER " + t[2]
        return "RANGE ROVER"
    if len(t) > 1 and (t[0].isdigit() and t[1] == "SERIES"): return t[0] + " SERIES"
    if len(t) > 1 and (t[0], t[1]) in TWO: return t[0] + " " + t[1]
    if make == "MERCEDES-BENZ":
        m = re.match(r"^([A-Z]{1,3})(-CLASS|\d{2,3}\w*)?$", t[0])
        if m and m.group(1) in ("A", "B", "C", "E", "S", "CLA", "CLS", "GLA", "GLB", "GLC", "GLE", "GL", "ML", "SLK", "SL", "CLK", "V", "G", "R", "M"):
            return m.group(1) + "-CLASS"
    if make == "BMW":
        m = re.match(r"^(\d)\d\d\w*$", t[0])
        if m: return m.group(1) + " SERIES"
    if make == "AUDI":
        m = re.match(r"^(A\d|Q\d|TT|S\d|RS\d)", t[0])
        if m: return m.group(1)
    return t[0]

# MOT class 4 also covers light goods vehicles: these families are vans or pick-ups, left out of "car" model rankings
VANS = {("FORD", "TRANSIT"), ("FORD", "TRANSIT CUSTOM"), ("FORD", "TRANSIT CONNECT"), ("FORD", "TRANSIT COURIER"), ("FORD", "RANGER"),
        ("VOLKSWAGEN", "TRANSPORTER"), ("VOLKSWAGEN", "CADDY"), ("VOLKSWAGEN", "CRAFTER"), ("VOLKSWAGEN", "AMAROK"),
        ("CITROEN", "BERLINGO"), ("CITROEN", "DISPATCH"), ("CITROEN", "RELAY"), ("CITROEN", "NEMO"),
        ("PEUGEOT", "PARTNER"), ("PEUGEOT", "EXPERT"), ("PEUGEOT", "BOXER"), ("PEUGEOT", "BIPPER"),
        ("VAUXHALL", "VIVARO"), ("VAUXHALL", "COMBO"), ("VAUXHALL", "MOVANO"),
        ("RENAULT", "TRAFIC"), ("RENAULT", "KANGOO"), ("RENAULT", "MASTER"),
        ("MERCEDES-BENZ", "VITO"), ("MERCEDES-BENZ", "SPRINTER"), ("MERCEDES-BENZ", "CITAN"), ("MERCEDES-BENZ", "X-CLASS"),
        ("NISSAN", "NAVARA"), ("NISSAN", "NV200"), ("NISSAN", "NV300"), ("NISSAN", "NV400"), ("NISSAN", "PRIMASTAR"), ("NISSAN", "E-NV200"),
        ("MITSUBISHI", "L200"), ("TOYOTA", "HILUX"), ("TOYOTA", "PROACE"), ("TOYOTA", "HIACE"), ("ISUZU", "D-MAX"), ("ISUZU", "RODEO"),
        ("FIAT", "DUCATO"), ("FIAT", "DOBLO"), ("FIAT", "SCUDO"), ("FIAT", "FIORINO"), ("FIAT", "TALENTO"),
        ("LAND ROVER", "DEFENDER"), ("IVECO", "DAILY"), ("LDV", "V80"), ("MAXUS", "DELIVER"), ("SSANGYONG", "MUSSO")}
def is_van(make, fam):
    return (make, fam) in VANS or make in ("IVECO", "LDV", "MAXUS", "LEVC")

# postcode areas, named after their main post town (Royal Mail convention)
AREA_NAME = dict(x.split(":") for x in """AB:Aberdeen,AL:St Albans,B:Birmingham,BA:Bath,BB:Blackburn,BD:Bradford,BH:Bournemouth,BL:Bolton,BN:Brighton,BR:Bromley,BS:Bristol,BT:Belfast,CA:Carlisle,CB:Cambridge,CF:Cardiff,CH:Chester,CM:Chelmsford,CO:Colchester,CR:Croydon,CT:Canterbury,CV:Coventry,CW:Crewe,DA:Dartford,DD:Dundee,DE:Derby,DG:Dumfries,DH:Durham,DL:Darlington,DN:Doncaster,DT:Dorchester,DY:Dudley,E:London E,EC:London EC,EH:Edinburgh,EN:Enfield,EX:Exeter,FK:Falkirk,FY:Blackpool,G:Glasgow,GL:Gloucester,GU:Guildford,HA:Harrow,HD:Huddersfield,HG:Harrogate,HP:Hemel Hempstead,HR:Hereford,HS:Outer Hebrides,HU:Hull,HX:Halifax,IG:Ilford,IP:Ipswich,IV:Inverness,KA:Kilmarnock,KT:Kingston upon Thames,KW:Kirkwall,KY:Kirkcaldy,L:Liverpool,LA:Lancaster,LD:Llandrindod Wells,LE:Leicester,LL:Llandudno,LN:Lincoln,LS:Leeds,LU:Luton,M:Manchester,ME:Medway,MK:Milton Keynes,ML:Motherwell,N:London N,NE:Newcastle upon Tyne,NG:Nottingham,NN:Northampton,NP:Newport,NR:Norwich,NW:London NW,OL:Oldham,OX:Oxford,PA:Paisley,PE:Peterborough,PH:Perth,PL:Plymouth,PO:Portsmouth,PR:Preston,RG:Reading,RH:Redhill,RM:Romford,S:Sheffield,SA:Swansea,SE:London SE,SG:Stevenage,SK:Stockport,SL:Slough,SM:Sutton,SN:Swindon,SO:Southampton,SP:Salisbury,SR:Sunderland,SS:Southend-on-Sea,ST:Stoke-on-Trent,SW:London SW,SY:Shrewsbury,TA:Taunton,TD:Galashiels,TF:Telford,TN:Tonbridge,TQ:Torquay,TR:Truro,TS:Cleveland,TW:Twickenham,UB:Southall,W:London W,WA:Warrington,WC:London WC,WD:Watford,WF:Wakefield,WN:Wigan,WR:Worcester,WS:Walsall,WV:Wolverhampton,YO:York,ZE:Lerwick""".split(","))

def title(s):
    """Make names readable: FORD -> Ford, but keep short acronyms (BMW, MG, DS) upper case."""
    KEEP = {"BMW", "MG", "DS", "BYD", "LDV", "LEVC", "SEAT", "GWM", "TVR"}
    out = []
    for w in s.split():
        if w in KEEP or (len(w) <= 3 and any(c.isdigit() for c in w)) or re.match(r"^[A-Z]{1,2}\d", w) or re.match(r"^\d", w) or w in ("CR-V", "HR-V", "CX-5", "CX-3", "MX-5", "RAV4", "XC90", "XC60", "XC40", "GTI", "ID.3"):
            out.append("SEAT" if w == "SEAT" else w)
        else:
            out.append("-".join(p.capitalize() for p in w.split("-")))
    return " ".join(out).replace("Seat", "SEAT")
