"""
Unit and integration tests for Resource / Budget Optimization (Sustainability Extension Part 4).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.resource_optimization import ResourceOptimizationService
from app.schemas.resource_optimization import ResourceOptimizationResult


@pytest.fixture
def sample_priorities_result():
    """Sample output from Part 3 Recovery Priority Engine."""
    return {
        "session_id": "test_session_opt_123",
        "region": "kerala",
        "total_sectors_evaluated": 8,
        "high_priority_count": 3,
        "medium_priority_count": 3,
        "low_priority_count": 2,
        "priorities": [
            {
                "category": "buildings",
                "category_name": "Residential & Commercial Buildings",
                "category_type": "infrastructure",
                "location": {"lat": 10.02, "lon": 76.35},
                "priority_rank": 1,
                "priority_score": 9.2,
                "priority_level": "HIGH",
                "damage_severity": "Critical",
                "population_impact": "54 submerged building footprints",
                "ecological_importance": "Low",
                "infrastructure_importance": "Critical",
                "natural_recovery_likelihood": "Low",
                "urgency": "Immediate",
                "recommended_action": "Structural integrity & habitability survey",
                "contributing_factors": {
                    "damage_severity_score": 1.0,
                    "infrastructure_importance_score": 1.0,
                    "population_impact_score": 1.0,
                    "ecological_importance_score": 0.1,
                    "urgency_score": 1.0,
                    "natural_recovery_factor": 1.0,
                },
                "reason": "Assigned HIGH priority (9.2/10) due to Critical structural inundation of 54 building footprints.",
                "estimated_effort_level": "High",
                "target_resource_domain": "Structural & Civil Engineering",
            },
            {
                "category": "roads",
                "category_name": "Roads & Transportation Network",
                "category_type": "infrastructure",
                "location": {"lat": 10.03, "lon": 76.36},
                "priority_rank": 2,
                "priority_score": 8.8,
                "priority_level": "HIGH",
                "damage_severity": "Severe",
                "population_impact": "12.4 km cutoff transport network",
                "ecological_importance": "Low",
                "infrastructure_importance": "Critical",
                "natural_recovery_likelihood": "Low",
                "urgency": "Immediate",
                "recommended_action": "Clear debris, desilt culverts, and repair sub-base",
                "contributing_factors": {
                    "damage_severity_score": 0.75,
                    "infrastructure_importance_score": 0.95,
                    "population_impact_score": 0.85,
                    "ecological_importance_score": 0.15,
                    "urgency_score": 1.0,
                    "natural_recovery_factor": 1.0,
                },
                "reason": "Assigned HIGH priority (8.8/10) due to Severe transport corridor submersion (12.4 km).",
                "estimated_effort_level": "High",
                "target_resource_domain": "Transportation & Highway Maintenance",
            },
            {
                "category": "drainage",
                "category_name": "Drainage Channels & Stormwater",
                "category_type": "infrastructure",
                "location": {"lat": 10.04, "lon": 76.37},
                "priority_rank": 3,
                "priority_score": 7.6,
                "priority_level": "HIGH",
                "damage_severity": "Moderate",
                "population_impact": "Drainage blockage posing high risk of urban waterlogging",
                "ecological_importance": "Moderate",
                "infrastructure_importance": "High",
                "natural_recovery_likelihood": "Low",
                "urgency": "Immediate",
                "recommended_action": "Mechanized desilting of major stormwater canals",
                "contributing_factors": {
                    "damage_severity_score": 0.45,
                    "infrastructure_importance_score": 0.85,
                    "population_impact_score": 0.70,
                    "ecological_importance_score": 0.40,
                    "urgency_score": 1.0,
                    "natural_recovery_factor": 1.0,
                },
                "reason": "Assigned HIGH priority (7.6/10) due to Moderate drainage siltation.",
                "estimated_effort_level": "Moderate",
                "target_resource_domain": "Municipal Drainage & Public Works",
            },
            {
                "category": "agriculture",
                "category_name": "Agricultural Land & Crops",
                "category_type": "environmental",
                "location": {"lat": 10.05, "lon": 76.38},
                "priority_rank": 4,
                "priority_score": 6.8,
                "priority_level": "MEDIUM",
                "damage_severity": "Moderate",
                "population_impact": "Farmland inundation directly threatening seasonal livelihood",
                "ecological_importance": "Moderate",
                "infrastructure_importance": "Moderate",
                "natural_recovery_likelihood": "Moderate",
                "urgency": "Medium-Term",
                "recommended_action": "Soil aeration and furrow de-siltation",
                "contributing_factors": {
                    "damage_severity_score": 0.45,
                    "infrastructure_importance_score": 0.60,
                    "population_impact_score": 0.75,
                    "ecological_importance_score": 0.60,
                    "urgency_score": 0.50,
                    "natural_recovery_factor": 0.85,
                },
                "reason": "Assigned MEDIUM priority (6.8/10) due to Moderate agricultural inundation.",
                "estimated_effort_level": "Moderate",
                "target_resource_domain": "Agronomic & Soil Conditioning",
            },
            {
                "category": "soil_land",
                "category_name": "Soil & Land Stability",
                "category_type": "environmental",
                "location": {"lat": 10.06, "lon": 76.39},
                "priority_rank": 5,
                "priority_score": 5.4,
                "priority_level": "MEDIUM",
                "damage_severity": "Moderate",
                "population_impact": "Lowland waterlogging and potential soil compaction",
                "ecological_importance": "High",
                "infrastructure_importance": "Moderate",
                "natural_recovery_likelihood": "Moderate",
                "urgency": "Medium-Term",
                "recommended_action": "Drainage swale clearing and bio-engineering slope stabilization",
                "contributing_factors": {
                    "damage_severity_score": 0.45,
                    "infrastructure_importance_score": 0.50,
                    "population_impact_score": 0.45,
                    "ecological_importance_score": 0.75,
                    "urgency_score": 0.50,
                    "natural_recovery_factor": 0.85,
                },
                "reason": "Assigned MEDIUM priority (5.4/10) due to Moderate waterlogging.",
                "estimated_effort_level": "Moderate",
                "target_resource_domain": "Land Stabilization & Bio-Engineering",
            },
            {
                "category": "habitats",
                "category_name": "Natural Habitats & Wildlife Corridors",
                "category_type": "environmental",
                "location": {"lat": 10.07, "lon": 76.40},
                "priority_rank": 6,
                "priority_score": 4.6,
                "priority_level": "MEDIUM",
                "damage_severity": "Moderate",
                "population_impact": "Riparian corridor buffer with biodiversity focus",
                "ecological_importance": "High",
                "infrastructure_importance": "Low",
                "natural_recovery_likelihood": "Moderate",
                "urgency": "Medium-Term",
                "recommended_action": "Ground biodiversity survey and fauna corridor verification",
                "contributing_factors": {
                    "damage_severity_score": 0.45,
                    "infrastructure_importance_score": 0.30,
                    "population_impact_score": 0.15,
                    "ecological_importance_score": 1.0,
                    "urgency_score": 0.50,
                    "natural_recovery_factor": 0.85,
                },
                "reason": "Assigned MEDIUM priority (4.6/10) because ecological riparian corridors require ground field verification.",
                "estimated_effort_level": "Low",
                "target_resource_domain": "Ecological Survey & Conservation",
            },
            {
                "category": "water_wetlands",
                "category_name": "Water Bodies & Wetlands",
                "category_type": "environmental",
                "location": {"lat": 10.08, "lon": 76.41},
                "priority_rank": 7,
                "priority_score": 2.2,
                "priority_level": "LOW",
                "damage_severity": "Low",
                "population_impact": "Natural retention overflow with low direct residential density",
                "ecological_importance": "High",
                "infrastructure_importance": "Low",
                "natural_recovery_likelihood": "High",
                "urgency": "Routine Monitoring",
                "recommended_action": "Passive wetland hydrological recovery and satellite monitoring",
                "contributing_factors": {
                    "damage_severity_score": 0.15,
                    "infrastructure_importance_score": 0.35,
                    "population_impact_score": 0.20,
                    "ecological_importance_score": 0.90,
                    "urgency_score": 0.10,
                    "natural_recovery_factor": 0.35,
                },
                "reason": "Assigned LOW priority (2.2/10) because Water Bodies exhibits High natural ecological recovery potential.",
                "estimated_effort_level": "Low",
                "target_resource_domain": "Hydrological Remote Sensing",
            },
            {
                "category": "vegetation",
                "category_name": "Vegetation & Forest Cover",
                "category_type": "environmental",
                "location": {"lat": 10.09, "lon": 76.42},
                "priority_rank": 8,
                "priority_score": 1.8,
                "priority_level": "LOW",
                "damage_severity": "Low",
                "population_impact": "General green cover inundation with low direct residential density",
                "ecological_importance": "High",
                "infrastructure_importance": "Low",
                "natural_recovery_likelihood": "High",
                "urgency": "Routine Monitoring",
                "recommended_action": "Passive satellite monitoring via Sentinel-2 NDVI time-series",
                "contributing_factors": {
                    "damage_severity_score": 0.15,
                    "infrastructure_importance_score": 0.25,
                    "population_impact_score": 0.20,
                    "ecological_importance_score": 0.85,
                    "urgency_score": 0.10,
                    "natural_recovery_factor": 0.35,
                },
                "reason": "Assigned LOW priority (1.8/10) because Vegetation exhibits High natural ecological recovery potential.",
                "estimated_effort_level": "Low",
                "target_resource_domain": "Satellite Vegetation Monitoring",
            },
        ],
    }


def test_resource_optimization_service_default_budget(sample_priorities_result):
    """Test optimization with standard ₹10 Lakhs budget and 5 sites constraint."""
    service = ResourceOptimizationService()
    result = service.optimize_resources(
        recovery_priorities=sample_priorities_result,
        budget_lakhs=10.0,
        max_capacity_sites=5,
        allow_natural_recovery_funding=False,
    )

    # Validate top-level schema conformance
    validated = ResourceOptimizationResult(**result)
    assert validated.summary.total_budget_lakhs == 10.0
    assert validated.summary.allocated_budget_lakhs <= 10.0
    assert validated.summary.remaining_budget_lakhs >= 0.0
    assert validated.summary.allocated_capacity_used <= 5
    assert len(validated.selected_sites) == validated.summary.allocated_capacity_used

    # Verify high priority structural sectors are allocated
    selected_cats = [s.category for s in validated.selected_sites]
    assert "buildings" in selected_cats
    assert "roads" in selected_cats
    assert "drainage" in selected_cats

    # Verify natural recovery sectors are deferred
    unselected_cats = [u.category for u in validated.unselected_sites]
    assert "vegetation" in unselected_cats
    assert "water_wetlands" in unselected_cats
    
    veg_unselected = next(u for u in validated.unselected_sites if u.category == "vegetation")
    assert "Natural Recovery Deferral" in veg_unselected.reason_deferred


def test_resource_optimization_service_small_budget(sample_priorities_result):
    """Test constrained small budget of ₹2.0 Lakhs."""
    service = ResourceOptimizationService()
    result = service.optimize_resources(
        recovery_priorities=sample_priorities_result,
        budget_lakhs=2.0,
        max_capacity_sites=5,
    )
    validated = ResourceOptimizationResult(**result)
    
    assert validated.summary.allocated_budget_lakhs <= 2.0
    assert validated.summary.remaining_budget_lakhs >= 0.0
    
    # Check that high cost items (like buildings ~₹4.38L or roads ~₹3.3L) are marked as exceeding budget
    unselected_reasons = {u.category: u.reason_deferred for u in validated.unselected_sites}
    assert "buildings" in unselected_reasons
    assert "Budget Limit" in unselected_reasons["buildings"]


def test_resource_optimization_service_capacity_limit(sample_priorities_result):
    """Test capacity constraint of 2 sites with high budget (₹50 Lakhs)."""
    service = ResourceOptimizationService()
    result = service.optimize_resources(
        recovery_priorities=sample_priorities_result,
        budget_lakhs=50.0,
        max_capacity_sites=2,
    )
    validated = ResourceOptimizationResult(**result)
    
    assert len(validated.selected_sites) == 2
    assert validated.summary.allocated_capacity_used == 2
    assert validated.summary.remaining_capacity_sites == 0
    
    # 3rd rank item (drainage) should be deferred due to capacity limit
    unselected_reasons = {u.category: u.reason_deferred for u in validated.unselected_sites}
    assert "drainage" in unselected_reasons
    assert "Capacity Limit" in unselected_reasons["drainage"]


def test_resource_optimization_service_domain_filter(sample_priorities_result):
    """Test domain filtering (e.g. only transportation)."""
    service = ResourceOptimizationService()
    result = service.optimize_resources(
        recovery_priorities=sample_priorities_result,
        budget_lakhs=20.0,
        max_capacity_sites=5,
        domain_filter="Transportation",
    )
    validated = ResourceOptimizationResult(**result)
    
    # Only roads should be selected
    assert len(validated.selected_sites) == 1
    assert validated.selected_sites[0].category == "roads"
    assert "Transportation" in validated.selected_sites[0].target_resource_domain


def test_resource_optimization_service_allow_natural_recovery(sample_priorities_result):
    """Test allowing funding for natural recovery items when enabled with large budget."""
    service = ResourceOptimizationService()
    result = service.optimize_resources(
        recovery_priorities=sample_priorities_result,
        budget_lakhs=30.0,
        max_capacity_sites=8,
        allow_natural_recovery_funding=True,
    )
    validated = ResourceOptimizationResult(**result)
    
    selected_cats = [s.category for s in validated.selected_sites]
    assert "vegetation" in selected_cats or "water_wetlands" in selected_cats


def test_optimize_resources_endpoint(sample_priorities_result):
    """Test FastAPI POST /api/v1/flood/optimize-resources endpoint."""
    from app.api.v1.endpoints.flood import _session_cache
    client = TestClient(app)

    session_id = "test_opt_endpoint_session"
    _session_cache[session_id] = {
        "recovery_priorities": sample_priorities_result,
    }

    response = client.post(
        "/api/v1/flood/optimize-resources",
        data={
            "session_id": session_id,
            "budget_lakhs": 15.0,
            "max_capacity_sites": 4,
            "allow_natural_recovery": "false",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "summary" in data
    assert data["summary"]["total_budget_lakhs"] == 15.0
    assert data["summary"]["total_capacity_sites"] == 4
    assert len(data["selected_sites"]) > 0
    assert len(data["unselected_sites"]) > 0
    assert "disclaimer" in data
    assert "decision-support" in data["disclaimer"].lower()
