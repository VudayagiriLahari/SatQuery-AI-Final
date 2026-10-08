"""
Pydantic schemas for Recovery Failure / Stall Diagnosis (Sustainability Extension Part 6).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PossibleCause(BaseModel):
    """A plausible evidence-based contributing cause for poor recovery trajectory."""
    cause: str = Field(..., description="Hypothesized root cause or physical mechanism (e.g., 'Persistent Waterlogging')")
    evidence: str = Field(..., description="Observed multi-temporal satellite/GIS evidence supporting this hypothesis")
    confidence: str = Field(
        ...,
        description="'High', 'Moderate', 'Low', or 'Requires Field Verification'",
    )


class StallDiagnosisItem(BaseModel):
    """Diagnostic evaluation for a single evaluated sector."""
    category: str = Field(..., description="Category identifier (e.g. 'habitats', 'buildings')")
    category_name: str = Field(..., description="Human-readable sector title")
    category_type: str = Field(..., description="'environmental' or 'infrastructure'")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Geographic centroid or bounding coordinates")
    recovery_status: str = Field(
        ...,
        description="'Recovery On Track', 'Recovery Lagging', 'Recovery Stalled', or 'Insufficient Data'",
    )
    recovery_score: float = Field(..., description="Observed or projected recovery progress [0.0 - 100.0%]")
    stall_detected: bool = Field(..., description="True if recovery is lagging, stalled, or anomalous")
    primary_indicator_name: str = Field(..., description="Primary sensor/spectral indicator used for evaluation")
    latest_observed_value: Optional[float] = Field(default=None, description="Latest numerical indicator value")
    baseline_value: Optional[float] = Field(default=None, description="Target pre-flood normal baseline value")
    possible_causes: List[PossibleCause] = Field(
        default_factory=list,
        description="Ranked list of plausible contributing factors backed by observable evidence",
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Bullet points detailing observable satellite spectral or structural evidence",
    )
    confidence: str = Field(
        ...,
        description="'High', 'Moderate', 'Low', or 'Requires Field Verification'",
    )
    field_verification_required: bool = Field(
        default=True,
        description="Whether on-ground field engineering or ecological survey is necessary",
    )
    data_is_simulated: bool = Field(
        default=False,
        description="True if diagnosis is derived from modeled progression rather than uploaded follow-up GeoTIFF rasters",
    )
    updated_recommendation: str = Field(
        ...,
        description="Actionable, sustainable adaptive decision-support recommendation",
    )
    notes: str = Field(..., description="Diagnostic context notes and epistemic caveats")


class RecoveryStallDiagnosisSummary(BaseModel):
    """Aggregate statistics for recovery failure and stall diagnosis."""
    total_diagnosed_sectors: int = Field(..., description="Total sectors evaluated")
    stalled_count: int = Field(..., description="Number of sectors classified as 'Recovery Stalled'")
    lagging_count: int = Field(..., description="Number of sectors classified as 'Recovery Lagging'")
    on_track_count: int = Field(..., description="Number of sectors classified as 'Recovery On Track'")
    insufficient_data_count: int = Field(..., description="Number of sectors with 'Insufficient Data'")
    stalled_or_lagging_count: int = Field(..., description="Total sectors requiring diagnostic attention (stalled + lagging)")
    requires_field_verification_count: int = Field(..., description="Sectors flagged for mandatory ground verification")


class RecoveryStallDiagnosisResult(BaseModel):
    """Consolidated result for Recovery Failure / Stall Diagnosis (Part 6)."""
    session_id: Optional[str] = None
    region: Optional[str] = None
    summary: RecoveryStallDiagnosisSummary
    diagnoses: List[StallDiagnosisItem] = Field(default_factory=list)
    methodology_notes: List[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "Recovery failure and stall diagnoses are automated decision-support hypotheses inferred from "
            "satellite spectral indices (NDVI, NDWI, NDTI), radar backscatter (SAR σ°), and GIS terrain overlays. "
            "They highlight potential environmental and infrastructural bottlenecks but do NOT replace in-situ "
            "civil engineering inspections, biological surveys, or official field investigations."
        ),
        description="Epistemic modesty disclaimer",
    )
