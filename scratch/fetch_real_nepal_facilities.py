import urllib.request
import json
import shapely.geometry
from shapely.geometry import Point, shape
import rasterio
import sys
sys.path.insert(0, 'Backend')
from app.services.flood_detection import FloodDetectionService
from app.services.polygon_generation import PolygonGenerationService

# First detect flood polygon so we know which facilities are outside the flood
det = FloodDetectionService().detect('data/test_images/nepal_before_flood.tif', 'data/test_images/nepal_after_flood.tif')
ds = rasterio.open('data/test_images/nepal_before_flood.tif')
poly = PolygonGenerationService().generate(det['mask_array'], ds.transform, ds.crs.to_wkt())
flood_geom = shape(poly['geojson']['features'][0]['geometry'])

q = """[out:json][timeout:35];
(
  node["amenity"~"school|college|hospital|clinic|doctors|community_centre|townhall|police|fire_station|shelter|place_of_worship"](28.00,85.10,28.38,85.60);
  node["office"~"government"](28.00,85.10,28.38,85.60);
);
out body;
"""

mirrors = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

print("Fetching real educational, healthcare, and emergency facilities from OSM for Nepal...")
elements = []
for mirror in mirrors:
    try:
        print(f"Trying Overpass mirror: {mirror}...")
        req = urllib.request.Request(mirror, data=q.encode('utf-8'), headers={'User-Agent': 'SatQuery-AI/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elements = data.get("elements", [])
            if elements:
                print(f"Fetched {len(elements)} raw Nepal facility nodes from {mirror}.")
                break
    except Exception as e:
        print(f"Mirror {mirror} failed: {e}")

features = []
for el in elements:
    tags = el.get("tags", {})
    name = tags.get("name:en") or tags.get("name")
    if not name:
        amenity_type = tags.get("amenity") or tags.get("office", "Civic Center")
        name = f"{amenity_type.replace('_', ' ').title()} Facility"
    
    lat, lon = el["lat"], el["lon"]
    amenity = tags.get("amenity") or tags.get("office", "government")
    pt = Point(lon, lat)
    
    dist_deg = pt.distance(flood_geom)
    dist_km = dist_deg * 111.0 # approx
    
    # Filter sites that are outside the flood polygon
    if not flood_geom.contains(pt):
        # standard evacuation capacity estimate based on amenity type
        if amenity in ("school", "college"):
            capacity = 450
        elif amenity in ("hospital", "clinic"):
            capacity = 200
        elif amenity in ("community_centre", "townhall", "government"):
            capacity = 300
        else:
            capacity = 150
            
        features.append({
            "type": "Feature",
            "properties": {
                "name": name,
                "type": amenity,
                "amenity": amenity,
                "capacity": capacity,
                "osm_id": el["id"],
                "country": "Nepal",
                "district": "Rasuwa",
                "distance_km": round(dist_km, 2)
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        })

print(f"Selected {len(features)} real suitable safe facilities around the Nepal flood zone.")
for f in features[:8]:
    p = f["properties"]
    print(f" - {p['name']} ({p['type']}): {p['distance_km']} km away")

with open("scratch/nepal_facilities.geojson", "w", encoding="utf-8") as out_f:
    json.dump({"type": "FeatureCollection", "features": features}, out_f, indent=2, ensure_ascii=False)

print("Saved scratch/nepal_facilities.geojson!")
