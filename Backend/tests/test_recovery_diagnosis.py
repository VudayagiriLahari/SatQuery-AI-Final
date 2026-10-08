"""
Unit and integration tests for Recovery Failure / Stall Diagnosis (Sustainability Extension Part 6).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.recovery_diagnosis import RecoveryStallDiagnosisService
from app.services.recovery_monitoring import RecoveryMonitoringService
from app.services.damage_assessment import DamageAssessmentService
from app.services.gis_repository import GISRepository
from app.core.config import settings

client = TestClient(app)


def test_recovery_stall_diagnosis_service_basic():
    """Verify diagnostic evaluation on standard Part 5 monitoring output."""
    sample_monitoring = {
        "session_id": "test_sess_p6",
        "region": "kerala",
        "summary": {
            "total_monitored_sectors": 3,
            "on_track_count": 2,
            "lagging_count": 1,
            "stalled_count": 0,
            "insufficient_data_count": 0,
            "average_recovery_score": 75.0,
            "total_observations_recorded": 12,
            "latest_observation_date": "2025-02-15",
        },
        "timelines": [
            {
                "category": "vegetation",
                "category_name": "Vegetation & Forest Cover",
                "category_type": "environmental",
                "location": {"lat": 10.15, "lon": 76.45},
                "baseline_date": "2024-08-15",
                "latest_observation_date": "2025-02-15",
                "recovery_status": "Recovery On Track",
                "recovery_score": 93.5,
                "latest_condition": "Recovery is on track with 93.5% observable trajectory.",
                "primary_indicator_name": "Sentinel-2 NDVI",
                "change_detected": True,
                "confidence": "High",
                "data_available": True,
                "field_verification_required": False,
                "data_is_simulated": True,
                "funded_in_part4": False,
                "observations": [
                    {"date": "2024-08-15", "timeline_stage": "Immediate", "indicator_name": "Sentinel-2 NDVI", "value": 0.28, "baseline_value": 0.74, "change_from_baseline": 0.0, "recovery_percentage": 0.0, "interpretation": "Drop"},
                    {"date": "2025-02-15", "timeline_stage": "6 Months", "indicator_name": "Sentinel-2 NDVI", "value": 0.71, "baseline_value": 0.74, "change_from_baseline": 0.43, "recovery_percentage": 93.5, "interpretation": "Regrowth"},
                ],
                "notes": "Fast natural regrowth.",
            },
            {
                "category": "habitats",
                "category_name": "Wildlife & Riverine Habitats",
                "category_type": "environmental",
                "location": {"lat": 10.18, "lon": 76.48},
                "baseline_date": "2024-08-15",
                "latest_observation_date": "2025-02-15",
                "recovery_status": "Recovery Lagging",
                "recovery_score": 59.1,
                "latest_condition": "Recovery is lagging at 59.1% progress.",
                "primary_indicator_name": "Multispectral Riparian Corridor Coherence Index",
                "change_detected": True,
                "confidence": "Moderate",
                "data_available": True,
                "field_verification_required": True,
                "data_is_simulated": True,
                "funded_in_part4": False,
                "observations": [
                    {"date": "2024-08-15", "timeline_stage": "Immediate", "indicator_name": "Multispectral Riparian Corridor Coherence Index", "value": 0.38, "baseline_value": 0.82, "change_from_baseline": 0.0, "recovery_percentage": 0.0, "interpretation": "Drop"},
                    {"date": "2025-02-15", "timeline_stage": "6 Months", "indicator_name": "Multispectral Riparian Corridor Coherence Index", "value": 0.64, "baseline_value": 0.82, "change_from_baseline": 0.26, "recovery_percentage": 59.1, "interpretation": "Slow recovery"},
                ],
                "notes": "Riparian buffer regrowth is naturally slow.",
            },
            {
                "category": "drainage",
                "category_name": "Drainage & Stormwater Channels",
                "category_type": "infrastructure",
                "location": {"lat": 10.12, "lon": 76.42},
                "baseline_date": "2024-08-15",
                "latest_observation_date": "2025-02-15",
                "recovery_status": "Recovery Stalled",
                "recovery_score": 18.5,
                "latest_condition": "Recovery has stalled at 18.5% progress.",
                "primary_indicator_name": "Stormwater Channel Silt Inundation & Flow Capacity Index",
                "change_detected": False,
                "confidence": "High",
                "data_available": True,
                "field_verification_required": False,
                "data_is_simulated": True,
                "funded_in_part4": False,
                "observations": [
                    {"date": "2024-08-15", "timeline_stage": "Immediate", "indicator_name": "Stormwater Channel Silt Inundation & Flow Capacity Index", "value": 0.18, "baseline_value": 0.88, "change_from_baseline": 0.0, "recovery_percentage": 0.0, "interpretation": "Silt blockage"},
                    {"date": "2025-02-15", "timeline_stage": "6 Months", "indicator_name": "Stormwater Channel Silt Inundation & Flow Capacity Index", "value": 0.31, "baseline_value": 0.88, "change_from_baseline": 0.13, "recovery_percentage": 18.5, "interpretation": "Severe residual silt"},
                ],
                "notes": "Drainage bottleneck.",
            },
        ],
    }

    service = RecoveryStallDiagnosisService()
    res = service.diagnose_stalls(
        recovery_monitoring=sample_monitoring,
        session_id="test_sess_p6",
        region="kerala",
    )

    assert res["session_id"] == "test_sess_p6"
    assert res["region"] == "kerala"
    assert "summary" in res
    assert "diagnoses" in res
    assert len(res["diagnoses"]) == 3

    sum_obj = res["summary"]
    assert sum_obj["total_diagnosed_sectors"] == 3
    assert sum_obj["stalled_count"] == 1
    assert sum_obj["lagging_count"] == 1
    assert sum_obj["on_track_count"] == 1
    assert sum_obj["stalled_or_lagging_count"] == 2

    # Verify on-track vegetation
    veg = next(d for d in res["diagnoses"] if d["category"] == "vegetation")
    assert veg["stall_detected"] is False
    assert len(veg["possible_causes"]) == 0
    assert "routine" in veg["updated_recommendation"].lower()

    # Verify lagging habitats
    hab = next(d for d in res["diagnoses"] if d["category"] == "habitats")
    assert hab["stall_detected"] is True
    assert len(hab["possible_causes"]) >= 1
    assert any("riparian" in c["cause"].lower() for c in hab["possible_causes"])
    assert hab["field_verification_required"] is True
    assert "biodiversity" in hab["updated_recommendation"].lower() or "riparian" in hab["updated_recommendation"].lower()

    # Verify stalled drainage
    drain = next(d for d in res["diagnoses"] if d["category"] == "drainage")
    assert drain["stall_detected"] is True
    assert len(drain["possible_causes"]) >= 1
    assert any("silt" in c["cause"].lower() or "drainage" in c["cause"].lower() for c in drain["possible_causes"])
    assert "desilting" in drain["updated_recommendation"].lower() or "dredging" in drain["updated_recommendation"].lower()


def test_epistemic_modesty_and_simulation_transparency():
    """Verify that all diagnoses use epistemic modesty and flag simulated data."""
    sample_monitoring = {
        "session_id": "test_modesty",
        "region": "nepal",
        "timelines": [
            {
                "category": "buildings",
                "category_name": "Urban & Rural Buildings",
                "category_type": "infrastructure",
                "location": {"lat": 28.1, "lon": 85.3},
                "baseline_date": "2026-07-28",
                "latest_observation_date": "2027-01-28",
                "recovery_status": "Recovery Lagging",
                "recovery_score": 45.0,
                "latest_condition": "Recovery lagging.",
                "primary_indicator_name": "Sentinel-1 SAR Double-Bounce Backscatter σ°",
                "change_detected": True,
                "confidence": "Moderate",
                "data_available": True,
                "field_verification_required": True,
                "data_is_simulated": True,
                "observations": [
                    {"date": "2026-07-28", "timeline_stage": "Immediate", "indicator_name": "SAR σ°", "value": -13.2, "baseline_value": -5.4, "change_from_baseline": 0.0, "recovery_percentage": 0.0, "interpretation": "Drop"},
                    {"date": "2027-01-28", "timeline_stage": "6 Months", "indicator_name": "SAR σ°", "value": -9.5, "baseline_value": -5.4, "change_from_baseline": 3.7, "recovery_percentage": 45.0, "interpretation": "Lagging"},
                ],
                "notes": "Lagging reconstruction.",
            }
        ]
    }

    service = RecoveryStallDiagnosisService()
    res = service.diagnose_stalls(sample_monitoring, session_id="test_modesty", region="nepal")
    diag = res["diagnoses"][0]

    assert diag["data_is_simulated"] is True
    assert "preliminary model indicator" in diag["notes"].lower() or "model" in diag["notes"].lower()

    # Verify cause phrasing contains epistemic humility
    for cause in diag["possible_causes"]:
        ev = cause["evidence"].lower()
        assert "evidence suggests" in ev or "possible" in ev or "may" in ev or "indicates" in ev


def test_insufficient_data_diagnosis_handling():
    """Verify handling of missing satellite observations."""
    sample_monitoring = {
        "session_id": "test_nodata",
        "region": "kerala",
        "timelines": [
            {
                "category": "roads",
                "category_name": "Road Network",
                "category_type": "infrastructure",
                "recovery_status": "Insufficient Data",
                "recovery_score": 0.0,
                "latest_condition": "No clear post-flood scenes available.",
                "primary_indicator_name": "Optical Transport Clearance",
                "data_available": False,
                "field_verification_required": True,
                "data_is_simulated": False,
                "observations": [],
                "notes": "Cloud cover.",
            }
        ]
    }

    service = RecoveryStallDiagnosisService()
    res = service.diagnose_stalls(sample_monitoring)
    diag = res["diagnoses"][0]

    assert diag["recovery_status"] == "Insufficient Data"
    assert diag["stall_detected"] is False
    assert diag["field_verification_required"] is True
    assert any("insufficient" in c["cause"].lower() or "cloud" in c["cause"].lower() for c in diag["possible_causes"])


def test_diagnosis_endpoint_with_session():
    """Verify POST /api/v1/flood/diagnosis endpoint."""
    from app.api.v1.endpoints.flood import _session_cache

    test_sess_id = "test_endpoint_session_p6"
    _session_cache[test_sess_id] = {
        "damage_assessment": {
            "session_id": test_sess_id,
            "region": "kerala",
            "categories": [
                {
                    "category_id": "vegetation",
                    "category_name": "Vegetation & Forest Cover",
                    "category_type": "environmental",
                    "severity": "Low",
                    "recovery_classification": "Likely Natural Recovery",
                    "geographic_location": {"lat": 10.15, "lon": 76.45},
                },
                {
                    "category_id": "habitats",
                    "category_name": "Wildlife & Riverine Habitats",
                    "category_type": "environmental",
                    "severity": "Moderate",
                    "recovery_classification": "Recovery Assistance Needed",
                    "geographic_location": {"lat": 10.18, "lon": 76.48},
                },
            ],
            "summary": {"total_categories_evaluated": 2},
        },
        "recovery_recommendations": {
            "session_id": test_sess_id,
            "region": "kerala",
            "total_recommendations": 2,
            "recommendations": [],
        },
        "recovery_priorities": {
            "session_id": test_sess_id,
            "region": "kerala",
            "total_sectors_evaluated": 2,
            "priorities": [],
        },
        "resource_optimization": {
            "session_id": test_sess_id,
            "region": "kerala",
            "summary": {},
            "selected_sites": [],
        },
        "recovery_monitoring": {
            "session_id": test_sess_id,
            "region": "kerala",
            "summary": {
                "total_monitored_sectors": 2,
                "on_track_count": 1,
                "lagging_count": 1,
                "stalled_count": 0,
                "insufficient_data_count": 0,
                "average_recovery_score": 76.3,
                "total_observations_recorded": 8,
                "latest_observation_date": "2025-02-15",
            },
            "timelines": [
                {
                    "category": "vegetation",
                    "category_name": "Vegetation & Forest Cover",
                    "category_type": "environmental",
                    "location": {"lat": 10.15, "lon": 76.45},
                    "baseline_date": "2024-08-15",
                    "latest_observation_date": "2025-02-15",
                    "recovery_status": "Recovery On Track",
                    "recovery_score": 93.5,
                    "latest_condition": "Recovery is on track with 93.5% observable trajectory.",
                    "primary_indicator_name": "Sentinel-2 NDVI",
                    "change_detected": True,
                    "confidence": "High",
                    "data_available": True,
                    "field_verification_required": False,
                    "data_is_simulated": True,
                    "funded_in_part4": False,
                    "observations": [],
                    "notes": "Natural recovery.",
                },
                {
                    "category": "habitats",
                    "category_name": "Wildlife & Riverine Habitats",
                    "category_type": "environmental",
                    "location": {"lat": 10.18, "lon": 76.48},
                    "baseline_date": "2024-08-15",
                    "latest_observation_date": "2025-02-15",
                    "recovery_status": "Recovery Lagging",
                    "recovery_score": 59.1,
                    "latest_condition": "Recovery is lagging at 59.1% progress.",
                    "primary_indicator_name": "Multispectral Riparian Corridor Coherence Index",
                    "change_detected": True,
                    "confidence": "Moderate",
                    "data_available": True,
                    "field_verification_required": True,
                    "data_is_simulated": True,
                    "funded_in_part4": False,
                    "observations": [],
                    "notes": "Riparian buffer regrowth is naturally slow.",
                },
            ],
            "methodology_notes": [],
            "disclaimer": "Disclaimer",
        },
    }

    try:
        response = client.post(
            "/api/v1/flood/diagnosis",
            data={"session_id": test_sess_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == test_sess_id
        assert data["summary"]["total_diagnosed_sectors"] == 2
        assert data["summary"]["lagging_count"] == 1
        assert len(data["diagnoses"]) == 2
        assert "disclaimer" in data
    finally:
        if test_sess_id in _session_cache:
            del _session_cache[test_sess_id]
