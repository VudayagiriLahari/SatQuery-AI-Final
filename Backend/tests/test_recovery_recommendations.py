"""
Unit and Integration tests for Natural Recovery Assessment & Sustainable Recovery Recommendation Engine (Part 2).
"""

import pytest
import os
import json
from app.services.damage_assessment import DamageAssessmentService
from app.services.recovery_recommendation import RecoveryRecommendationService
from app.services.gis_repository import GISRepository
from app.schemas.recovery_recommendation import RecoveryRecommendationsResult, RecoveryRecommendation
from app.core.config import settings


@pytest.fixture
def synthetic_damage_assessment():
    """Create a synthetic damage assessment dictionary for testing."""
    gis_repo = GISRepository(settings.DATA_DIR)
    dam_svc = DamageAssessmentService()
    synthetic_flood_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"area_km2": 4.5},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [76.35, 10.15],
                            [76.40, 10.15],
                            [76.40, 10.20],
                            [76.35, 10.20],
                            [76.35, 10.15],
                        ]
                    ],
                },
            }
        ],
    }
    mock_exposure = {
        "affected_buildings": 54,
        "affected_road_length_km": 12.3,
        "affected_buildings_geojson": None,
        "affected_roads_geojson": None,
    }
    return dam_svc.assess_damage(
        flood_geojson=synthetic_flood_geojson,
        session_id="test_rec_session",
        gis_repo=gis_repo,
        detection_result={"flood_area_km2": 4.5},
        exposure_result=mock_exposure,
    )


def test_recovery_recommendation_service_generates_all_sectors(synthetic_damage_assessment):
    """Test recommendation service evaluates all sectors with structured reasons and actions."""
    rec_svc = RecoveryRecommendationService()
    result = rec_svc.generate_recommendations(
        damage_assessment=synthetic_damage_assessment,
        session_id="test_rec_session",
        region="kerala",
    )

    assert result is not None
    assert "recommendations" in result
    assert result["total_recommendations"] == 8

    validated = RecoveryRecommendationsResult(**result)
    assert validated.session_id == "test_rec_session"
    assert validated.region == "kerala"
    assert validated.total_recommendations == 8
    assert validated.natural_recovery_count > 0, "System must recognize sectors capable of natural recovery"
    assert validated.intervention_needed_count > 0, "System must identify sectors requiring human assistance"

    allowed_conditions = {
        "Likely Natural Recovery",
        "Recovery Assistance Needed",
        "Severely/Persistently Damaged",
        "Field Verification Required",
    }

    for rec in validated.recommendations:
        assert rec.recovery_classification in allowed_conditions
        assert len(rec.recommended_action) > 5
        assert len(rec.reason) > 20, "Every recommendation must provide an evidence-based justification"
        assert rec.confidence in {"High", "Moderate", "Requires Field Verification"}
        assert isinstance(rec.requires_field_verification, bool)
        assert len(rec.sustainable_practices) > 0, "Must include nature-based / sustainable techniques"
        assert rec.urgency in {"Immediate", "Medium-Term", "Routine Monitoring"}


def test_natural_recovery_distinction(synthetic_damage_assessment):
    """Verify system does NOT assume every damaged area needs human intervention."""
    rec_svc = RecoveryRecommendationService()
    result = rec_svc.generate_recommendations(
        damage_assessment=synthetic_damage_assessment,
        session_id="test_rec_session",
        region="kerala",
    )

    validated = RecoveryRecommendationsResult(**result)
    
    # Vegetation & Water/Wetlands should have natural recovery / passive monitoring
    veg_rec = next(r for r in validated.recommendations if r.category == "vegetation")
    assert veg_rec.recovery_classification == "Likely Natural Recovery"
    assert veg_rec.intervention_type == "monitoring"
    assert "Passive" in veg_rec.recommended_action or "Monitoring" in veg_rec.recommended_action
    assert veg_rec.requires_field_verification is False

    wetlands_rec = next(r for r in validated.recommendations if r.category == "water_wetlands")
    assert wetlands_rec.recovery_classification == "Likely Natural Recovery"
    assert wetlands_rec.intervention_type == "monitoring"

    # Buildings & Roads should have active intervention needed
    bld_rec = next(r for r in validated.recommendations if r.category == "buildings")
    assert bld_rec.recovery_classification == "Recovery Assistance Needed"
    assert bld_rec.requires_field_verification is True
    assert "Inspection" in bld_rec.recommended_action or "Rehabilitation" in bld_rec.recommended_action

    road_rec = next(r for r in validated.recommendations if r.category == "roads")
    assert road_rec.recovery_classification == "Recovery Assistance Needed"
    assert road_rec.requires_field_verification is True


def test_recommendations_endpoint(synthetic_damage_assessment):
    """Test POST /api/v1/flood/recommendations endpoint."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.v1.endpoints.flood import _session_cache

    client = TestClient(app)
    session_id = "test_endpoint_rec_session"
    _session_cache[session_id] = {
        "damage_assessment": synthetic_damage_assessment,
    }

    response = client.post("/api/v1/flood/recommendations", data={"session_id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert len(data["recommendations"]) == 8
    assert data["total_recommendations"] == 8
    assert data["natural_recovery_count"] >= 1
