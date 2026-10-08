"""
End-to-End verification script for Sustainability Extension Part 1: Damage Assessment.
"""

import os
import json
import pytest
from app.services.flood_detection import FloodDetectionService
from app.services.polygon_generation import PolygonGenerationService
from app.services.exposure_analysis import ExposureAnalysisService
from app.services.evacuation import EvacuationService
from app.services.damage_assessment import DamageAssessmentService
from app.services.gis_repository import GISRepository
from app.core.config import settings


def test_e2e_kerala_damage_assessment():
    """Verify complete Kerala flood pipeline and damage assessment."""
    gis_repo = GISRepository(settings.DATA_DIR)
    
    pre_path = os.path.join(settings.DATA_DIR, "test_images", "kerala_before_flood.tif")
    post_path = os.path.join(settings.DATA_DIR, "test_images", "kerala_after_flood.tif")
    
    # 1. Detection
    det_svc = FloodDetectionService()
    det_res = det_svc.detect(pre_path, post_path, {"method": "auto", "morphology_iterations": 2})
    assert det_res["success"] is True
    mask_array = det_res["mask_array"]
    
    # 2. Polygonize
    import rasterio
    with rasterio.open(pre_path) as ds:
        transform = ds.transform
        crs_wkt = ds.crs.to_wkt() if ds.crs else "EPSG:4326"
    
    poly_svc = PolygonGenerationService()
    poly_res = poly_svc.generate(mask_array, transform, crs_wkt, 0.0001)
    assert poly_res["success"] is True
    flood_geojson = poly_res["geojson"]
    
    # 3. Exposure
    exp_svc = ExposureAnalysisService()
    exp_res = exp_svc.calculate_exposure(flood_geojson, "kerala", gis_repo)
    assert exp_res["affected_buildings"] == 54, f"Expected 54 buildings for Kerala, got {exp_res['affected_buildings']}"
    
    # 4. Damage Assessment
    dam_svc = DamageAssessmentService()
    dam_res = dam_svc.assess_damage(
        flood_geojson=flood_geojson,
        session_id="kerala_e2e_test",
        gis_repo=gis_repo,
        pre_path=pre_path,
        post_path=post_path,
        detection_result=det_res,
        exposure_result=exp_res,
    )
    
    assert dam_res["summary"]["total_submerged_buildings"] == 54
    assert len(dam_res["categories"]) == 8
    
    # Check all recovery classes
    valid_classes = {
        "Likely to recover naturally",
        "Requires recovery assistance",
        "Severely / persistently damaged",
        "Requires field verification",
    }
    for cat in dam_res["categories"]:
        assert cat["recovery_classification"] in valid_classes
        print(f"[{cat['category_type'].upper()}] {cat['category_name']}: {cat['recovery_classification']} (Severity: {cat['severity']})")


def test_e2e_nepal_damage_assessment():
    """Verify complete Nepal flood pipeline and damage assessment."""
    gis_repo = GISRepository(settings.DATA_DIR)
    
    pre_path = os.path.join(settings.DATA_DIR, "test_images", "nepal_before_flood.tif")
    post_path = os.path.join(settings.DATA_DIR, "test_images", "nepal_after_flood.tif")
    
    # 1. Detection
    det_svc = FloodDetectionService()
    det_res = det_svc.detect(pre_path, post_path, {"method": "auto", "morphology_iterations": 2})
    assert det_res["success"] is True
    mask_array = det_res["mask_array"]
    
    # 2. Polygonize
    import rasterio
    with rasterio.open(pre_path) as ds:
        transform = ds.transform
        crs_wkt = ds.crs.to_wkt() if ds.crs else "EPSG:4326"
    
    poly_svc = PolygonGenerationService()
    poly_res = poly_svc.generate(mask_array, transform, crs_wkt, 0.0001)
    assert poly_res["success"] is True
    flood_geojson = poly_res["geojson"]
    
    # 3. Exposure
    exp_svc = ExposureAnalysisService()
    exp_res = exp_svc.calculate_exposure(flood_geojson, "nepal", gis_repo)
    
    # 4. Damage Assessment
    dam_svc = DamageAssessmentService()
    dam_res = dam_svc.assess_damage(
        flood_geojson=flood_geojson,
        session_id="nepal_e2e_test",
        gis_repo=gis_repo,
        pre_path=pre_path,
        post_path=post_path,
        detection_result=det_res,
        exposure_result=exp_res,
    )
    
    assert dam_res["region"] == "nepal"
    assert len(dam_res["categories"]) == 8
    print("Nepal damage assessment categories passed!")


if __name__ == "__main__":
    test_e2e_kerala_damage_assessment()
    test_e2e_nepal_damage_assessment()
    print("ALL E2E DAMAGE ASSESSMENT TESTS PASSED!")
