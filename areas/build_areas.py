"""Build areas/*.geojson: boundaries with official land areas.

Every area_km2 is in square kilometers; places are land area, lakes water surface:
States and metro areas: Census Bureau 2024 cartographic boundary files (1:20m).
  Area = ALAND from the same files (Census land area, square meters -> km2).
  Metro population: Census Vintage 2024 population estimates (July 1, 2024).
Countries: World Bank Official Boundaries (Admin 0), area from World Bank WDI
  AG.LND.TOTL.K2 "Land area (sq. km)" (FAO; excludes inland water), latest year.
Lakes: HydroLAKES v1.0 (lakes and reservoirs of 5,000 km2 and up); area is the
  dataset's Lake_area, water surface in km2. Not land area -- lakes are water.

Usage: python build_areas.py <download_dir>
  download_dir holds the unzipped Census shapefiles, cbsa-est2024.csv,
  wb_land.json, the unzipped World Bank Admin 0 shapefile in wb_admin0/ and the
  unzipped HydroLAKES polygons in hydrolakes/
  (see SOURCES.md).
Needs: pip install pyshp shapely
"""
import csv
import glob
import json
import os
import sys

import shapefile
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

DL = sys.argv[1]
OUT = os.path.dirname(os.path.abspath(__file__))
M2_PER_KM2 = 1_000_000
KM2_PER_SQ_MI = 2.589988110336  # exact: 1 mi = 1.609344 km


def simplify(geom, tol):
    g = shape(geom).simplify(tol, preserve_topology=True)
    return round_coords(mapping(g))


def round_coords(geom, nd=4):
    def r(c):
        if isinstance(c[0], (int, float)):
            return [round(c[0], nd), round(c[1], nd)]
        return [r(x) for x in c]
    return {"type": geom["type"], "coordinates": r(geom["coordinates"])}


def write(name, features):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, separators=(",", ":"))
    print(f"{name}: {len(features)} features, {os.path.getsize(path) // 1024} KB")


def census_features(stem, keep, props, tol):
    r = shapefile.Reader(os.path.join(DL, stem, stem))
    feats = []
    for sr in r.iterShapeRecords():
        rec = sr.record.as_dict()
        if not keep(rec):
            continue
        p = props(rec)
        p["area_km2"] = round(rec["ALAND"] / M2_PER_KM2, 1)  # ALAND is in square meters
        feats.append({"type": "Feature", "properties": p, "geometry": simplify(sr.shape.__geo_interface__, tol)})
    return feats


# States (50 states + DC + Puerto Rico)
states = census_features(
    "cb_2024_us_state_20m",
    lambda r: True,
    lambda r: {"id": r["GEOID"], "name": r["NAME"], "abbr": r["STUSPS"]},
    0.005,
)
states.sort(key=lambda f: f["properties"]["name"])
write("states.geojson", states)

# Metropolitan statistical areas (LSAD M1; micropolitan areas dropped)
pop = {}
with open(os.path.join(DL, "cbsa-est2024.csv"), encoding="latin-1") as f:
    for row in csv.DictReader(f):
        if row["LSAD"] == "Metropolitan Statistical Area":
            pop[row["CBSA"]] = int(row["POPESTIMATE2024"])
msas = census_features(
    "cb_2024_us_cbsa_20m",
    lambda r: r["LSAD"] == "M1",
    lambda r: {"id": r["GEOID"], "name": r["NAME"], "population_2024": pop.get(r["GEOID"])},
    0.005,
)
msas.sort(key=lambda f: -(f["properties"]["population_2024"] or 0))
for i, f in enumerate(msas, 1):
    f["properties"]["pop_rank"] = i
write("msas.geojson", msas)

# Countries
wb = json.load(open(os.path.join(DL, "wb_land.json")))[1]
land_area = {d["countryiso3code"]: (d["value"], d["date"], d["country"]["value"]) for d in wb if d["value"] is not None}
iso2 = {d["countryiso3code"]: d["country"]["id"] for d in wb}
admin0 = shapefile.Reader(glob.glob(os.path.join(DL, "wb_admin0", "**", "*.shp"), recursive=True)[0])
parts = {}
for sr in admin0.iterShapeRecords():
    rec = sr.record.as_dict()
    code = rec["WB_A3"] if rec["WB_A3"] in land_area else rec["ISO_A3"]
    if code in land_area and sr.shape.points:
        parts.setdefault(code, []).append(shape(sr.shape.__geo_interface__))
