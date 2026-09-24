import sys
sys.path.insert(0, 'Backend')
import json
import rasterio
from shapely.geometry import shape

from app.services.flood_detection import FloodDetectionService
from app.services.polygon_generation import PolygonGenerationService
from app.services.gis_repository import GISRepository
from app.services.exposure_analysis import ExposureAnalysisService
from app.services.evacuation import EvacuationService
from app.services.impact_scoring import ImpactScoringService

def run_study(region_name, pre_img, post_img):
    print(f"\n========================================================")
    print(f" TESTING FULL GIS PIPELINE FOR: {region_name.upper()}")
    print(f"========================================================")
    
    # 1. Flood Detection
    det = FloodDetectionService().detect(pre_img, post_img)
    with rasterio.open(pre_img) as ds:
        poly = PolygonGenerationService().generate(det['mask_array'], ds.transform, ds.crs.to_wkt())
    
    flood_geojson = poly['geojson']
    print(f"Detected Flood Area: {poly.get('total_area_km2', 0):.2f} km2 ({len(flood_geojson.get('features', []))} polygons)")
    
    # 2. Exposure Analysis
    repo = GISRepository("data")
    exposure_svc = ExposureAnalysisService()
    exposure = exposure_svc.calculate_exposure(flood_geojson, region_name, repo)
    
    print("\n--- EXPOSURE RESULTS ---")
    print("Data availability:", exposure.get("data_availability"))
    print("Affected population:", exposure.get("affected_population"))
    print("Affected buildings:", exposure.get("affected_buildings"))
    print("Affected road length (km):", exposure.get("affected_road_length_km"))
    print(f"Affected admin regions count: {len(exposure.get('affected_villages', []))}")
    for v in exposure.get("affected_villages", []):
        print(f" - {v['name']}: {v['area_flooded_km2']} km2 flooded")
        
    # 3. Priority Scoring
    priority = ImpactScoringService().compute_priority_scores(exposure)
    print("\n--- PRIORITY SCORES ---")
    for p in priority:
        print(f" - Rank #{p['rank']}: {p.get('village_name')} (score={p['priority_score']:.4f})")
        
    # 4. Evacuation Candidates & Routing
    evac_svc = EvacuationService()
    evac = evac_svc.find_candidates(flood_geojson, repo, buffer_m=100.0)
    candidates = evac.get("candidates", [])
    print(f"\n--- EVACUATION CANDIDATES ---")
    print(f"Total safe candidates found: {len(candidates)}")
    for c in candidates[:6]:
        print(f" - {c['name']} ({c['type']}): distance={c['distance_to_flood_km']} km, route_km={c.get('route_distance_km')}, elev={c.get('elevation_m')}m")
    
    return True

print("Running both Kerala and Nepal GIS workflows...")
# Test Kerala
run_study("kerala", "data/test_images/kerala_before_flood.tif", "data/test_images/kerala_after_flood.tif")

# Test Nepal
run_study("nepal", "data/test_images/nepal_before_flood.tif", "data/test_images/nepal_after_flood.tif")
