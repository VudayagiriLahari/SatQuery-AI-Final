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


    # 5. Part 2: Recommendations
    from app.services.recovery_recommendation import RecoveryRecommendationService
    rec_svc = RecoveryRecommendationService()
    rec_res = rec_svc.generate_recommendations(dam_res, "kerala_e2e_test", "kerala")
    assert rec_res["total_recommendations"] == 8

    # 6. Part 3: Priorities
    from app.services.recovery_priority import RecoveryPriorityService
    prio_svc = RecoveryPriorityService()
    prio_res = prio_svc.compute_recovery_priorities(dam_res, rec_res, exp_res, "kerala_e2e_test", "kerala")
    assert prio_res["total_sectors_evaluated"] == 8
    assert prio_res["high_priority_count"] >= 1
    # Check that buildings is rank 1 or high
    bld_prio = next(p for p in prio_res["priorities"] if p["category"] == "buildings")
    assert bld_prio["priority_level"] == "HIGH"

    # 7. Part 4: Resource & Budget Optimization
    from app.services.resource_optimization import ResourceOptimizationService
    opt_svc = ResourceOptimizationService()
    opt_res = opt_svc.optimize_resources(prio_res, budget_lakhs=10.0, max_capacity_sites=5, session_id="kerala_e2e_test", region="kerala")
    assert opt_res["summary"]["allocated_budget_lakhs"] <= 10.0
    assert len(opt_res["selected_sites"]) > 0
    # 8. Part 5: Recovery Timeline & Satellite Monitoring
    from app.services.recovery_monitoring import RecoveryMonitoringService
    mon_svc = RecoveryMonitoringService()
    mon_res = mon_svc.generate_recovery_timelines(
        damage_assessment=dam_res,
        recovery_recommendations=rec_res,
        recovery_priorities=prio_res,
        resource_optimization=opt_res,
        session_id="kerala_e2e_test",
        region="kerala",
    )
    assert mon_res["summary"]["total_monitored_sectors"] == 8
    assert len(mon_res["timelines"]) == 8
    assert any(t["recovery_status"] == "Recovery On Track" for t in mon_res["timelines"])

    # 9. Part 6: Recovery Failure / Stall Diagnosis
    from app.services.recovery_diagnosis import RecoveryStallDiagnosisService
    diag_svc = RecoveryStallDiagnosisService()
    diag_res = diag_svc.diagnose_stalls(
        recovery_monitoring=mon_res,
        damage_assessment=dam_res,
        recovery_recommendations=rec_res,
        recovery_priorities=prio_res,
        session_id="kerala_e2e_test",
        region="kerala",
    )
    assert diag_res["summary"]["total_diagnosed_sectors"] == 8
    assert len(diag_res["diagnoses"]) == 8
    assert diag_res["summary"]["on_track_count"] >= 1


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

    # 5. Part 2 Recommendations & Part 3 Priorities & Part 4 Resource Optimization & Part 5 Monitoring & Part 6 Diagnosis
    from app.services.recovery_recommendation import RecoveryRecommendationService
    from app.services.recovery_priority import RecoveryPriorityService
    from app.services.resource_optimization import ResourceOptimizationService
    from app.services.recovery_monitoring import RecoveryMonitoringService
    from app.services.recovery_diagnosis import RecoveryStallDiagnosisService

    rec_res = RecoveryRecommendationService().generate_recommendations(dam_res, "nepal_e2e_test", "nepal")
    prio_res = RecoveryPriorityService().compute_recovery_priorities(dam_res, rec_res, exp_res, "nepal_e2e_test", "nepal")
    opt_res = ResourceOptimizationService().optimize_resources(prio_res, budget_lakhs=10.0, max_capacity_sites=5, session_id="nepal_e2e_test", region="nepal")
    mon_res = RecoveryMonitoringService().generate_recovery_timelines(dam_res, rec_res, prio_res, opt_res, "nepal_e2e_test", "nepal")
    diag_res = RecoveryStallDiagnosisService().diagnose_stalls(mon_res, dam_res, rec_res, prio_res, "nepal_e2e_test", "nepal")
    
    assert opt_res["summary"]["allocated_budget_lakhs"] <= 10.0
    assert len(opt_res["selected_sites"]) > 0
    assert mon_res["summary"]["total_monitored_sectors"] == 8
    assert diag_res["summary"]["total_diagnosed_sectors"] == 8
    assert len(diag_res["diagnoses"]) == 8


if __name__ == "__main__":
    test_e2e_kerala_damage_assessment()
    test_e2e_nepal_damage_assessment()
    print("ALL E2E DAMAGE ASSESSMENT TESTS PASSED!")


