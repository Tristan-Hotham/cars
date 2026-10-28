/* Step 1. Gather the data in a web browser (run in the browser console; nothing large is stored).
   The three jobs below are the scripts used on 28 October 2026. Each keeps only aggregates, which were saved as
   gzipped JSON bundles: cars_mot2025_v2.json.gz, cars_onspd_geo.json.gz and cars_dft_veh.json.gz.
   Model-family and van rules are the same as in code/common.py.

   A. DVSA MOT 2025 results extract. Run on a page of the bucket's own origin
      (https://s3.eu-west-1.amazonaws.com/edh-dvsa-data-gov-uk-files-prod/) so range requests are same-origin.
      The archive (4.8 GB) holds twelve monthly CSVs stored without compression; the script reads the ZIP
      central directory from the end of the file, then streams each month with HTTP Range requests, December first,
      and counts each vehicle_id once (a bitset of ids already seen), test class 4 only. */
const TWO = new Set(["TRANSIT CUSTOM", "TRANSIT CONNECT", "TRANSIT COURIER", "TOURNEO CONNECT", "TOURNEO CUSTOM", "DISCOVERY SPORT", "GRAND C-MAX", "GRAND SCENIC", "GRAND C4", "C4 PICASSO", "C4 CACTUS", "C3 AIRCROSS", "C5 AIRCROSS", "MODEL 3", "MODEL Y", "MODEL S", "MODEL X", "SANTA FE", "ZAFIRA TOURER", "CROSSLAND X", "GRANDLAND X", "GRAND VITARA", "IONIQ 5", "SPACE STAR", "PUNTO EVO", "GRANDE PUNTO", "NEW BEETLE", "POLO VIVO"]);
const MINI_HATCH = new Set(["COOPER", "ONE", "MINI", "JOHN", "COOPERS"]);
const MB = new Set(["A", "B", "C", "E", "S", "CLA", "CLS", "GLA", "GLB", "GLC", "GLE", "GL", "ML", "SLK", "SL", "CLK", "V", "G", "R", "M"]);
function fam(make, model) {
  const t = model.split(/\s+/).filter(x => x); if (!t.length) return "UNKNOWN";
  if (make === "MINI" && MINI_HATCH.has(t[0])) return "HATCH";
  if (make === "LAND ROVER" && t[0] === "RANGE") { if (t.length > 2 && ["SPORT", "EVOQUE", "VELAR"].includes(t[2])) return "RANGE ROVER " + t[2]; return "RANGE ROVER"; }
  if (t.length > 1 && /^\d+$/.test(t[0]) && t[1] === "SERIES") return t[0] + " SERIES";
  if (t.length > 1 && TWO.has(t[0] + " " + t[1])) return t[0] + " " + t[1];
  if (make === "MERCEDES-BENZ") { const m = t[0].match(/^([A-Z]{1,3})(-CLASS|\d{2,3}\w*)?$/); if (m && MB.has(m[1])) return m[1] + "-CLASS"; }
  if (make === "BMW") { const m = t[0].match(/^(\d)\d\d\w*$/); if (m) return m[1] + " SERIES"; }
  if (make === "AUDI") { const m = t[0].match(/^(A\d|Q\d|TT|S\d|RS\d)/); if (m) return m[1]; }
  return t[0];
}
const VANS = new Set(["FORD|TRANSIT", "FORD|TRANSIT CUSTOM", "FORD|TRANSIT CONNECT", "FORD|TRANSIT COURIER", "FORD|RANGER", "VOLKSWAGEN|TRANSPORTER", "VOLKSWAGEN|CADDY", "VOLKSWAGEN|CRAFTER", "VOLKSWAGEN|AMAROK", "CITROEN|BERLINGO", "CITROEN|DISPATCH", "CITROEN|RELAY", "CITROEN|NEMO", "PEUGEOT|PARTNER", "PEUGEOT|EXPERT", "PEUGEOT|BOXER", "PEUGEOT|BIPPER", "VAUXHALL|VIVARO", "VAUXHALL|COMBO", "VAUXHALL|MOVANO", "RENAULT|TRAFIC", "RENAULT|KANGOO", "RENAULT|MASTER", "MERCEDES-BENZ|VITO", "MERCEDES-BENZ|SPRINTER", "MERCEDES-BENZ|CITAN", "MERCEDES-BENZ|X-CLASS", "NISSAN|NAVARA", "NISSAN|NV200", "NISSAN|NV300", "NISSAN|NV400", "NISSAN|PRIMASTAR", "NISSAN|E-NV200", "MITSUBISHI|L200", "TOYOTA|HILUX", "TOYOTA|PROACE", "TOYOTA|HIACE", "ISUZU|D-MAX", "ISUZU|RODEO", "FIAT|DUCATO", "FIAT|DOBLO", "FIAT|SCUDO", "FIAT|FIORINO", "FIAT|TALENTO", "LAND ROVER|DEFENDER", "IVECO|DAILY", "LDV|V80", "MAXUS|DELIVER", "SSANGYONG|MUSSO"]);
const VANMAKE = new Set(["IVECO", "LDV", "MAXUS", "LEVC"]);

