"""
Unit and integration tests for Recovery Verification (Sustainability Extension Part 7).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.recovery_verification import RecoveryVerificationService
from app.core.config import settings

client = TestClient(app)


def test_simulated_only_data_yields_insufficient_data():
    """
    STRICT DATA INTEGRITY REQUIREMENT:
    Simulated/modeled Part 5 observations must NEVER be marked as VERIFIED RECOVERY.
    They must be classified as 'INSUFFICIENT DATA'.
    """
    sample_damage = {
        "session_id": "test_sim_integrity",
        "region": "kerala",
        "categories": [
            {
                "category_id": "vegetation",
                "category_name": "Vegetation & Forest Cover",
                "category_type": "environmental",
                "severity": "Low",
                "damage_description": "Canopy stripping along river banks.",
                "recovery_notes": "Passive natural regrowth.",
            },
            {
                "category_id": "buildings",
                "category_name": "Urban & Rural Buildings",
                "category_type": "infrastructure",
                "severity": "Critical",
                "damage_description": "54 flooded structures.",
                "recovery_notes": "Structural repair and drying.",
            }
        ]
    }

    sample_monitoring = {
        "timelines": [
            {
                "category": "vegetation",
                "primary_indicator_name": "Sentinel-2 NDVI",
                "data_is_simulated": True,  # Modeled projection
                "recovery_score": 93.5,
                "observations": [
                    {"date": "2024-08-15", "value": 0.28, "baseline_value": 0.74},
                    {"date": "2025-02-15", "value": 0.71, "baseline_value": 0.74},
                ]
            },
            {
                "category": "buildings",
                "primary_indicator_name": "Sentinel-1 SAR Double-Bounce Backscatter σ°",
                "data_is_simulated": True,  # Modeled projection
                "recovery_score": 93.6,
                "observations": [
                    {"date": "2024-08-15", "value": -13.2, "baseline_value": -5.4},
                    {"date": "2025-02-15", "value": -5.9, "baseline_value": -5.4},
                ]
            }
        ]
    }

    service = RecoveryVerificationService()
    res = service.verify_recovery(
        damage_assessment=sample_damage,
        recovery_monitoring=sample_monitoring,
        session_id="test_sim_integrity",
        region="kerala",
    )

    assert res["summary"]["total_evaluated_sectors"] == 2
    assert res["summary"]["verified_recovery_count"] == 0, "Simulated data MUST NOT yield verified recovery!"
    assert res["summary"]["insufficient_data_count"] == 2

    for item in res["verifications"]:
        assert item["verification_status"] == "INSUFFICIENT DATA"
        assert item["data_is_simulated"] is True
        assert "modeled projection" in item["evidence"].lower()


def test_empirical_followup_verified_recovery():
    """
    When valid empirical follow-up satellite observations are available,
    measurable improvement (≥80% toward baseline) yields VERIFIED RECOVERY.
    """
    sample_damage = {
        "session_id": "test_empirical_verified",
        "region": "kerala",
        "categories": [
            {
                "category_id": "vegetation",
                "category_name": "Vegetation & Forest Cover",
                "category_type": "environmental",
                "severity": "Low",
                "damage_description": "Canopy stripping.",
                "recovery_notes": "Assisted reforestation.",
            }
        ]
    }

    sample_monitoring = {
        "timelines": [
            {
                "category": "vegetation",
                "primary_indicator_name": "Sentinel-2 NDVI",
                "data_is_simulated": False,  # Real empirical follow-up
                "observations": [
                    {"date": "2024-08-15", "value": 0.28, "baseline_value": 0.74},
                    {"date": "2025-02-15", "value": 0.70, "baseline_value": 0.74},  # Progress = (0.70-0.28)/(0.74-0.28) = 91.3%
                ]
            }
        ]
    }

    service = RecoveryVerificationService()
    res = service.verify_recovery(
        damage_assessment=sample_damage,
        recovery_monitoring=sample_monitoring,
        session_id="test_empirical_verified",
        region="kerala",
    )

    assert res["summary"]["verified_recovery_count"] == 1
    veg = res["verifications"][0]
    assert veg["verification_status"] == "VERIFIED RECOVERY"
    assert veg["data_is_simulated"] is False
    assert veg["expected_recovery_direction"] == "Increasing (Toward Pre-Flood Baseline)"
    assert "confirms" in veg["evidence"].lower() or "restoration" in veg["evidence"].lower()


def test_empirical_followup_partial_improving():
    """
    When empirical follow-up observations show partial progress (25% - 79%),
    status is PARTIAL / IMPROVING.
    """
    sample_damage = {
        "session_id": "test_empirical_partial",
        "region": "kerala",
        "categories": [
            {
                "category_id": "roads",
                "category_name": "Road Network",
                "category_type": "infrastructure",
                "severity": "Moderate",
                "damage_description": "Corridor silt inundation.",
                "recovery_notes": "Mechanized debris clearing.",
            }
        ]
    }

    sample_monitoring = {
        "timelines": [
            {
                "category": "roads",
                "primary_indicator_name": "Optical Transport Corridor Clearance",
                "data_is_simulated": False,  # Real empirical follow-up
                "observations": [
                    {"date": "2024-08-15", "value": 0.16, "baseline_value": 0.92},
                    {"date": "2024-10-15", "value": 0.54, "baseline_value": 0.92},  # Progress = (0.54-0.16)/(0.92-0.16) = 50.0%
                ]
            }
        ]
    }

    service = RecoveryVerificationService()
    res = service.verify_recovery(
        damage_assessment=sample_damage,
        recovery_monitoring=sample_monitoring,
    )

    assert res["summary"]["partial_improving_count"] == 1
    road = res["verifications"][0]
    assert road["verification_status"] == "PARTIAL / IMPROVING"
    assert road["field_verification_required"] is True


def test_empirical_followup_not_verified():
    """
    When empirical follow-up observations show lack of expected progress (<25% or deterioration),
    status is NOT VERIFIED.
    """
    sample_damage = {
        "session_id": "test_empirical_not_verified",
        "region": "kerala",
        "categories": [
            {
                "category_id": "drainage",
                "category_name": "Drainage Channels",
                "category_type": "infrastructure",
                "severity": "Severe",
                "damage_description": "Canal silt blockage.",
                "recovery_notes": "Canal dredging.",
            }
        ]
    }

    sample_monitoring = {
        "timelines": [
            {
                "category": "drainage",
                "primary_indicator_name": "Flow Capacity Index",
                "data_is_simulated": False,  # Real empirical follow-up
                "observations": [
                    {"date": "2024-08-15", "value": 0.18, "baseline_value": 0.88},
                    {"date": "2024-11-15", "value": 0.20, "baseline_value": 0.88},  # Progress = (0.20-0.18)/(0.88-0.18) = 2.8% (<25%)
                ]
            }
        ]
    }

    service = RecoveryVerificationService()
    res = service.verify_recovery(
        damage_assessment=sample_damage,
        recovery_monitoring=sample_monitoring,
    )

    assert res["summary"]["not_verified_count"] == 1
    drain = res["verifications"][0]
    assert drain["verification_status"] == "NOT VERIFIED"
    assert drain["field_verification_required"] is True


def test_inverted_domain_direction_ndwi():
    """
    Verify inverted indicator direction (e.g. NDWI water extent receding toward 0.32 from 0.82).
    """
    sample_damage = {
        "session_id": "test_inverted_direction",
        "region": "kerala",
        "categories": [
            {
                "category_id": "water_wetlands",
                "category_name": "Water Bodies & Wetlands",
                "category_type": "environmental",
                "severity": "Severe",
                "damage_description": "Overland flood expansion.",
                "recovery_notes": "Natural recession.",
            }
        ]
    }

    sample_monitoring = {
        "timelines": [
            {
                "category": "water_wetlands",
                "primary_indicator_name": "Sentinel-2 NDWI",
                "data_is_simulated": False,  # Real empirical follow-up
                "observations": [
                    {"date": "2024-08-15", "value": 0.82, "baseline_value": 0.32},  # Post-flood surge at 0.82
                    {"date": "2025-02-15", "value": 0.35, "baseline_value": 0.32},  # Dropped back to 0.35 -> Progress = (0.82-0.35)/(0.82-0.32) = 94.0%
                ]
            }
        ]
    }

    service = RecoveryVerificationService()
    res = service.verify_recovery(
        damage_assessment=sample_damage,
        recovery_monitoring=sample_monitoring,
    )

    water = res["verifications"][0]
    assert water["expected_recovery_direction"] == "Decreasing (Receding Toward Normal)"
    assert water["verification_status"] == "VERIFIED RECOVERY"


def test_verification_endpoint_with_session():
    """Verify POST /api/v1/flood/verification endpoint."""
    from app.api.v1.endpoints.flood import _session_cache

    test_sess_id = "test_endpoint_session_p7"
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
                    "damage_description": "Canopy stripping.",
                    "recovery_notes": "Natural regrowth.",
                },
            ],
            "summary": {"total_categories_evaluated": 1},
        },
        "recovery_recommendations": {
            "session_id": test_sess_id,
            "region": "kerala",
            "recommendations": [
                {
                    "category_id": "vegetation",
                    "recommended_action": "Passive Regeneration",
                }
            ],
        },
        "recovery_priorities": {
            "session_id": test_sess_id,
            "region": "kerala",
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
                "total_monitored_sectors": 1,
                "on_track_count": 1,
                "lagging_count": 0,
                "stalled_count": 0,
                "insufficient_data_count": 0,
                "average_recovery_score": 93.5,
                "total_observations_recorded": 2,
                "latest_observation_date": "2025-02-15",
            },
            "timelines": [
                {
                    "category": "vegetation",
                    "category_name": "Vegetation & Forest Cover",
                    "category_type": "environmental",
                    "recovery_status": "Recovery On Track",
                    "recovery_score": 93.5,
                    "primary_indicator_name": "Sentinel-2 NDVI",
                    "data_is_simulated": True,
                    "observations": [
                        {"date": "2024-08-15", "value": 0.28, "baseline_value": 0.74},
                        {"date": "2025-02-15", "value": 0.71, "baseline_value": 0.74},
                    ],
                    "notes": "Natural regrowth.",
                },
            ],
        },
        "recovery_diagnosis": {
            "session_id": test_sess_id,
            "region": "kerala",
            "summary": {},
            "diagnoses": [],
        },
    }

    try:
        response = client.post(
            "/api/v1/flood/verification",
            data={"session_id": test_sess_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == test_sess_id
        assert data["summary"]["total_evaluated_sectors"] == 1
        assert data["summary"]["insufficient_data_count"] == 1  # Modeled data is marked INSUFFICIENT DATA
        assert len(data["verifications"]) == 1
        assert "disclaimer" in data
    finally:
        if test_sess_id in _session_cache:
            del _session_cache[test_sess_id]
