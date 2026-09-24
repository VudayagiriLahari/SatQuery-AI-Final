import urllib.request
import json

q = """[out:json][timeout:35];
(
  way["building"](28.04,85.14,28.35,85.55);
);
out geom 500;
"""

mirrors = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

print("Fetching real building footprints from OpenStreetMap for Nepal...")
elements = []
for mirror in mirrors:
    try:
        print(f"Trying Overpass mirror: {mirror}...")
        req = urllib.request.Request(mirror, data=q.encode('utf-8'), headers={'User-Agent': 'SatQuery-AI/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elements = data.get("elements", [])
            if elements:
                print(f"Fetched {len(elements)} real Nepal building footprints from {mirror}.")
                break
    except Exception as e:
        print(f"Mirror {mirror} failed: {e}")

features = []
for idx, el in enumerate(elements):
    pts = [(pt["lon"], pt["lat"]) for pt in el.get("geometry", [])]
    if len(pts) >= 3:
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        tags = el.get("tags", {})
        b_type = tags.get("building", "residential")
        name = tags.get("name:en") or tags.get("name") or "Building"
        features.append({
            "type": "Feature",
            "properties": {
                "building_id": f"NEPAL_OSM_BLD_{el.get('id', idx+1)}",
                "type": b_type,
                "name": name,
                "district": "Rasuwa",
                "country": "Nepal"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [pts]
            }
        })

print(f"Constructed {len(features)} real Nepal building Polygon features.")
with open("scratch/nepal_buildings.geojson", "w", encoding="utf-8") as out_f:
    json.dump({"type": "FeatureCollection", "features": features}, out_f, indent=2, ensure_ascii=False)

print("Saved scratch/nepal_buildings.geojson!")
