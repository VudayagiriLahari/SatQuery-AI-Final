"""
Pydantic schemas for Recovery Priority Engine (Sustainability Extension Part 3).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContributingFactorsBreakdown(BaseModel):
    """Transparent breakdown of normalized scoring factors."""
    damage_severity_score: float = Field(..., description="Normalized damage severity score [0.0 - 1.0]")
    infrastructure_importance_score: float = Field(..., description="Normalized infrastructure criticality score [0.0 - 1.0]")
    population_impact_score: float = Field(..., description="Normalized population / community impact score [0.0 - 1.0]")
    ecological_importance_score: float = Field(..., description="Normalized ecological sensitivity score [0.0 - 1.0]")
    urgency_score: float = Field(..., description="Normalized urgency score [0.0 - 1.0]")
    natural_recovery_factor: float = Field(..., description="Multiplicative recovery modifier (lower for natural recovery)")


class SectorRecoveryPriority(BaseModel):
    """Prioritized recovery item for an affected sector or location."""
    category: str = Field(..., description="Unique category identifier (e.g. 'buildings', 'roads', 'vegetation')")
    category_name: str = Field(..., description="Human-readable sector title")
    category_type: str = Field(..., description="'environmental' or 'infrastructure'")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Centroid coordinates or geographic zone")
    priority_rank: int = Field(..., description="Rank position (1 = highest priority)")
    priority_score: float = Field(..., description="Normalized priority score in range [0.0, 10.0]")
    priority_level: str = Field(..., description="'HIGH', 'MEDIUM', or 'LOW'")
    damage_severity: str = Field(..., description="'Low', 'Moderate', 'Severe', 'Critical'")
    population_impact: str = Field(..., description="Qualitative / quantitative population impact description")
    ecological_importance: str = Field(..., description="'High', 'Moderate', 'Low'")
    infrastructure_importance: str = Field(..., description="'Critical', 'High', 'Moderate', 'Low'")
    natural_recovery_likelihood: str = Field(..., description="'High', 'Moderate', 'Low'")
    urgency: str = Field(..., description="'Immediate', 'Medium-Term', 'Routine Monitoring'")
    recommended_action: str = Field(..., description="Recommended sustainable action from Part 2")
    contributing_factors: ContributingFactorsBreakdown
    reason: str = Field(..., description="Clear evidence-based justification for assigned priority level")
    estimated_effort_level: str = Field(..., description="'High', 'Moderate', 'Low'")
    target_resource_domain: str = Field(..., description="Target recovery resource domain for Part 4 integration")


class RecoveryPrioritiesResult(BaseModel):
    """Consolidated Recovery Priority Engine result."""
    session_id: Optional[str] = None
    region: Optional[str] = None
    total_sectors_evaluated: int = 0
    high_priority_count: int = 0
    medium_priority_count: int = 0
    low_priority_count: int = 0
    priorities: List[SectorRecoveryPriority] = Field(default_factory=list)
    disclaimer: str = Field(
        default="Recovery priority scores are decision-support rankings derived from geospatial overlays and multi-criteria weighting. They are not deterministic administrative mandates.",
        description="Epistemic modesty disclaimer",
    )
