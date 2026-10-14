# Areas: sources

All four files are GeoJSON (WGS84 lon/lat), simplified for the web, with official
areas as properties. Built by `build_areas.py`, which also writes
`../nested_data_source.csv` (one row per area, with source links; shown by
`nested_data_source.html`).

## Units
Every `area_km2` is in **square kilometers**. States, metro areas and countries are
**land area** (water left out); lakes and reservoirs are **water surface area**.
- Census `ALAND` is in square meters (per the files' metadata: "Current land area
  (square meters)"); divided by 1,000,000.
- World Bank `AG.LND.TOTL.K2` is already in square kilometers.
- HydroLAKES `Lake_area` is already in square kilometers (tech doc: "Lake surface area
  (i.e. polygon area), in square kilometers").
- Square miles in the CSV use 1 sq mi = 2.589988110336 km² (exact).
- Check: Census land of the 50 states + DC sums to 9,151,638 km²; the World Bank's
  land area for the United States is 9,147,420 km² (+0.05%). `build_areas.py` prints this.

## states.geojson (52: 50 states, DC, Puerto Rico)
- Boundaries: U.S. Census Bureau, 2024 cartographic boundary file, states, 1:20,000,000
  https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_20m.zip
- Area: `ALAND` from the same file (Census land area; water left out).

## msas.geojson (393 metropolitan statistical areas)
- Boundaries: U.S. Census Bureau, 2024 cartographic boundary file, CBSAs, 1:20,000,000,
  metropolitan only (LSAD M1; the 542 micropolitan areas are dropped). Delineations are
  OMB Bulletin 23-01 (July 2023).
  https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_cbsa_20m.zip
- Area: `ALAND`, as for states.
- `population_2024` / `pop_rank`: Census Vintage 2024 population estimates, July 1, 2024
  https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/metro/totals/cbsa-est2024-alldata.csv

## countries.geojson (215)
- Area: World Bank WDI `AG.LND.TOTL.K2`, Land area (sq. km), 2024 (source: FAO).
  "A country's total area, excluding area under inland water bodies, national claims to
  continental shelf, and exclusive economic zones."
  https://data.worldbank.org/indicator/AG.LND.TOTL.K2
- Boundaries: World Bank Official Boundaries, Admin 0, 1:10m, matched on `WB_A3`
  https://datacatalogfiles.worldbank.org/ddh-published/0038272/DR0046659/wb_countries_admin0_10m.zip
- Every country with a World Bank land area has a shape except the Channel Islands (CHI).
  Places with no World Bank land area (e.g. Taiwan, Kosovo, Vatican City, Antarctica,
  Western Sahara) are left out.

## lakes.geojson (38 lakes and reservoirs of 5,000 km² and up)
- Boundaries and area: HydroLAKES v1.0, `Lake_area` (km², computed from each polygon
  the same way for every lake). A peer-reviewed global dataset, not official figures.
  https://www.hydrosheds.org/products/hydrolakes
  Messager, M.L., Lehner, B., Grill, G., Nedeva, I., Schmitt, O. (2016): Estimating the
  volume and age of water stored in global lakes using a geo-statistical approach.
  Nature Communications: 13603. doi:10.1038/ncomms13603
- `lake_type`: "lake" (HydroLAKES types 1 and 3; 3 is a natural lake with a dam
  regulating it) or "reservoir" (type 2). HydroLAKES names are bare ("Superior"); the
  build adds "Lake" ("Lake Superior", "Great Bear Lake") and fixes a few
  ("Michikamau" -> "Smallwood Reservoir", "Chiquita" -> "Mar Chiquita"); see `LAKE_NAMES`.
- Areas can differ from figures quoted elsewhere because they are measured from the
  polygons (e.g. Caspian Sea 377,002 km²; Lake Volta 6,045 km² against the ~8,500 km²
  often quoted at full pool).

## Rebuilding
Download the files above into a folder (unzip the shapefiles into folders named after
the zips, the World Bank one into `wb_admin0/`), save
`https://api.worldbank.org/v2/country/all/indicator/AG.LND.TOTL.K2?format=json&per_page=500&mrnev=1`
as `wb_land.json`, unzip
https://data.hydrosheds.org/file/hydrolakes/HydroLAKES_polys_v10_shp.zip (820 MB) into
`hydrolakes/`, then `pip install pyshp shapely` and
`python areas/build_areas.py <that folder>`.
