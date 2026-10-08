"""
Pydantic schemas for Post-Flood Environmental & Infrastructure Damage Assessment (Sustainability Extension Part 1).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DamageCategoryAssessment(BaseModel):
    """Assessment of a single environmental or infrastructure category."""
    category_id: str = Field(..., description="Unique category identifier, e.g. 'vegetation', 'buildings'")
    category_name: str = Field(..., description="Human-readable category title")
    category_type: str = Field(..., description="'environmental' or 'infrastructure'")
    affected_area_km2: Optional[float] = Field(default=None, description="Affected area in square kilometers")
    affected_count: Optional[int] = Field(default=None, description="Count of physical assets affected (e.g. buildings)")
    affected_length_km: Optional[float] = Field(default=None, description="Length of linear infrastructure affected in km")
    severity: str = Field(..., description="Severity rating: 'Low', 'Moderate', 'Severe', 'Critical'")
    detected_change: str = Field(..., description="Physical or spectral change description")
    geographic_location: Optional[Dict[str, Any]] = Field(default=None, description="Centroid or spatial extent coordinates")
    confidence_level: str = Field(..., description="'High', 'Moderate', or 'Requires Field Verification'")
    recovery_classification: str = Field(
        ...,
        description="Recovery class: 'Likely to recover naturally', 'Requires recovery assistance', 'Severely / persistently damaged', or 'Requires field verification'",
    )
    recovery_notes: str = Field(..., description="Recovery trajectory, intervention recommendations, or monitoring guidance")
    geojson: Optional[Dict[str, Any]] = Field(default=None, description="GeoJSON FeatureCollection for spatial rendering")
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Additional quantitative sector metrics")


class DamageAssessmentSummary(BaseModel):
    """Consolidated summary metrics across all evaluated damage categories."""
    total_flood_area_km2: float = Field(0.0, description="Total detected flood inundation area in km²")
    total_environmental_damage_area_km2: float = Field(0.0, description="Total affected environmental land area in km²")
    total_submerged_buildings: Optional[int] = Field(default=None, description="Total submerged building footprint count")
    total_inundated_roads_km: Optional[float] = Field(default=None, description="Total inundated road length in km")
    recovery_breakdown: Dict[str, int] = Field(
        default_factory=lambda: {
            "Likely to recover naturally": 0,
            "Requires recovery assistance": 0,
            "Severely / persistently damaged": 0,
            "Requires field verification": 0,
        },
        description="Count of evaluated categories under each recovery classification",
    )


class DamageAssessmentResult(BaseModel):
    """Complete Post-Flood Environmental & Infrastructure Damage Assessment output."""
    session_id: Optional[str] = None
    region: Optional[str] = None
    summary: DamageAssessmentSummary = Field(default_factory=DamageAssessmentSummary)
    categories: List[DamageCategoryAssessment] = Field(default_factory=list)
    data_availability: Dict[str, bool] = Field(
        default_factory=lambda: {
            "satellite_raster": False,
            "dem_elevation": False,
            "buildings_osm": False,
            "roads_osm": False,
            "administrative_boundaries": False,
            "wetlands_hydrology": False,
        }
    )
    disclaimers: List[str] = Field(
        default_factory=lambda: [
            "Assessments are derived from satellite observations and available GIS layers.",
            "Epistemic modesty standard: No specific crop species or biological mortality is asserted without in-situ ground validation.",
            "No chemical or biological water contamination is inferred without physical laboratory water-quality testing.",
            "Physical structural safety and re-occupancy require certified on-site engineering inspections.",
        ]
    )
