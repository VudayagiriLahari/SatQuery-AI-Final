"""
Pydantic schemas for Resource / Budget Optimization (Sustainability Extension Part 4).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AllocatedSectorSite(BaseModel):
    """An affected sector/site selected and funded in the resource allocation simulation."""
    category: str = Field(..., description="Category identifier (e.g. 'buildings', 'roads')")
    category_name: str = Field(..., description="Human-readable sector title")
    category_type: str = Field(..., description="'environmental' or 'infrastructure'")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Geographic coordinates or centroid")
    priority_rank: int = Field(..., description="Rank position from Part 3 priority engine")
    priority_score: float = Field(..., description="Normalized priority score [0.0 - 10.0]")
    priority_level: str = Field(..., description="'HIGH', 'MEDIUM', or 'LOW'")
    estimated_cost_lakhs: float = Field(..., description="Hypothetical estimated cost in ₹ Lakhs")
    allocated_budget_lakhs: float = Field(..., description="Hypothetical allocated funds in ₹ Lakhs")
    estimated_effort_level: str = Field(..., description="'High', 'Moderate', 'Low'")
    expected_benefit_score: float = Field(..., description="Quantified multi-criteria benefit contribution")
    recommended_action: str = Field(..., description="Recommended sustainable action from Part 2")
    target_resource_domain: str = Field(..., description="Resource / engineering domain")
    allocation_reason: str = Field(..., description="Clear transparent justification for funding this intervention")


class UnallocatedSectorSite(BaseModel):
    """An affected sector/site not funded or deferred under current resource constraints."""
    category: str = Field(..., description="Category identifier")
    category_name: str = Field(..., description="Human-readable sector title")
    category_type: str = Field(..., description="'environmental' or 'infrastructure'")
    priority_rank: int = Field(..., description="Rank position from Part 3 priority engine")
    priority_score: float = Field(..., description="Normalized priority score [0.0 - 10.0]")
    priority_level: str = Field(..., description="'HIGH', 'MEDIUM', or 'LOW'")
    estimated_cost_lakhs: float = Field(..., description="Hypothetical estimated cost in ₹ Lakhs")
    reason_deferred: str = Field(..., description="Reason intervention is deferred or unselected under constraints")
    recommended_action: str = Field(..., description="Recommended action or passive monitoring")


class ResourceOptimizationSummary(BaseModel):
    """High-level summary of resource optimization budget and capacity distribution."""
    total_budget_lakhs: float = Field(..., description="Total hypothetical budget available in ₹ Lakhs")
    allocated_budget_lakhs: float = Field(..., description="Total budget allocated to selected interventions in ₹ Lakhs")
    remaining_budget_lakhs: float = Field(..., description="Remaining unallocated budget in ₹ Lakhs")
    budget_utilization_pct: float = Field(..., description="Percentage of available budget utilized")
    total_capacity_sites: int = Field(..., description="Maximum allowed simultaneous intervention sites")
    allocated_capacity_used: int = Field(..., description="Number of intervention sites funded")
    remaining_capacity_sites: int = Field(..., description="Unused intervention capacity")
    expected_total_benefit: float = Field(..., description="Cumulative benefit score achieved by allocation")
    allocation_strategy: str = Field(
        default="Multi-Criteria Knapsack with Natural Recovery Deferral",
        description="Optimization heuristic strategy employed",
    )


class ResourceOptimizationResult(BaseModel):
    """Consolidated Resource / Budget Optimization result."""
    session_id: Optional[str] = None
    region: Optional[str] = None
    summary: ResourceOptimizationSummary
    selected_sites: List[AllocatedSectorSite] = Field(default_factory=list)
    unselected_sites: List[UnallocatedSectorSite] = Field(default_factory=list)
    allocation_notes: List[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "Resource allocation simulations, budget figures (₹ Lakhs), and capacity metrics are hypothetical "
            "decision-support estimates for multi-criteria optimization. They do not represent official government "
            "financial allocations, commercial contract bids, or guaranteed costs."
        ),
        description="Epistemic modesty disclaimer",
    )
