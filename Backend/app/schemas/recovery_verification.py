"""
Pydantic schemas for Recovery Verification (Sustainability Extension Part 7).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SectorRecoveryVerificationItem(BaseModel):
    """Detailed recovery verification evaluation for a single evaluated sector."""
    category: str = Field(..., description="Category identifier (e.g. 'vegetation', 'buildings')")
    category_name: str = Field(..., description="Human-readable sector title")
    category_type: str = Field(..., description="'environmental' or 'infrastructure'")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Geographic coordinates or centroid")
    original_damage: str = Field(..., description="Summary of initial flood damage from Part 1")
    damage_severity: str = Field(..., description="Severity level ('Low', 'Moderate', 'Severe', 'Critical')")
    recommended_intervention: str = Field(..., description="Recommended sustainable action from Part 2")
    funded_or_selected: bool = Field(default=False, description="Whether sector was selected/funded in Part 4 optimization")
    baseline_observation: Optional[str] = Field(default=None, description="Baseline event condition description and date")
    latest_observation: Optional[str] = Field(default=None, description="Latest observation date and state")
    indicator: str = Field(..., description="Name of geospatial/spectral indicator used for verification")
    baseline_value: Optional[float] = Field(default=None, description="Post-flood baseline numerical value")
    target_baseline_value: Optional[float] = Field(default=None, description="Pre-flood normal baseline benchmark")
    latest_value: Optional[float] = Field(default=None, description="Latest observed quantitative value")
    measured_change: Optional[float] = Field(default=None, description="Numerical delta between baseline and latest value")
    expected_recovery_direction: str = Field(
        ...,
        description="'Increasing (Toward Pre-Flood Baseline)' or 'Decreasing (Receding Toward Normal)'",
    )
    verification_status: str = Field(
        ...,
        description="'VERIFIED RECOVERY', 'PARTIAL / IMPROVING', 'NOT VERIFIED', or 'INSUFFICIENT DATA'",
    )
    evidence: str = Field(..., description="Physical and sensor evidence supporting the verification decision")
    confidence: str = Field(
        ...,
        description="'High', 'Moderate', 'Low', or 'Requires Field Verification'",
    )
    field_verification_required: bool = Field(
        default=True,
        description="Whether in-situ physical ground inspection is mandatory",
    )
    data_is_simulated: bool = Field(
        default=False,
        description="True if evaluation relies on modeled projection rather than empirical follow-up rasters",
    )
    verification_notes: str = Field(..., description="Detailed verification remarks, caveats, and next steps")
    # Interoperability alias fields for frontend UI integration
    recommended_action: Optional[str] = Field(default=None, description="Alias for recommended_intervention")
    primary_indicator_name: Optional[str] = Field(default=None, description="Alias for indicator")
    latest_observed_value: Optional[float] = Field(default=None, description="Alias for latest_value")
    observable_recovery_percentage: Optional[float] = Field(default=None, description="Percentage restoration toward baseline")
    expected_direction: Optional[str] = Field(default=None, description="Alias for expected_recovery_direction")
    physical_evidence: Optional[str] = Field(default=None, description="Alias for evidence")
    resource_allocation_status: Optional[str] = Field(default=None, description="Contextual resource funding description from Part 4")
    recovery_diagnosis_status: Optional[str] = Field(default=None, description="Diagnosis status from Part 6")
    allocated_budget_lakhs: Optional[float] = Field(default=None, description="Allocated budget in Lakhs if funded")


class RecoveryVerificationSummary(BaseModel):
    """Aggregate statistics for recovery verification across all evaluated sectors."""
    total_evaluated_sectors: int = Field(..., description="Total sectors evaluated for verification")
    verified_recovery_count: int = Field(..., description="Count of sectors with 'VERIFIED RECOVERY'")
    partial_improving_count: int = Field(..., description="Count of sectors with 'PARTIAL / IMPROVING'")
    not_verified_count: int = Field(..., description="Count of sectors with 'NOT VERIFIED'")
    insufficient_data_count: int = Field(..., description="Count of sectors with 'INSUFFICIENT DATA'")
    simulated_projections_count: int = Field(..., description="Count of sectors based on modeled/simulated data")
    requires_field_verification_count: int = Field(..., description="Count of sectors requiring mandatory in-situ verification")


class RecoveryVerificationResult(BaseModel):
    """Consolidated result for Recovery Verification (Part 7)."""
    session_id: Optional[str] = None
    region: Optional[str] = None
    summary: RecoveryVerificationSummary
    verifications: List[SectorRecoveryVerificationItem] = Field(default_factory=list)
    methodology_notes: List[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "Recovery verification evaluates whether observable spectral indicators (NDVI, NDWI, NDTI) and "
            "radar backscatter (SAR σ°) demonstrate measurable improvement toward pre-flood baselines. "
            "Modeled projections are transparently categorized as 'INSUFFICIENT DATA' for real verification. "
            "Satellite-derived verification reflects visible surface changes and does NOT constitute complete "
            "civil structural certification or biological ecosystem restoration without physical on-ground inspection."
        ),
        description="Epistemic modesty disclaimer",
    )
