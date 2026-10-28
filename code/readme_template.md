# What Britain drives

Car makes, models, colours, fuel and age by county, postcode area and nation, from every MOT test in Great Britain in 2025, with electric cars and Northern Ireland from DfT vehicle licensing statistics.

Interactive page: https://maps.tristanhotham.com/cars/
Paper: https://doi.org/10.5281/zenodo.23748250
Author: Dr Tristan Hotham, Independent researcher (ORCID 0000-0003-4931-9349)

## Headline results

- {{meta.rows|int}} MOT test records for 2025 reduce to {{meta.vehicles|int}} class 4 vehicles (each counted once, at its last test of the year) and {{meta.cars|int}} cars once {{meta.vans|int}} vans and pick-ups are set aside.
- The average British car is a {{facts.GB.top_model_colour}} {{facts.GB.top_model}}, {{facts.GB.age|f1}} years old at its test, with a {{facts.GB.cc|int}} cc engine. Ford is the most common make ({{facts.GB.top_make_share|pct1}}), black the most common colour ({{facts.GB.top_colour_share|pct1}}).
- Ford leads in {{facts.areas_ford|int}} of {{facts.areas_n|int}} postcode areas. Vauxhall's strongest area is Luton ({{facts.a_LU.top_make_share|pct1}} of cars); the Toyota Prius is the most common car in east London.
- Scotland's most common colour is white ({{facts.Scotland.top_colour_share|pct1}}) and its most common model the Vauxhall Corsa; its tested cars are the youngest ({{facts.Scotland.age|f1}} years).
- The most unusual postcode area is Shetland: {{facts.a_ZE.top_make_share|pct1}} of cars are Toyotas, {{facts.unusual_area.0.lq|x1}} times Scotland's share.
- Grey rose from {{facts.grey2000|pct1}} of surviving cars first used in 2000 to {{facts.grey2022|pct1}} of those from 2022; silver fell from {{facts.silver2000|pct1}} to {{facts.silver2022|pct1}}.
- Battery electric cars per 100 privately kept cars (DfT, end of 2025): {{facts.uk_bev|f2}} in the UK, from {{facts.bev_top.0.bev|f2}} in the City of London to {{facts.bev_low.0.bev|f2}} in Fermanagh and Omagh.
- Northern Ireland (DfT licensed cars): Volkswagen leads ({{facts.NI.m1s|pct1}}), then Audi ({{facts.NI.m2s|pct1}}); {{facts.NI.diesel|pct1}} of cars are diesel against {{facts.GB.dft_diesel|pct1}} in Great Britain.

## Files

- `index.html`: the interactive page (Leaflet map with a Map layers panel, search, charts). It loads `data/units.json`, `data/postcode_areas.geojson`, `data/counties.geojson` and `data/places.json`.
- `data/results.json`: every number used on the page, in the paper, the blog post and the collage.
- `data/postcode_areas.csv`, `data/counties.csv`, `data/nations.csv`: one row per place: cars tested, top make, model and colour with shares, average age and engine size, fuel shares, DfT licensed cars and battery electric cars per 100 private cars, dissimilarity from the nation and the most over-represented make.
- `data/area_make_counts.csv`, `data/area_model_counts.csv` (model families with at least 5 cars, flagged if van or pick-up), `data/area_colour_fuel_counts.csv` (colour, raw fuel code and year of first use): the MOT aggregates by postcode area, cars only.
- `data/gb_colour_by_year.csv`: colour shares by year of first use.
- `data/area_county_weights.csv`: share of each postcode area's live postcodes in each county or unitary authority; `data/lsoa_county.csv`: neighbourhood to county lookup used for the DfT tables.
- `data/postcode_areas.geojson`: approximate postcode area outlines (Voronoi cells around postcode group centres, clipped to the coast); `data/counties.geojson`: ONS ultra generalised boundaries.
- `data/places.json`: OS Open Names cities, towns, villages and suburbs tagged with postcode area and county, for search and labels.
- `code/`: the pipeline (below). `release/`: paper PDF and LaTeX source, blog post and figures, Zenodo files. `reddit/`: the collage and post.