async function gatherMOT() {
  const U = "https://s3.eu-west-1.amazonaws.com/edh-dvsa-data-gov-uk-files-prod/dft_test_result_extracts_2025.zip", SIZE = 4835709507;
  // central directory (ZIP64)
  const b = new Uint8Array(await (await fetch(U, { headers: { Range: `bytes=${SIZE - 65536}-${SIZE - 1}` } })).arrayBuffer()), dv = new DataView(b.buffer);
  let i = b.length - 22; while (dv.getUint32(i, true) !== 0x06054b50) i--;
  let j = i; while (j > 0 && dv.getUint32(j, true) !== 0x06064b50) j--;
  const n = Number(dv.getBigUint64(j + 32, true)), cdOff = Number(dv.getBigUint64(j + 48, true));
  let p = cdOff - (SIZE - 65536); const ents = [];
  for (let k = 0; k < n; k++) {
    let usz = dv.getUint32(p + 24, true), lho = dv.getUint32(p + 42, true); const nl = dv.getUint16(p + 28, true), el = dv.getUint16(p + 30, true), cl = dv.getUint16(p + 32, true);
    let q = p + 46 + nl; const qe = q + el;
    while (q < qe) { const id = dv.getUint16(q, true), sz = dv.getUint16(q + 2, true); if (id === 1) { let r = q + 4; if (usz === 0xffffffff) { usz = Number(dv.getBigUint64(r, true)); r += 8; } r += 8; if (lho === 0xffffffff) lho = Number(dv.getBigUint64(r, true)); } q += 4 + sz; }
    ents.push({ usz, lho }); p = qe + cl;
  }
  const seen = new Uint8Array(2 ** 31 / 8), A = {}, NAT = { famColour: new Map(), makeColour: new Map(), colourFy: new Map(), fuelFy: new Map(), makeFy: new Map(), famFy: new Map(), famFuel: new Map(), areaFam: new Map(), areaFamColour: new Map(), vanFam: new Map() };
  const inc = (o, k) => { o[k] = (o[k] || 0) + 1; }, minc = (m, k) => m.set(k, (m.get(k) || 0) + 1);
  for (const e of ents.reverse()) {
    const h = new DataView(await (await fetch(U, { headers: { Range: `bytes=${e.lho}-${e.lho + 300}` } })).arrayBuffer());
    const start = e.lho + 30 + h.getUint16(26, true) + h.getUint16(28, true), end = start + e.usz - 1;
    const rd = (await fetch(U, { headers: { Range: `bytes=${start}-${end}` } })).body.getReader(), dec = new TextDecoder(); let rem = "", header = null;
    for (;;) {
      const { value, done } = await rd.read(); if (done) break;
      const lines = (rem + dec.decode(value, { stream: true })).split("\n"); rem = lines.pop();
      for (const ln of lines) {
        if (!header) { header = ln; continue; }
        const f = ln.split(",");   // the few quoted lines were parsed with a small CSV state machine
        if (f[3] !== "4") continue;
        const vid = +f[1], by = Math.floor(vid / 8), bit = 1 << (vid % 8); if (seen[by] & bit) continue; seen[by] |= bit;
        const area = f[7] || "NA", make = (f[8] || "UNKNOWN").trim(), model = (f[9] || "UNKNOWN").trim(), col = f[10] || "NA", fuel = f[11] || "NA", cc = +f[12], fu = f[13] || "", td = f[2];
        const mf = make + "|" + fam(make, model), van = VANS.has(mf) || VANMAKE.has(make), fy = fu.slice(0, 4);
        const a = A[area] || (A[area] = { car: { n: 0, make: {}, colour: {}, fuel: {}, fy: {}, ageSum: 0, ageN: 0, ccSum: 0, ccN: 0 }, van: { n: 0, colour: {}, fuel: {} } });
        if (van) { a.van.n++; inc(a.van.colour, col); inc(a.van.fuel, fuel); minc(NAT.vanFam, mf); continue; }
        const c = a.car; c.n++; inc(c.make, make); inc(c.colour, col); inc(c.fuel, fuel);
        if (fy.length === 4) { inc(c.fy, fy); const age = (Date.parse(td) - Date.parse(fu)) / 31557600000; if (age >= 0 && age < 120) { c.ageSum += age; c.ageN++; } }
        if (cc > 0 && cc < 20000 && fuel !== "EL" && fuel !== "ELECTRIC") { c.ccSum += cc; c.ccN++; }
        minc(NAT.areaFam, area + "|" + mf); minc(NAT.areaFamColour, area + "|" + mf + "|" + col); minc(NAT.famColour, mf + "|" + col); minc(NAT.makeColour, make + "|" + col);
        minc(NAT.colourFy, col + "|" + fy); minc(NAT.fuelFy, fuel + "|" + fy); minc(NAT.makeFy, make + "|" + fy); minc(NAT.famFy, mf + "|" + fy); minc(NAT.famFuel, mf + "|" + fuel);
      }
    }
  }
  return { areas: A, nat: NAT };
}

