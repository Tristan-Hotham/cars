# Reddit post

## Title

[OC] What does Britain drive? The most common car make, model and colour in every postcode area, from 28.9 million cars that had an MOT test in 2025

## Body

I read every MOT test from 2025 (42,728,066 records) and counted each car once. Ford is the most common make in 89 of 118 postcode areas, and the average British car is a blue Ford Fiesta, 10.7 years old. Scotland is different: white is its most common colour and the Vauxhall Corsa its top model. Shetland is the oddest place in Britain, with 14.4% Toyotas. Grey has gone from 3% of surviving cars first used in 2000 to 26% of those from 2022. Caveat: cars under three have no MOT yet and are placed by the testing garage's postcode area, so electric cars come from DfT licensing data instead.

Search your own town or postcode: https://maps.tristanhotham.com/cars/

## Source comment

Source: DVSA anonymised MOT tests and results, 2025 results extract (Open Government Licence v3.0); DfT vehicle licensing statistics tables VEH0120, VEH0125 and VEH0145 (Open Government Licence v3.0); ONS Postcode Directory (August 2026) and Counties and Unitary Authorities boundaries (Open Government Licence v3.0; contains OS data and Royal Mail data, Crown copyright and database right 2026). Vans and pick-ups set aside by model. Northern Ireland's MOTs are run by the DVA, which publishes no make or colour data, so it is shown from DfT licensing data only.

Tools: Python (shapely, scipy, pyproj, matplotlib), with the MOT files streamed in a web browser.

Interactive version: https://maps.tristanhotham.com/cars/
Blog post: https://blog.tristanhotham.com/2026/10/28/cars/
Paper: https://doi.org/10.5281/zenodo.23748250
