"""
Unit and Integration tests for Recovery Priority Engine (Part 3).
"""

import pytest
import os
import json
from app.services.damage_assessment import DamageAssessmentService
from app.services.recovery_recommendation import RecoveryRecommendationService
from app.services.recovery_priority import RecoveryPriorityService
from app.services.gis_repository import GISRepository
from app.schemas.recovery_priority import RecoveryPrioritiesResult, SectorRecoveryPriority
from app.core.config import settings


@pytest.fixture
def synthetic_pipeline_outputs():
    """Create synthetic damage assessment and recovery recommendation dictionaries."""
    gis_repo = GISRepository(settings.DATA_DIR)
    dam_svc = DamageAssessmentService()
    rec_svc = RecoveryRecommendationService()

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
        "affected_road_length_km": 14.85,
        "affected_buildings_geojson": None,
        "affected_roads_geojson": None,
    }

    damage_dict = dam_svc.assess_damage(
        flood_geojson=synthetic_flood_geojson,
        session_id="test_prio_session",
        gis_repo=gis_repo,
        detection_result={"flood_area_km2": 4.5},
        exposure_result=mock_exposure,
    )

    rec_dict = rec_svc.generate_recommendations(
        damage_assessment=damage_dict,
        session_id="test_prio_session",
        region="kerala",
    )

    return damage_dict, rec_dict, mock_exposure


def test_recovery_priority_service_scoring_and_ranking(synthetic_pipeline_outputs):
    """Test priority engine scores, ranks, and classifies all sectors accurately."""
    damage_dict, rec_dict, mock_exposure = synthetic_pipeline_outputs
    prio_svc = RecoveryPriorityService()

    result = prio_svc.compute_recovery_priorities(
        damage_assessment=damage_dict,
        recovery_recommendations=rec_dict,
        exposure_data=mock_exposure,
        session_id="test_prio_session",
        region="kerala",
    )

    assert result is not None
    assert "priorities" in result
    assert result["total_sectors_evaluated"] == 8

    validated = RecoveryPrioritiesResult(**result)
    assert validated.session_id == "test_prio_session"
    assert validated.region == "kerala"
    assert validated.total_sectors_evaluated == 8

    # Verify rank sorting
    scores = [p.priority_score for p in validated.priorities]
    assert scores == sorted(scores, reverse=True), "Priorities must be strictly sorted by score descending"
    for i, p in enumerate(validated.priorities):
        assert p.priority_rank == i + 1

    # Verify HIGH, MEDIUM, LOW presence
    assert validated.high_priority_count > 0, "Must have HIGH priority sectors (e.g. buildings, roads)"
    assert validated.low_priority_count > 0, "Must have LOW priority sectors (natural recovery sectors)"

    # Verify that naturally recovering sectors (vegetation, wetlands) receive LOW priority
    veg_prio = next(p for p in validated.priorities if p.category == "vegetation")
    assert veg_prio.priority_level == "LOW"
    assert veg_prio.natural_recovery_likelihood == "High"
    assert "natural" in veg_prio.reason.lower() or "passive" in veg_prio.reason.lower()

    wetlands_prio = next(p for p in validated.priorities if p.category == "water_wetlands")
    assert wetlands_prio.priority_level == "LOW"
    assert wetlands_prio.natural_recovery_likelihood == "High"

    # Verify critical infrastructure receives HIGH priority
    bld_prio = next(p for p in validated.priorities if p.category == "buildings")
    assert bld_prio.priority_level == "HIGH"
    assert bld_prio.priority_score >= 7.0
    assert "54" in bld_prio.population_impact or "buildings" in bld_prio.reason.lower()

    road_prio = next(p for p in validated.priorities if p.category == "roads")
    assert road_prio.priority_level == "HIGH"
    assert road_prio.priority_score >= 7.0


def test_contributing_factors_and_reasons(synthetic_pipeline_outputs):
    """Verify each sector provides transparent factor weights and clear justification."""
    damage_dict, rec_dict, mock_exposure = synthetic_pipeline_outputs
    prio_svc = RecoveryPriorityService()

    result = prio_svc.compute_recovery_priorities(
        damage_assessment=damage_dict,
        recovery_recommendations=rec_dict,
        exposure_data=mock_exposure,
        session_id="test_prio_session",
        region="kerala",
    )
    validated = RecoveryPrioritiesResult(**result)

    for item in validated.priorities:
        assert item.contributing_factors.damage_severity_score >= 0.0
        assert item.contributing_factors.infrastructure_importance_score >= 0.0
        assert item.contributing_factors.population_impact_score >= 0.0
        assert item.contributing_factors.ecological_importance_score >= 0.0
        assert item.contributing_factors.urgency_score >= 0.0
        assert item.contributing_factors.natural_recovery_factor > 0.0
        assert len(item.reason) > 20, "Must provide clear plain-language explanation"
        assert len(item.target_resource_domain) > 3, "Must assign resource domain for Part 4"
        assert item.estimated_effort_level in {"High", "Moderate", "Low"}


def test_priorities_endpoint(synthetic_pipeline_outputs):
    """Test POST /api/v1/flood/priorities endpoint."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.v1.endpoints.flood import _session_cache

    damage_dict, rec_dict, mock_exposure = synthetic_pipeline_outputs
    client = TestClient(app)
    session_id = "test_prio_endpoint_session"
    _session_cache[session_id] = {
        "damage_assessment": damage_dict,
        "recovery_recommendations": rec_dict,
        "impact": mock_exposure,
    }

    response = client.post("/api/v1/flood/priorities", data={"session_id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["total_sectors_evaluated"] == 8
    assert len(data["priorities"]) == 8
    assert data["high_priority_count"] >= 1
    assert data["low_priority_count"] >= 1
