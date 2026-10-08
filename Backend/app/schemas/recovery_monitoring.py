"""
Pydantic schemas for Recovery Timeline + Satellite-Based Recovery Monitoring (Sustainability Extension Part 5).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RecoveryObservation(BaseModel):
    """A single dated satellite/geospatial observation for a monitored sector."""
    date: str = Field(..., description="Observation date (ISO string or formatted date)")
    timeline_stage: str = Field(
        ...,
        description="'Immediate Post-Flood', '1 Month Post-Flood', '3 Months Post-Flood', '6 Months Post-Flood', or custom date",
    )
    indicator_name: str = Field(..., description="Name of geospatial/spectral indicator (e.g. 'Sentinel-2 NDVI', 'SAR Backscatter σ°')")
    value: float = Field(..., description="Observed quantitative indicator value")
    baseline_value: float = Field(..., description="Reference pre-flood or post-flood baseline value")
    change_from_baseline: float = Field(..., description="Observed delta from immediate post-flood condition")
    recovery_percentage: float = Field(..., description="Estimated recovery progress [0.0% - 100.0%] toward pre-flood normal")
    interpretation: str = Field(..., description="Physical evidence-based interpretation of observable change")


class MonitoredSectorTimeline(BaseModel):
    """Complete multi-temporal recovery timeline for an evaluated sector."""
    category: str = Field(..., description="Category identifier (e.g. 'buildings', 'vegetation')")
    category_name: str = Field(..., description="Human-readable sector title")
    category_type: str = Field(..., description="'environmental' or 'infrastructure'")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Geographic coordinates or centroid")
    baseline_date: str = Field(..., description="Event flood baseline date")
    latest_observation_date: str = Field(..., description="Timestamp of the most recent satellite observation")
    recovery_status: str = Field(
        ...,
        description="'Recovery On Track', 'Recovery Lagging', 'Recovery Stalled', or 'Insufficient Data'",
    )
    recovery_score: float = Field(..., description="Composite recovery score [0.0 - 100.0]")
    latest_condition: str = Field(..., description="Qualitative summary of latest observable state")
    primary_indicator_name: str = Field(..., description="Primary indicator used for monitoring this category")
    change_detected: bool = Field(..., description="Whether significant positive change has been observed")
    confidence: str = Field(..., description="'High', 'Moderate', 'Low', or 'Requires Field Verification'")
    data_available: bool = Field(..., description="Whether satellite observation data is available")
    field_verification_required: bool = Field(..., description="Whether in-situ ground inspection is necessary")
    funded_in_part4: bool = Field(default=False, description="Whether sector was funded in Part 4 budget allocation")
    observations: List[RecoveryObservation] = Field(default_factory=list, description="Chronological satellite observation sequence")
    notes: str = Field(..., description="Detailed timeline justification and progression notes")


class RecoveryMonitoringSummary(BaseModel):
    """Aggregate statistics for recovery monitoring across all evaluated sectors."""
    total_monitored_sectors: int = Field(..., description="Total sectors tracked")
    on_track_count: int = Field(..., description="Count of sectors classified as 'Recovery On Track'")
    lagging_count: int = Field(..., description="Count of sectors classified as 'Recovery Lagging'")
    stalled_count: int = Field(..., description="Count of sectors classified as 'Recovery Stalled'")
    insufficient_data_count: int = Field(..., description="Count of sectors with 'Insufficient Data'")
    average_recovery_score: float = Field(..., description="Mean recovery progress percentage across all tracked sectors")
    total_observations_recorded: int = Field(..., description="Total observation timestamps recorded across all timelines")
    latest_observation_date: str = Field(..., description="Most recent observation date across all timelines")


class RecoveryMonitoringResult(BaseModel):
    """Consolidated result for Recovery Timeline + Satellite-Based Recovery Monitoring (Part 5)."""
    session_id: Optional[str] = None
    region: Optional[str] = None
    summary: RecoveryMonitoringSummary
    timelines: List[MonitoredSectorTimeline] = Field(default_factory=list)
    methodology_notes: List[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "Satellite-derived recovery indicators reflect observable spectral indices (NDVI, NDWI, NDTI) and "
            "radar backscatter (SAR σ°) over time. They quantify visible land-surface and structural restoration "
            "trends but do not constitute comprehensive ground engineering or biological certifications without "
            "in-situ physical field verification."
        ),
        description="Epistemic modesty disclaimer",
    )
