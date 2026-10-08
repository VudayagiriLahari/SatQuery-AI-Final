"""
Resource / Budget Optimization Service (Sustainability Extension Part 4).

Determines optimal hypothetical recovery resource allocations among prioritized sectors
based on multi-criteria benefit maximization under budget and site-capacity constraints.
Distinguishes between active structural interventions and cost-free natural recovery.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResourceOptimizationService:
    """
    Evidence-based resource and budget allocation simulation engine.
    """

    # Baseline hypothetical unit costs per sector (in ₹ Lakhs)
    BASE_UNIT_COSTS_LAKHS = {
        "buildings": 3.5,       # Structural integrity inspection, temporary bracing, shoring
        "roads": 3.0,           # Transport corridor clearing, culvert desiltation, emergency paving
        "drainage": 1.8,        # Mechanized stormwater canal and swale clearing
        "agriculture": 1.5,     # Furrow de-siltation, soil aeration & organic conditioning
        "soil_land": 1.2,       # Swale clearing, bio-engineering & slope stabilization
        "habitats": 0.6,        # Biodiversity ground survey & riparian buffer marking
        "water_wetlands": 0.3,  # Hydrological telemetry & water quality sensor deployment
        "vegetation": 0.2,      # Multispectral satellite NDVI change verification setup
    }

    SEVERITY_COST_MULTIPLIERS = {
        "Critical": 1.25,
        "Severe": 1.10,
        "Moderate": 1.00,
        "Low": 0.75,
    }

    def __init__(self) -> None:
        pass

    def optimize_resources(
        self,
        recovery_priorities: Dict[str, Any],
        budget_lakhs: float = 10.0,
        max_capacity_sites: int = 5,
        allow_natural_recovery_funding: bool = False,
        domain_filter: Optional[str] = None,
        session_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run budget & workforce capacity allocation simulation across prioritized sectors.

        Args:
            recovery_priorities: Dict output from RecoveryPriorityService.
            budget_lakhs: Available hypothetical recovery budget in ₹ Lakhs (e.g. 10.0 = ₹10 Lakhs).
            max_capacity_sites: Maximum concurrent site interventions allowed by workforce.
            allow_natural_recovery_funding: Whether to allow active funding for naturally recovering sectors.
            domain_filter: Optional filter to allocate only within a specific engineering/resource domain.
            session_id: Optional session identifier.
            region: Optional region name.

        Returns:
            Dict conforming to ResourceOptimizationResult schema.
        """
        priorities = recovery_priorities.get("priorities", [])
        active_session = session_id or recovery_priorities.get("session_id")
        active_region = region or recovery_priorities.get("region")

        # Clamp parameters to valid ranges
        budget = max(0.0, float(budget_lakhs))
        capacity = max(1, int(max_capacity_sites))

        # Prepare candidate sector items with cost & benefit metrics
        candidates: List[Dict[str, Any]] = []
        for p in priorities:
            cat_id = p.get("category", "")
            severity = p.get("damage_severity", "Moderate")
            base_cost = self.BASE_UNIT_COSTS_LAKHS.get(cat_id, 1.0)
            multiplier = self.SEVERITY_COST_MULTIPLIERS.get(severity, 1.0)
            est_cost = round(base_cost * multiplier, 2)

            prio_score = float(p.get("priority_score", 0.0))
            prio_level = p.get("priority_level", "LOW")

            # Calculate benefit score
            bonus = 15.0 if prio_level == "HIGH" else (5.0 if prio_level == "MEDIUM" else 0.0)
            benefit_score = round(prio_score * 10.0 + bonus, 1)

            # Benefit-to-cost ratio for multi-criteria optimization
            cost_ratio = benefit_score / max(0.1, est_cost)

            candidates.append({
                **p,
                "estimated_cost_lakhs": est_cost,
                "expected_benefit_score": benefit_score,
                "cost_effectiveness_ratio": round(cost_ratio, 2),
            })

        # Sort candidates primarily by priority rank (and secondary cost effectiveness)
        candidates.sort(key=lambda x: (x.get("priority_rank", 99), -x["cost_effectiveness_ratio"]))

        selected_sites: List[Dict[str, Any]] = []
        unselected_sites: List[Dict[str, Any]] = []
        remaining_budget = budget
        allocated_capacity = 0

        for item in candidates:
            cat_id = item.get("category", "")
            cat_name = item.get("category_name", cat_id)
            cat_type = item.get("category_type", "environmental")
            rank = item.get("priority_rank", 0)
            score = item.get("priority_score", 0.0)
            level = item.get("priority_level", "LOW")
            cost = item.get("estimated_cost_lakhs", 1.0)
            benefit = item.get("expected_benefit_score", 0.0)
            effort = item.get("estimated_effort_level", "Moderate")
            domain = item.get("target_resource_domain", "Public Works")
            action = item.get("recommended_action", "Monitoring")
            loc = item.get("location")
            nat_recovery = item.get("natural_recovery_likelihood", "Low")

            # Check domain filter
            if domain_filter and domain_filter.lower() not in ("all", "any", ""):
                if domain_filter.lower() not in domain.lower():
                    unselected_sites.append({
                        "category": cat_id,
                        "category_name": cat_name,
                        "category_type": cat_type,
                        "priority_rank": rank,
                        "priority_score": score,
                        "priority_level": level,
                        "estimated_cost_lakhs": cost,
                        "reason_deferred": f"Domain Filter: Resource domain '{domain}' does not match active filter '{domain_filter}'.",
                        "recommended_action": action,
                    })
                    continue

            # Check natural recovery deferral
            is_high_natural = nat_recovery == "High" or "natural" in action.lower() or "passive" in action.lower()
            if is_high_natural and not allow_natural_recovery_funding:
                unselected_sites.append({
                    "category": cat_id,
                    "category_name": cat_name,
                    "category_type": cat_type,
                    "priority_rank": rank,
                    "priority_score": score,
                    "priority_level": level,
                    "estimated_cost_lakhs": cost,
                    "reason_deferred": (
                        f"Natural Recovery Deferral: {cat_name} exhibits High natural resilience. "
                        f"Active capital (₹{cost:.2f}L) deferred to preserve recovery budget for critical infrastructure."
                    ),
                    "recommended_action": action,
                })
                continue

            # Check capacity constraint
            if allocated_capacity >= capacity:
                unselected_sites.append({
                    "category": cat_id,
                    "category_name": cat_name,
                    "category_type": cat_type,
                    "priority_rank": rank,
                    "priority_score": score,
                    "priority_level": level,
                    "estimated_cost_lakhs": cost,
                    "reason_deferred": f"Capacity Limit: Maximum simultaneous intervention capacity ({capacity} sites) reached.",
                    "recommended_action": action,
                })
                continue

            # Check budget constraint
            if cost > remaining_budget:
                unselected_sites.append({
                    "category": cat_id,
                    "category_name": cat_name,
                    "category_type": cat_type,
                    "priority_rank": rank,
                    "priority_score": score,
                    "priority_level": level,
                    "estimated_cost_lakhs": cost,
                    "reason_deferred": (
                        f"Budget Limit: Estimated cost (₹{cost:.2f}L) exceeds remaining available allocation (₹{remaining_budget:.2f}L)."
                    ),
                    "recommended_action": action,
                })
                continue

            # Allocate funds to candidate site
            remaining_budget = round(remaining_budget - cost, 2)
            allocated_capacity += 1

            alloc_reason = (
                f"Funded at ₹{cost:.2f}L ({effort} effort) due to Rank #{rank} {level} priority ({score}/10) "
                f"delivering +{benefit} benefit units in {domain}."
            )

            selected_sites.append({
                "category": cat_id,
                "category_name": cat_name,
                "category_type": cat_type,
                "location": loc,
                "priority_rank": rank,
                "priority_score": score,
                "priority_level": level,
                "estimated_cost_lakhs": cost,
                "allocated_budget_lakhs": cost,
                "estimated_effort_level": effort,
                "expected_benefit_score": benefit,
                "recommended_action": action,
                "target_resource_domain": domain,
                "allocation_reason": alloc_reason,
            })

        allocated_total = round(sum(s["allocated_budget_lakhs"] for s in selected_sites), 2)
        rem_budget_final = round(budget - allocated_total, 2)
        utilization_pct = round((allocated_total / budget * 100.0) if budget > 0 else 0.0, 1)
        total_benefit = round(sum(s["expected_benefit_score"] for s in selected_sites), 1)

        summary = {
            "total_budget_lakhs": budget,
            "allocated_budget_lakhs": allocated_total,
            "remaining_budget_lakhs": rem_budget_final,
            "budget_utilization_pct": utilization_pct,
            "total_capacity_sites": capacity,
            "allocated_capacity_used": len(selected_sites),
            "remaining_capacity_sites": max(0, capacity - len(selected_sites)),
            "expected_total_benefit": total_benefit,
            "allocation_strategy": "Multi-Criteria Knapsack with Natural Recovery Deferral",
        }

        notes = [
            f"Simulated allocation across {len(candidates)} sectors under budget of ₹{budget:.2f} Lakhs and capacity of {capacity} sites.",
            f"Selected {len(selected_sites)} intervention sites utilizing ₹{allocated_total:.2f} Lakhs ({utilization_pct}% of budget).",
            f"Conserved ₹{rem_budget_final:.2f} Lakhs in unallocated reserve capital.",
        ]
        if not allow_natural_recovery_funding:
            notes.append("Natural ecological recovery sectors were systematically preserved without active capital expenditure.")

        return {
            "session_id": active_session,
            "region": active_region,
            "summary": summary,
            "selected_sites": selected_sites,
            "unselected_sites": unselected_sites,
            "allocation_notes": notes,
            "disclaimer": (
                "Resource allocation simulations, budget figures (₹ Lakhs), and capacity metrics are hypothetical "
                "decision-support estimates for multi-criteria optimization. They do not represent official government "
                "financial allocations, commercial contract bids, or guaranteed costs."
            ),
        }
