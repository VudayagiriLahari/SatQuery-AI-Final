"""
Pydantic schemas for Natural Recovery Assessment & Sustainable Recovery Recommendation Engine (Part 2).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RecoveryRecommendation(BaseModel):
    """Structured decision-support recovery recommendation for a damaged sector."""
    category: str = Field(..., description="Unique category key, e.g. 'vegetation', 'buildings'")
    category_name: str = Field(..., description="Human-readable sector title")
    category_type: str = Field(..., description="'environmental' or 'infrastructure'")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Geographic centroid coordinates or region")
    damage_severity: str = Field(..., description="Severity rating: 'Low', 'Moderate', 'Severe', 'Critical'")
    recovery_classification: str = Field(
        ...,
        description="Recovery condition: 'Likely Natural Recovery', 'Recovery Assistance Needed', 'Severely/Persistently Damaged', 'Field Verification Required'",
    )
    recommended_action: str = Field(..., description="Recommended sustainable recovery action")
    intervention_type: str = Field(..., description="'monitoring', 'assisted_regeneration', 'repair', 'rehabilitation', 'land_stabilization', 'wetland_restoration', 'inspection', 'maintenance', 'field_assessment'")
    reason: str = Field(..., description="Evidence-based reasoning explaining why this specific action is recommended")
    confidence: str = Field(..., description="'High', 'Moderate', or 'Requires Field Verification'")
    requires_field_verification: bool = Field(..., description="Whether on-ground validation is needed prior to action")
    sustainable_practices: List[str] = Field(default_factory=list, description="Recommended sustainable / nature-based recovery techniques")
    urgency: str = Field(..., description="'Immediate', 'Medium-Term', or 'Routine Monitoring'")


class RecoveryRecommendationsResult(BaseModel):
    """Consolidated recovery assessment and recommendation engine output."""
    session_id: Optional[str] = None
    region: Optional[str] = None
    total_recommendations: int = 0
    natural_recovery_count: int = Field(0, description="Count of sectors where natural recovery is sufficient and no active intervention is needed")
    intervention_needed_count: int = Field(0, description="Count of sectors requiring active human assistance or repair")
    field_verification_count: int = Field(0, description="Count of sectors requiring on-ground physical inspection")
    recommendations: List[RecoveryRecommendation] = Field(default_factory=list)
    disclaimer: str = Field(
        default="Recommendations are decision-support guidelines derived from satellite observations and available GIS layers. They are not guaranteed instructions and must be validated by local authorities and licensed engineers.",
        description="Epistemic modesty and decision-support disclaimer",
    )