countries = []
for code, geoms in parts.items():
    km2, year, wbname = land_area[code]
    countries.append({
        "type": "Feature",
        "properties": {"id": code, "name": wbname, "area_km2": km2, "area_year": int(year)},
        "geometry": simplify(mapping(unary_union(geoms)), 0.02),
    })
countries.sort(key=lambda f: f["properties"]["name"])
write("countries.geojson", countries)
missing = sorted(set(k for k in land_area if len(k) == 3) - {f["properties"]["id"] for f in countries})
print("WB land-area codes without a boundary (mostly aggregates):", " ".join(missing))

# Lakes and reservoirs of 5,000 km2 and up
LAKE_MIN_KM2 = 5000
LAKE_TYPES = {1: "lake", 2: "reservoir", 3: "lake"}  # 3 = natural lake with a dam controlling its level
# HydroLAKES names are bare ("Superior"); most become "Lake Superior". These don't.
LAKE_NAMES = {
    "Great Bear": "Great Bear Lake", "Great Slave": "Great Slave Lake", "Great Salt": "Great Salt Lake", "Reindeer": "Reindeer Lake",
    "Chiquita": "Mar Chiquita", "Issyk Kul": "Lake Issyk-Kul", "Vanern": "Lake Vänern",
    "Michikamau": "Smallwood Reservoir",  # HydroLAKES uses the name of the lake it flooded
}


def lake_name(name):
    if name in LAKE_NAMES:
        return LAKE_NAMES[name]
    if any(w in name for w in ("Sea", "Reservoir", "Gol", "Lake")):
        return name
    return "Lake " + name


hl = shapefile.Reader(glob.glob(os.path.join(DL, "hydrolakes", "**", "HydroLAKES_polys_v10.shp"), recursive=True)[0], encoding="cp1252")  # names are Windows-1252
lakes = []
for i, rec in enumerate(hl.iterRecords(fields=["Hylak_id", "Lake_name", "Lake_type", "Lake_area", "Country"])):
    if rec["Lake_area"] < LAKE_MIN_KM2:
        continue
    lakes.append({
        "type": "Feature",
        "properties": {"id": str(rec["Hylak_id"]), "name": lake_name(rec["Lake_name"]) if rec["Lake_name"] else f"Lake {rec['Hylak_id']}",
                       "lake_type": LAKE_TYPES[rec["Lake_type"]], "country": rec["Country"],
                       "area_km2": round(rec["Lake_area"], 1)},
        "geometry": simplify(hl.shape(i).__geo_interface__, 0.01),
    })
lakes.sort(key=lambda f: -f["properties"]["area_km2"])
write("lakes.geojson", lakes)

# nested_data_source.csv: every area with its sources, shown by nested_data_source.html
CENSUS_BOUNDARIES = "https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.2024.html"
CENSUS_METRO_POP = "https://www.census.gov/data/tables/time-series/demo/popest/2020s-total-metro-and-micro-statistical-areas.html"
WB_BOUNDARIES = "https://datacatalog.worldbank.org/search/dataset/0038272"
HYDROLAKES = "https://www.hydrosheds.org/products/hydrolakes"
rows = []
for category, feats in [("US states", states), ("US metro areas", msas), ("Countries", countries), ("Lakes and reservoirs", lakes)]:
    for f in feats:
        p = f["properties"]
        area_type = "land"
        if category == "Lakes and reservoirs":
            year = 2016  # HydroLAKES v1.0
            area_type = p["lake_type"] + " surface"
            source = HYDROLAKES
        elif category == "Countries":
            year = p["area_year"]
            source = f"https://data.worldbank.org/indicator/AG.LND.TOTL.K2?locations={iso2[p['id']]} {WB_BOUNDARIES}"
        else:
            year = 2024
            source = CENSUS_BOUNDARIES + (" " + CENSUS_METRO_POP if category == "US metro areas" else "")
        rows.append({
            "category": category,
            "name": p["name"],
            "area_km2": p["area_km2"],
            "area_sq_mi": round(p["area_km2"] / KM2_PER_SQ_MI, 1),
            "area_type": area_type,
            "population_2024": p.get("population_2024", ""),
            "year": year,
            "source": source,
        })
csv_path = os.path.join(OUT, "..", "nested_data_source.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"nested_data_source.csv: {len(rows)} rows")

# Unit check across the two sources: Census land of the 50 states + DC should
# match the World Bank's land area for the United States.
census_us = sum(f["properties"]["area_km2"] for f in states if f["properties"]["abbr"] != "PR")
wb_us = land_area["USA"][0]
print(f"US land: Census states sum {census_us:,.0f} km2, World Bank {wb_us:,.0f} km2 ({census_us / wb_us - 1:+.2%})")
