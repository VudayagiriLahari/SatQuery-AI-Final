"""
Unit and Integration tests for Post-Flood Environmental & Infrastructure Damage Assessment (Part 1).
"""

import pytest
import os
import json
from app.services.damage_assessment import DamageAssessmentService
from app.services.gis_repository import GISRepository
from app.schemas.damage_assessment import DamageAssessmentResult, DamageCategoryAssessment, DamageAssessmentSummary
from app.core.config import settings


@pytest.fixture
def synthetic_flood_geojson():
    """Create a synthetic flood GeoJSON in Kerala coordinates."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"area_km2": 3.5},
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


def test_damage_assessment_service_synthetic(synthetic_flood_geojson):
    """Test damage assessment service calculates all 8 categories with valid recovery classes."""
    gis_repo = GISRepository(settings.DATA_DIR)
    svc = DamageAssessmentService()
    
    result_dict = svc.assess_damage(
        flood_geojson=synthetic_flood_geojson,
        session_id="test_session_kerala",
        gis_repo=gis_repo,
        detection_result={"flood_area_km2": 3.5},
    )

    assert result_dict is not None
    assert "categories" in result_dict
    assert len(result_dict["categories"]) == 8

    # Verify Pydantic schema validation
    validated = DamageAssessmentResult(**result_dict)
    assert validated.session_id == "test_session_kerala"
    assert validated.summary.total_flood_area_km2 > 0

    valid_recovery_classes = {
        "Likely to recover naturally",
        "Requires recovery assistance",
        "Severely / persistently damaged",
        "Requires field verification",
    }

    # Verify all 8 categories have valid fields and recovery classifications
    category_ids = [c.category_id for c in validated.categories]
    expected_ids = [
        "vegetation",
        "agriculture",
        "water_wetlands",
        "soil_land",
        "habitats",
        "buildings",
        "roads",
        "drainage",
    ]
    for exp_id in expected_ids:
        assert exp_id in category_ids

    for cat in validated.categories:
        assert cat.recovery_classification in valid_recovery_classes
        assert cat.severity in {"Low", "Moderate", "Severe", "Critical"}
        assert cat.confidence_level in {"High", "Moderate", "Requires Field Verification"}
        assert len(cat.detected_change) > 10
        assert len(cat.recovery_notes) > 10


def test_damage_assessment_with_exposure_integration(synthetic_flood_geojson):
    """Test damage assessment integrates exposure result (e.g. 54 submerged buildings)."""
    gis_repo = GISRepository(settings.DATA_DIR)
    svc = DamageAssessmentService()

    mock_exposure = {
        "affected_buildings": 54,
        "affected_road_length_km": 14.85,
        "affected_buildings_geojson": {"type": "FeatureCollection", "features": []},
        "affected_roads_geojson": {"type": "FeatureCollection", "features": []},
    }

    result = svc.assess_damage(
        flood_geojson=synthetic_flood_geojson,
        session_id="kerala_demo",
        gis_repo=gis_repo,
        detection_result={"flood_area_km2": 5.2},
        exposure_result=mock_exposure,
    )

    validated = DamageAssessmentResult(**result)
    assert validated.summary.total_submerged_buildings == 54
    assert validated.summary.total_inundated_roads_km == 14.85

    # Check building category
    bld_cat = next(c for c in validated.categories if c.category_id == "buildings")
    assert bld_cat.affected_count == 54
    assert bld_cat.severity == "Critical"
    assert bld_cat.recovery_classification == "Requires recovery assistance"

    # Check road category
    road_cat = next(c for c in validated.categories if c.category_id == "roads")
    assert road_cat.affected_length_km == 14.85
    assert road_cat.severity == "Critical"
    assert road_cat.recovery_classification == "Requires recovery assistance"


def test_damage_assessment_nepal_region():
    """Test damage assessment correctly identifies Nepal region and layers."""
    gis_repo = GISRepository(settings.DATA_DIR)
    svc = DamageAssessmentService()

    nepal_flood_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"area_km2": 1.8},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [85.30, 28.10],
                            [85.35, 28.10],
                            [85.35, 28.15],
                            [85.30, 28.15],
                            [85.30, 28.10],
                        ]
                    ],
                },
            }
        ],
    }

    result = svc.assess_damage(
        flood_geojson=nepal_flood_geojson,
        session_id="nepal_demo",
        gis_repo=gis_repo,
        detection_result={"flood_area_km2": 1.8},
    )

    validated = DamageAssessmentResult(**result)
    assert validated.region == "nepal"
    assert validated.summary.total_flood_area_km2 == 1.8
    assert len(validated.disclaimers) >= 4


def test_damage_assessment_endpoint(synthetic_flood_geojson):
    """Test POST /api/v1/flood/damage-assessment endpoint with cached session."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.v1.endpoints.flood import _session_cache

    client = TestClient(app)
    session_id = "test_endpoint_session"
    _session_cache[session_id] = {
        "flood_geojson": synthetic_flood_geojson,
        "detection_result": {"flood_area_km2": 4.1},
        "impact": {
            "affected_buildings": 12,
            "affected_road_length_km": 5.4,
            "affected_buildings_geojson": None,
            "affected_roads_geojson": None,
        }
    }

    response = client.post("/api/v1/flood/damage-assessment", data={"session_id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert len(data["categories"]) == 8
    assert data["summary"]["total_submerged_buildings"] == 12
    assert data["summary"]["total_inundated_roads_km"] == 5.4

