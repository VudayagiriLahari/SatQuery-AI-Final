import urllib.request
import json
import shapely.geometry

# Bounding box covering Nepal Rasuwa / Trishuli / Bhote Koshi flood corridor
# 28.03 to 28.36 N, 85.13 to 85.56 E
q = """[out:json][timeout:35];
(
  way["highway"~"trunk|primary|secondary|tertiary|unclassified|residential|service|track"](28.03,85.13,28.36,85.56);
);
out geom 800;
"""

mirrors = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

print("Fetching real OpenStreetMap roads in Nepal Rasuwa flood zone...")
elements = []
for mirror in mirrors:
    try:
        print(f"Trying Overpass mirror: {mirror}...")
        req = urllib.request.Request(mirror, data=q.encode('utf-8'), headers={'User-Agent': 'SatQuery-AI/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elements = data.get("elements", [])
            if elements:
                print(f"Fetched {len(elements)} real Nepal road elements from {mirror}.")
                break
    except Exception as e:
        print(f"Mirror {mirror} failed: {e}")

features = []
for el in elements:
    pts = [(pt["lon"], pt["lat"]) for pt in el.get("geometry", [])]
    if len(pts) >= 2:
        tags = el.get("tags", {})
        name = tags.get("name:en") or tags.get("name") or tags.get("ref") or f"{tags.get('highway', 'Road').capitalize()} Road"
        features.append({
            "type": "Feature",
            "properties": {
                "name": name,
                "highway": tags.get("highway", "secondary"),
                "surface": tags.get("surface", "unpaved"),
                "osm_id": el.get("id"),
                "country": "Nepal",
                "district": "Rasuwa"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": pts
            }
        })

print(f"Constructed {len(features)} Nepal road LineString features.")
with open("scratch/nepal_roads.geojson", "w", encoding="utf-8") as f:
    json.dump({"type": "FeatureCollection", "features": features}, f, indent=2, ensure_ascii=False)

print("Saved scratch/nepal_roads.geojson!")
