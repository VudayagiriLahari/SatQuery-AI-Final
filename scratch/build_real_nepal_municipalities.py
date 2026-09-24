import urllib.request
import json
import time
import shapely.geometry
from shapely.ops import linemerge, polygonize, unary_union

# Authoritative Census 2021 Population figures (CBS Nepal)
municipalities = [
    {"id": 10529084, "name": "Gosaikunda Rural Municipality", "nepali_name": "गोसाइँकुण्ड गाउँपालिका", "district": "Rasuwa", "population": 7855, "zone": "North/Langtang"},
    {"id": 10529085, "name": "Kalika Rural Municipality", "nepali_name": "कालिका गाउँपालिका", "district": "Rasuwa", "population": 9566, "zone": "South/Trishuli"},
    {"id": 10529086, "name": "Uttargaya Rural Municipality", "nepali_name": "उत्तरगया गाउँपालिका", "district": "Rasuwa", "population": 8555, "zone": "South-West/Betrawati"},
    {"id": 10529087, "name": "Naukunda Rural Municipality", "nepali_name": "नौकुण्ड गाउँपालिका", "district": "Rasuwa", "population": 12357, "zone": "South-East"},
    {"id": 10529088, "name": "Aamachhodingmo Rural Municipality", "nepali_name": "आमाछोदिङ्मो गाउँपालिका", "district": "Rasuwa", "population": 6673, "zone": "North-West/Chilime"},
    {"id": 10534616, "name": "Helambu Rural Municipality", "nepali_name": "हेलम्बु गाउँपालिका", "district": "Sindhupalchowk", "population": 17490, "zone": "East"},
    {"id": 10534782, "name": "Kispang Rural Municipality", "nepali_name": "किस्पाङ गाउँपालिका", "district": "Nuwakot", "population": 14861, "zone": "South-West"}
]

features = []
visual_features = []

for m in municipalities:
    rel_id = m["id"]
    url = f"https://www.openstreetmap.org/api/0.6/relation/{rel_id}/full.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'SatQuery-AI/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elements = data.get("elements", [])
            nodes = {e["id"]: (e["lon"], e["lat"]) for e in elements if e["type"] == "node"}
            ways = [e for e in elements if e["type"] == "way"]
            
            rel_elem = [e for e in elements if e["type"] == "relation" and e["id"] == rel_id][0]
            members = rel_elem.get("members", [])
            outer_way_ids = {m_ref["ref"] for m_ref in members if m_ref.get("role") in ("outer", "")}
            
            lines = []
            for w in ways:
                if w["id"] in outer_way_ids or not outer_way_ids:
                    w_nodes = w.get("nodes", [])
                    pts = [nodes[nid] for nid in w_nodes if nid in nodes]
                    if len(pts) >= 2:
                        lines.append(shapely.geometry.LineString(pts))
            
            if lines:
                merged = linemerge(lines)
                polys = list(polygonize(merged))
                if polys:
                    poly = unary_union(polys)
                else:
                    poly = shapely.geometry.MultiLineString(lines).convex_hull
                
                poly_simple = poly.simplify(0.0003, preserve_topology=True)
                
                feat = {
                    "type": "Feature",
                    "properties": {
                        "name": m["name"],
                        "nepali_name": m["nepali_name"],
                        "district": m["district"],
                        "country": "Nepal",
                        "population": m["population"],
                        "zone": m["zone"],
                        "type": "Rural Municipality"
                    },
                    "geometry": shapely.geometry.mapping(poly_simple)
                }
                features.append(feat)

                # For visual overlay: exterior ring LineString for dashed yellow outlines
                if poly_simple.geom_type == "Polygon":
                    vis_geom = shapely.geometry.LineString(poly_simple.exterior.coords)
                elif poly_simple.geom_type == "MultiPolygon":
                    vis_geom = shapely.geometry.MultiLineString([g.exterior.coords for g in poly_simple.geoms])
                else:
                    vis_geom = poly_simple
                
                vis_feat = {
                    "type": "Feature",
                    "properties": {
                        "name": m["name"],
                        "district": m["district"],
                        "population": m["population"],
                        "zone": m["zone"]
                    },
                    "geometry": shapely.geometry.mapping(vis_geom)
                }
                visual_features.append(vis_feat)

                print(f"Success for {m['name']}: {poly_simple.geom_type}, bounds={poly_simple.bounds}")
        time.sleep(0.5)
    except Exception as e:
        print(f"Failed {m['name']}: {e}")

print(f"\nConstructed {len(features)} real Rural Municipalities in Nepal Rasuwa study area!")

with open("scratch/nepal_municipalities.geojson", "w", encoding="utf-8") as f:
    json.dump({"type": "FeatureCollection", "features": features}, f, indent=2, ensure_ascii=False)

with open("scratch/nepal_municipalities_visual.geojson", "w", encoding="utf-8") as f:
    json.dump({"type": "FeatureCollection", "features": visual_features}, f, indent=2, ensure_ascii=False)

print("Saved scratch/nepal_municipalities.geojson and scratch/nepal_municipalities_visual.geojson!")
