"""
Unit and integration tests for Recovery Timeline + Satellite Monitoring (Sustainability Extension Part 5).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.recovery_monitoring import RecoveryMonitoringService
from app.schemas.recovery_monitoring import RecoveryMonitoringResult


@pytest.fixture
def sample_damage_assessment_data():
    """Sample Part 1 Damage Assessment data across 8 sectors."""
    return {
        "session_id": "test_mon_session_123",
        "region": "kerala",
        "categories": [
            {
                "category_id": "vegetation",
                "category_name": "Vegetation & Forest Cover",
                "category_type": "environmental",
                "severity": "Low",
                "affected_area_km2": 4.5,
                "recovery_classification": "Likely to recover naturally",
                "confidence_level": "High Confidence",
                "geographic_location": {"lat": 10.02, "lon": 76.35},
            },
            {
                "category_id": "agriculture",
                "category_name": "Agricultural Land & Crops",
                "category_type": "environmental",
                "severity": "Moderate",
                "affected_area_km2": 8.2,
                "recovery_classification": "Requires recovery assistance",
                "confidence_level": "High Confidence",
                "geographic_location": {"lat": 10.03, "lon": 76.36},
            },
            {
                "category_id": "water_wetlands",
                "category_name": "Water Bodies & Wetlands",
                "category_type": "environmental",
                "severity": "Low",
                "affected_area_km2": 12.0,
                "recovery_classification": "Likely to recover naturally",
                "confidence_level": "High Confidence",
                "geographic_location": {"lat": 10.04, "lon": 76.37},
            },
            {
                "category_id": "soil_land",
                "category_name": "Soil & Land Stability",
                "category_type": "environmental",
                "severity": "Moderate",
                "affected_area_km2": 6.1,
                "recovery_classification": "Requires recovery assistance",
                "confidence_level": "Moderate Confidence",
                "geographic_location": {"lat": 10.05, "lon": 76.38},
            },
            {
                "category_id": "habitats",
                "category_name": "Natural Habitats & Wildlife Corridors",
                "category_type": "environmental",
                "severity": "Moderate",
                "affected_area_km2": 3.4,
                "recovery_classification": "Requires field verification",
                "confidence_level": "Requires Field Verification",
                "geographic_location": {"lat": 10.06, "lon": 76.39},
            },
            {
                "category_id": "buildings",
                "category_name": "Residential & Commercial Buildings",
                "category_type": "infrastructure",
                "severity": "Critical",
                "affected_count": 54,
                "recovery_classification": "Severely / persistently damaged",
                "confidence_level": "High Confidence",
                "geographic_location": {"lat": 10.07, "lon": 76.40},
            },
            {
                "category_id": "roads",
                "category_name": "Roads & Transportation Network",
                "category_type": "infrastructure",
                "severity": "Severe",
                "affected_length_km": 12.4,
                "recovery_classification": "Requires recovery assistance",
                "confidence_level": "High Confidence",
                "geographic_location": {"lat": 10.08, "lon": 76.41},
            },
            {
                "category_id": "drainage",
                "category_name": "Drainage Channels & Stormwater",
                "category_type": "infrastructure",
                "severity": "Moderate",
                "affected_length_km": 7.8,
                "recovery_classification": "Requires recovery assistance",
                "confidence_level": "Moderate Confidence",
                "geographic_location": {"lat": 10.09, "lon": 76.42},
            },
        ],
    }


def test_recovery_monitoring_service_generates_all_sectors(sample_damage_assessment_data):
    """Verify that RecoveryMonitoringService constructs 8 timelines with multi-temporal checkpoints."""
    service = RecoveryMonitoringService()
    result = service.generate_recovery_timelines(
        damage_assessment=sample_damage_assessment_data,
        session_id="test_session",
        region="kerala",
    )

    validated = RecoveryMonitoringResult(**result)
    assert validated.summary.total_monitored_sectors == 8
    assert len(validated.timelines) == 8
    assert validated.summary.on_track_count + validated.summary.lagging_count + validated.summary.stalled_count + validated.summary.insufficient_data_count == 8

    # Verify each timeline has 4 observations (T+0, T+30d, T+90d, T+180d)
    for t in validated.timelines:
        assert len(t.observations) == 4
        stages = [o.timeline_stage for o in t.observations]
        assert "Immediate Post-Flood" in stages
        assert "1 Month Post-Flood" in stages
        assert "3 Months Post-Flood" in stages
        assert "6 Months Post-Flood" in stages
        assert t.recovery_score >= 0.0
        assert t.recovery_status in ("Recovery On Track", "Recovery Lagging", "Recovery Stalled", "Insufficient Data")


def test_recovery_monitoring_indicators_per_sector(sample_damage_assessment_data):
    """Verify specific satellite indicators for each sector."""
    service = RecoveryMonitoringService()
    result = service.generate_recovery_timelines(sample_damage_assessment_data)

    timelines_map = {t["category"]: t for t in result["timelines"]}

    # Vegetation should use NDVI
    assert "NDVI" in timelines_map["vegetation"]["primary_indicator_name"]
    # Agriculture should use SAVI
    assert "SAVI" in timelines_map["agriculture"]["primary_indicator_name"]
    # Water wetlands should use NDWI
    assert "NDWI" in timelines_map["water_wetlands"]["primary_indicator_name"]
    # Buildings should use SAR Backscatter
    assert "SAR" in timelines_map["buildings"]["primary_indicator_name"]
    # Roads should use optical clearance
    assert "Clearance" in timelines_map["roads"]["primary_indicator_name"] or "Transport" in timelines_map["roads"]["primary_indicator_name"]


def test_recovery_status_classification(sample_damage_assessment_data):
    """Verify status classification logic based on recovery score thresholds."""
    service = RecoveryMonitoringService()
    result = service.generate_recovery_timelines(sample_damage_assessment_data)

    for t in result["timelines"]:
        score = t["recovery_score"]
        status = t["recovery_status"]
        if score >= 65.0:
            assert status == "Recovery On Track"
        elif score >= 25.0:
            assert status == "Recovery Lagging"
        else:
            assert status == "Recovery Stalled"


def test_nepal_timeline_dates(sample_damage_assessment_data):
    """Verify Nepal 2026 event baseline observation date handling."""
    sample_damage_assessment_data["region"] = "nepal"
    service = RecoveryMonitoringService()
    result = service.generate_recovery_timelines(sample_damage_assessment_data, region="nepal")

    for t in result["timelines"]:
        assert "2026" in t["baseline_date"]
        assert "2026" in t["latest_observation_date"] or "2027" in t["latest_observation_date"]


def test_recovery_monitoring_endpoint(sample_damage_assessment_data):
    """Test FastAPI POST /api/v1/flood/monitoring endpoint."""
    from app.api.v1.endpoints.flood import _session_cache
    client = TestClient(app)

    session_id = "test_mon_endpoint_session"
    _session_cache[session_id] = {
        "damage_assessment": sample_damage_assessment_data,
    }

    response = client.post(
        "/api/v1/flood/monitoring",
        data={"session_id": session_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "summary" in data
    assert data["summary"]["total_monitored_sectors"] == 8
    assert len(data["timelines"]) == 8
    assert "disclaimer" in data