## How to rerun

1. `code/01_gather_browser.js`: browser scripts that stream the DVSA MOT 2025 archive by HTTP range requests, query the ONS Postcode Directory service with grouped statistics, and filter the DfT tables, saving three gzipped JSON bundles of aggregates (`cars_mot2025_v2.json.gz`, `cars_onspd_geo.json.gz`, `cars_dft_veh.json.gz`). Only aggregates were ever saved; the 4.8 GB MOT archive was never downloaded whole.
2. `python3 code/02_geo.py`: postcode area to county weights, postcode area outlines, county polygons.
3. `python3 code/03_analyse.py`: all tables and `data/results.json`.
4. `python3 code/04_build_site.py`: `index.html`, `data/units.json`, `data/places.json` (checks the facts stated in words).
5. `python3 code/05_figures.py`: paper and blog figures, `header.png`.
6. `python3 code/06_paper.py`: the paper (xelatex).
7. `python3 code/07_release.py`: blog post, README, Zenodo files.
8. `python3 reddit/collage.py`: the collage.

`code/common.py` holds the model-family rules, the van and pick-up list, fuel groups and postcode area names (named after their main post town).

## Method notes and limits

- MOT class 4 only; each vehicle counted once at its latest 2025 test ({{meta.retests|int}} earlier tests and retests dropped). Vans and pick-ups are set aside by model family; some car-derived vans remain.
- Cars are placed by the postcode area of the testing garage, not the keeper's address. County figures share out each postcode area's cars by its live small-user postcodes (ONS Postcode Directory, August 2026, {{meta.postcodes|int}} postcodes), so counties within one postcode area look alike.
- Cars under three years old have no MOT: {{meta.cars|int}} tested cars against {{meta.gb_licensed_cars|int}} licensed in Great Britain. Electric cars are therefore taken from DfT licensing data, private keepers only (company cars are registered at head offices).
- Northern Ireland's MOT tests are run by the DVA, which publishes summary test statistics through the Department for Infrastructure but, as far as I could find, no open make, model or colour data. Northern Ireland's makes and models are DfT VEH0120 (UK) minus VEH0120 (GB); no colours or ages.
- Postcode areas EC and WC (central London) have no MOT stations and are not drawn separately.

## Sources and licences

- Driver and Vehicle Standards Agency, Anonymised MOT tests and results, MOT testing data results extracts (2025), https://open.data.dvsa.gov.uk/mot-anonymised/index.html. Open Government Licence v3.0.
- Department for Transport, Vehicle licensing statistics data files, tables VEH0120 (GB and UK), VEH0125 and VEH0145, https://www.gov.uk/government/statistical-data-sets/vehicle-licensing-statistics-data-files. Open Government Licence v3.0.
- Office for National Statistics, ONS Postcode Directory (August 2026), Ward to LAD to CTYUA to Region to Country lookup (May 2026), Counties and Unitary Authorities (December 2025) Boundaries UK BUC, ONS Open Geography Portal. Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026. Contains Royal Mail data © Royal Mail copyright and database right 2026. Northern Ireland postcodes: © Crown copyright (Land and Property Services), used under the ONSPD terms.
- Ordnance Survey, OS Open Names. Open Government Licence v3.0.
- Base map tiles on the page © Esri. Map library: Leaflet. Postcode lookups on the page: postcodes.io.

Licences for this repository: data files are derived from the sources above and released under the Open Government Licence v3.0; text and figures CC BY 4.0; code MIT (see LICENSE).

## Citation

Hotham, T. (2026) What Britain Drives: Car Makes, Models, Colours and Ages by County and Postcode Area from the 2025 MOT Record. Zenodo. https://doi.org/10.5281/zenodo.23748250

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
