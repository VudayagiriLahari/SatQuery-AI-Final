"""
Integration Test for Real Nepal 2026 Flood Event Dataset & Full GIS Pipeline.

Tests:
1. Dual-GeoTIFF Image Study analysis, flood mask generation, area calculation, and centroid computation (Sentinel-2 Harmonized).
2. Full Nepal GIS pipeline: Administrative boundaries, OSM roads, OSM buildings, Safe facilities, Census population, DEM terrain, and evacuation routing.
3. Regression verification for Kerala.
"""

import os
import sys
import rasterio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_study import ImageStudyService
from app.services.flood_detection import FloodDetectionService
from app.services.polygon_generation import PolygonGenerationService
from app.services.gis_repository import GISRepository
from app.services.exposure_analysis import ExposureAnalysisService
from app.services.evacuation import EvacuationService
from app.services.impact_scoring import ImpactScoringService


def test_nepal_2026_flood_image_study():
    """
    Test ImageStudyService using the exported real Sentinel-2 GeoTIFF pair for Nepal August 2026.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pre_path = os.path.join(root_dir, "data", "test_images", "nepal_before_flood.tif")
    post_path = os.path.join(root_dir, "data", "test_images", "nepal_after_flood.tif")

    assert os.path.exists(pre_path), f"Missing test file: {pre_path}"
    assert os.path.exists(post_path), f"Missing test file: {post_path}"

    svc = ImageStudyService()

    # 1. Metadata check
    pre_meta = svc.validate_and_extract_metadata(pre_path)
    post_meta = svc.validate_and_extract_metadata(post_path)

    assert "EPSG:4326" in pre_meta["crs"]
    assert "EPSG:4326" in post_meta["crs"]
    assert pre_meta["width"] == post_meta["width"]
    assert pre_meta["height"] == post_meta["height"]

    # 2. Pipeline Analysis
    res = svc.analyze_pair(pre_path, post_path)
    assert res["success"] is True, f"Analysis failed: {res.get('error')}"

    assert res["polygon_count"] > 0, f"Expected polygon_count > 0, got {res['polygon_count']}"
    assert res["flood_area_km2"] > 0.0, f"Expected flood_area_km2 > 0, got {res['flood_area_km2']}"

    cent = res["centroid"]
    assert cent is not None, "Missing centroid"
    assert 28.0 <= cent["latitude"] <= 28.5, f"Expected lat ~28.2, got {cent['latitude']}"
    assert 85.0 <= cent["longitude"] <= 85.6, f"Expected lon ~85.2, got {cent['longitude']}"

    # 3. GeoJSON Validation
    geojson = res["geojson"]
    assert geojson is not None
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0


def test_nepal_full_gis_pipeline():
    """
    Verify complete GIS workflow for Nepal 2026 Flood:
    - Flood detection
    - Real administrative boundaries (Municipalities)
    - Real OSM road network
    - Real OSM building footprints
    - Real POI facilities & safe shelters
    - Real DEM elevation sampling
    - Exposure analysis & priority scoring
    - Evacuation candidate routing
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(root_dir, "data")
    pre_path = os.path.join(data_dir, "test_images", "nepal_before_flood.tif")
    post_path = os.path.join(data_dir, "test_images", "nepal_after_flood.tif")

    # 1. Detect Flood
    det = FloodDetectionService().detect(pre_path, post_path)
    with rasterio.open(pre_path) as ds:
        poly = PolygonGenerationService().generate(det['mask_array'], ds.transform, ds.crs.to_wkt())

    flood_geojson = poly['geojson']
    assert poly['total_area_km2'] > 0

    # 2. GIS Repository for Nepal
    repo = GISRepository(data_dir)
    
    # Verify presence of real Nepal GIS layers
    muni_gdf = repo.load_layer("villages", region="nepal")
    assert muni_gdf is not None and len(muni_gdf) > 0, "Missing Nepal municipalities layer"

    roads_gdf = repo.load_layer("roads", region="nepal")
    assert roads_gdf is not None and len(roads_gdf) > 0, "Missing Nepal roads layer"

    bld_gdf = repo.load_layer("buildings", region="nepal")
    assert bld_gdf is not None and len(bld_gdf) > 0, "Missing Nepal buildings layer"

    pois_gdf = repo.load_layer("pois", region="nepal")
    assert pois_gdf is not None and len(pois_gdf) > 0, "Missing Nepal POIs/facilities layer"

    dem_path = repo.get_dem_path(region="nepal")
    assert dem_path is not None and os.path.isfile(dem_path), "Missing Nepal DEM raster"

    # 3. Exposure Analysis
    exposure_svc = ExposureAnalysisService()
    exposure = exposure_svc.calculate_exposure(flood_geojson, "nepal", repo)

    assert exposure["data_availability"]["villages"] is True
    assert exposure["data_availability"]["roads"] is True
    assert exposure["data_availability"]["buildings"] is True
    assert exposure["data_availability"]["population"] is True
    assert exposure["data_availability"]["dem"] is True

    assert len(exposure["affected_villages"]) > 0, "Expected affected Nepal municipalities"
    assert exposure["affected_road_length_km"] is not None and exposure["affected_road_length_km"] > 0
    assert exposure["affected_population"] is not None and exposure["affected_population"] > 0

    # 4. Priority Scoring
    priority = ImpactScoringService().compute_priority_scores(exposure)
    assert len(priority) > 0
    assert priority[0]["priority_score"] >= 0.0

    # 5. Evacuation Candidates
    evac_svc = EvacuationService()
    evac = evac_svc.find_candidates(flood_geojson, repo, buffer_m=100.0)
    candidates = evac.get("candidates", [])
    assert len(candidates) > 0, "Expected safe evacuation candidates outside Nepal flood zone"
    
    # Verify elevation sampling from real DEM
    first_c = candidates[0]
    assert first_c["elevation_m"] is not None and first_c["elevation_m"] > 500.0, f"Expected Himalayan elevation, got {first_c['elevation_m']}"


def test_kerala_regression_gis_pipeline():
    """
    Ensure Kerala GIS workflow remains 100% functional without regressions.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(root_dir, "data")
    pre_path = os.path.join(data_dir, "test_images", "kerala_before_flood.tif")
    post_path = os.path.join(data_dir, "test_images", "kerala_after_flood.tif")

    det = FloodDetectionService().detect(pre_path, post_path)
    with rasterio.open(pre_path) as ds:
        poly = PolygonGenerationService().generate(det['mask_array'], ds.transform, ds.crs.to_wkt())

    flood_geojson = poly['geojson']
    repo = GISRepository(data_dir)

    exposure = ExposureAnalysisService().calculate_exposure(flood_geojson, "kerala", repo)
    assert exposure["data_availability"]["villages"] is True
    assert len(exposure["affected_villages"]) > 0
    assert exposure["affected_road_length_km"] is not None and exposure["affected_road_length_km"] > 0

    evac = EvacuationService().find_candidates(flood_geojson, repo, buffer_m=100.0)
    assert len(evac.get("candidates", [])) > 0