/* B. ONS Postcode Directory (August 2026), from the ONS Open Geography ArcGIS service: live (doterm null), small-user
      postcodes counted by postcode area x LSOA x local authority x county x country, with mean grid references.
      A postcode area's postcodes are matched with prefixes such as 'BB0%' to 'BB9%' so 'B' and 'BB' never mix. */
async function gatherONSPD(AREAS) {
  const B = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/ONS_Postcode_Directory_(August_2026)_(Hosted_Table)/FeatureServer/0/query";
  const os = JSON.stringify([{ statisticType: "count", onStatisticField: "ObjectId", outStatisticFieldName: "n" }, { statisticType: "avg", onStatisticField: "east1m", outStatisticFieldName: "e" }, { statisticType: "avg", onStatisticField: "north1m", outStatisticFieldName: "no" }]);
  const rows = [];
  for (const a of AREAS) for (let d = 0; d < 10; d++) {
    let off = 0;
    for (;;) {
      const q = new URLSearchParams({ where: `doterm IS NULL AND usrtypind=0 AND pcds LIKE '${a}${d}%'`, outStatistics: os, groupByFieldsForStatistics: "lsoa21cd,lad26cd,cty26cd,ctry26cd", orderByFields: "lsoa21cd,lad26cd", resultOffset: off, resultRecordCount: 1000, f: "json" });
      const j = await (await fetch(B + "?" + q)).json();
      for (const f of j.features) { const x = f.attributes; rows.push([a, x.lsoa21cd, x.lad26cd, x.cty26cd, x.ctry26cd, x.n, Math.round(x.e), Math.round(x.no)]); }
      if (j.features.length === 1000) { off += 1000; continue; } break;
    }
  }
  return rows;  // plus the LAD26 to CTYUA26 lookup (grouped statistics query) and the CTYUA December 2025 BUC boundaries as GeoJSON (outSR 4326)
}

/* C. DfT vehicle licensing statistics (gov.uk assets origin): VEH0125 reduced to BodyType = Cars for 2025 Q4 and 2026 Q2,
      VEH0145 (plug-in vehicles by LSOA, fuel and keepership) for the same quarters, and VEH0120 GB and UK reduced to
      Cars, Licensed, by make, generic model, model and fuel. Each file is streamed line by line and filtered. */
