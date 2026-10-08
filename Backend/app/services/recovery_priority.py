"""
Recovery Priority Engine Service (Sustainability Extension Part 3).

Calculates transparent, evidence-based priority scores and ranks affected sectors/locations
for recovery resource allocation. Distinguishes between areas needing urgent intervention vs.
areas capable of natural recovery.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecoveryPriorityService:
    """
    Evidence-based multi-criteria prioritization engine for post-flood recovery.
    """

    # Weights for criteria summing to 1.0
    WEIGHT_DAMAGE_SEVERITY = 0.25
    WEIGHT_INFRASTRUCTURE = 0.20
    WEIGHT_POPULATION_IMPACT = 0.20
    WEIGHT_ECOLOGICAL = 0.15
    WEIGHT_URGENCY = 0.20

    def __init__(self) -> None:
        pass

    def compute_recovery_priorities(
        self,
        damage_assessment: Dict[str, Any],
        recovery_recommendations: Dict[str, Any],
        exposure_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute transparent priority scores and rank all evaluated sectors.

        Args:
            damage_assessment: Dict output from DamageAssessmentService.
            recovery_recommendations: Dict output from RecoveryRecommendationService.
            exposure_data: Optional exposure metrics from ExposureAnalysisService.
            session_id: Optional session identifier.
            region: Optional region name ('kerala', 'nepal').

        Returns:
            Dict matching RecoveryPrioritiesResult schema.
        """
        categories = damage_assessment.get("categories", [])
        recommendations_map = {
            r.get("category"): r for r in recovery_recommendations.get("recommendations", [])
        }
        active_region = region or damage_assessment.get("region")
        active_session = session_id or damage_assessment.get("session_id")

        prioritized_items: List[Dict[str, Any]] = []

        for cat in categories:
            cat_id = cat.get("category_id", "")
            rec = recommendations_map.get(cat_id, {})
            prioritized = self._score_sector(cat, rec, exposure_data, active_region)
            prioritized_items.append(prioritized)

        # Sort descending by priority_score
        prioritized_items.sort(key=lambda x: x["priority_score"], reverse=True)

        # Assign ranks
        for idx, item in enumerate(prioritized_items):
            item["priority_rank"] = idx + 1

        high_count = sum(1 for p in prioritized_items if p["priority_level"] == "HIGH")
        medium_count = sum(1 for p in prioritized_items if p["priority_level"] == "MEDIUM")
        low_count = sum(1 for p in prioritized_items if p["priority_level"] == "LOW")

        return {
            "session_id": active_session,
            "region": active_region,
            "total_sectors_evaluated": len(prioritized_items),
            "high_priority_count": high_count,
            "medium_priority_count": medium_count,
            "low_priority_count": low_count,
            "priorities": prioritized_items,
            "disclaimer": (
                "Recovery priority scores are decision-support rankings derived from geospatial overlays "
                "and multi-criteria weighting. They are not deterministic administrative mandates."
            ),
        }

    # ------------------------------------------------------------------
    # Scoring Algorithm
    # ------------------------------------------------------------------

    def _score_sector(
        self,
        cat: Dict[str, Any],
        rec: Dict[str, Any],
        exposure: Optional[Dict[str, Any]],
        region: Optional[str],
    ) -> Dict[str, Any]:
        """Compute composite priority score and generate explanation for one sector."""
        cat_id = cat.get("category_id", "")
        cat_name = cat.get("category_name", "Unknown Sector")
        cat_type = cat.get("category_type", "environmental")
        severity = cat.get("severity", "Moderate")
        geo_loc = cat.get("geographic_location")
        rec_action = rec.get("recommended_action", cat.get("recovery_notes", "Routine Monitoring"))
        rec_condition = rec.get("recovery_classification", cat.get("recovery_classification", "Likely Natural Recovery"))
        urgency = rec.get("urgency", "Routine Monitoring")

        # 1. Damage Severity Score [0.0 - 1.0]
        severity_scores = {
            "Critical": 1.0,
            "Severe": 0.75,
            "Moderate": 0.45,
            "Low": 0.15,
        }
        s_dam = severity_scores.get(severity, 0.45)

        # 2. Infrastructure Criticality [0.0 - 1.0]
        infra_scores = {
            "buildings": 1.0,
            "roads": 0.95,
            "drainage": 0.85,
            "agriculture": 0.60,
            "soil_land": 0.50,
            "water_wetlands": 0.35,
            "habitats": 0.30,
            "vegetation": 0.25,
        }
        s_inf = infra_scores.get(cat_id, 0.40)
        infra_importance_lbl = "Critical" if s_inf >= 0.9 else ("High" if s_inf >= 0.6 else ("Moderate" if s_inf >= 0.35 else "Low"))

        # 3. Population & Social Impact [0.0 - 1.0]
        pop_scores = {
            "buildings": 1.0,
            "roads": 0.85,
            "agriculture": 0.75,
            "drainage": 0.70,
            "soil_land": 0.45,
            "water_wetlands": 0.20,
            "vegetation": 0.20,
            "habitats": 0.15,
        }
        s_pop = pop_scores.get(cat_id, 0.30)
        
        # Qualitative population impact description
        if cat_id == "buildings":
            bld_count = cat.get("affected_count", 0)
            pop_desc = f"{bld_count} submerged building footprints (direct residential/commercial impact)"
        elif cat_id == "roads":
            road_km = cat.get("affected_length_km", 0.0)
            pop_desc = f"{road_km} km cutoff transport network disrupting community access"
        elif cat_id == "agriculture":
            pop_desc = "Farmland inundation directly threatening seasonal livelihood and food security"
        elif cat_id == "drainage":
            pop_desc = "Drainage blockage posing high risk of urban waterlogging and disease vectors"
        elif cat_id == "soil_land":
            pop_desc = "Lowland waterlogging and potential soil compaction on cultivable lands"
        elif cat_id == "water_wetlands":
            pop_desc = "Natural retention overflow with low direct residential density"
        elif cat_id == "vegetation":
            pop_desc = "General green cover inundation with low direct residential density"
        elif cat_id == "habitats":
            pop_desc = "Riparian corridor buffer with biodiversity focus rather than dense settlements"
        else:
            pop_desc = "Moderate community exposure"

        # 4. Ecological Sensitivity [0.0 - 1.0]
        eco_scores = {
            "habitats": 1.0,
            "water_wetlands": 0.90,
            "vegetation": 0.85,
            "soil_land": 0.75,
            "agriculture": 0.60,
            "drainage": 0.40,
            "roads": 0.15,
            "buildings": 0.10,
        }
        s_eco = eco_scores.get(cat_id, 0.50)
        eco_importance_lbl = "High" if s_eco >= 0.75 else ("Moderate" if s_eco >= 0.45 else "Low")

        # 5. Urgency Score [0.0 - 1.0]
        urgency_scores = {
            "Immediate": 1.0,
            "Medium-Term": 0.50,
            "Routine Monitoring": 0.10,
        }
        s_urg = urgency_scores.get(urgency, 0.50)

        # 6. Natural Recovery Multiplier
        # If the sector has high natural resilience, significantly lower the score so that
        # resources are NOT wasted where natural processes suffice.
        is_natural = "Natural" in rec_condition or "natural" in rec_condition
        is_severe = "Severe" in rec_condition or "severe" in rec_condition
        is_verification = "Verification" in rec_condition or "verification" in rec_condition

        if is_natural:
            nat_multiplier = 0.35
            nat_recovery_lbl = "High"
        elif is_severe:
            nat_multiplier = 1.15
            nat_recovery_lbl = "Low"
        elif is_verification:
            nat_multiplier = 0.85
            nat_recovery_lbl = "Moderate"
        else:
            nat_multiplier = 1.0
            nat_recovery_lbl = "Low"

        # Weighted Base Score
        base_score = (
            self.WEIGHT_DAMAGE_SEVERITY * s_dam +
            self.WEIGHT_INFRASTRUCTURE * s_inf +
            self.WEIGHT_POPULATION_IMPACT * s_pop +
            self.WEIGHT_ECOLOGICAL * s_eco +
            self.WEIGHT_URGENCY * s_urg
        )

        composite_score = base_score * nat_multiplier
        final_priority_score = round(min(10.0, max(0.0, composite_score * 10.0)), 1)

        # Priority Level Classification
        if final_priority_score >= 7.0:
            priority_level = "HIGH"
        elif final_priority_score >= 4.0:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"

        # Construct Transparent Evidence-Based Reason
        reason = self._build_reason(
            cat_name=cat_name,
            score=final_priority_score,
            level=priority_level,
            severity=severity,
            urgency=urgency,
            is_natural=is_natural,
            cat_id=cat_id,
            cat=cat,
        )

        # Metadata for Part 4 Integration
        effort_level, domain = self._get_resource_metadata(cat_id, severity, priority_level)

        factors_breakdown = {
            "damage_severity_score": round(s_dam, 3),
            "infrastructure_importance_score": round(s_inf, 3),
            "population_impact_score": round(s_pop, 3),
            "ecological_importance_score": round(s_eco, 3),
            "urgency_score": round(s_urg, 3),
            "natural_recovery_factor": round(nat_multiplier, 3),
        }

        return {
            "category": cat_id,
            "category_name": cat_name,
            "category_type": cat_type,
            "location": geo_loc,
            "priority_rank": 0,  # Assigned after sorting
            "priority_score": final_priority_score,
            "priority_level": priority_level,
            "damage_severity": severity,
            "population_impact": pop_desc,
            "ecological_importance": eco_importance_lbl,
            "infrastructure_importance": infra_importance_lbl,
            "natural_recovery_likelihood": nat_recovery_lbl,
            "urgency": urgency,
            "recommended_action": rec_action,
            "contributing_factors": factors_breakdown,
            "reason": reason,
            "estimated_effort_level": effort_level,
            "target_resource_domain": domain,
        }

    def _build_reason(
        self,
        cat_name: str,
        score: float,
        level: str,
        severity: str,
        urgency: str,
        is_natural: bool,
        cat_id: str,
        cat: Dict[str, Any],
    ) -> str:
        """Construct a clear, plain-language reason for the priority assignment."""
        if is_natural:
            return (
                f"Assigned {level} priority ({score}/10) because {cat_name} exhibits High natural ecological recovery "
                f"potential with Routine Monitoring urgency. Active external intervention is unnecessary and passive recovery is recommended."
            )

        if level == "HIGH":
            if cat_id == "buildings":
                count = cat.get("affected_count", 0)
                return (
                    f"Assigned HIGH priority ({score}/10) due to {severity} structural inundation of {count} building footprints "
                    f"with Immediate inspection urgency and zero natural recovery capability."
                )
            elif cat_id == "roads":
                km = cat.get("affected_length_km", 0.0)
                return (
                    f"Assigned HIGH priority ({score}/10) due to {severity} transport corridor submersion ({km} km) "
                    f"disrupting essential mobility, emergency routing, and community lifeline connectivity."
                )
            elif cat_id == "drainage":
                return (
                    f"Assigned HIGH priority ({score}/10) due to {severity} drainage siltation and canal blockage "
                    f"requiring Immediate mechanized clearing to prevent prolonged waterlogging and flooding recurrence."
                )
            elif cat_id == "agriculture":
                return (
                    f"Assigned HIGH priority ({score}/10) due to {severity} farmland inundation with Immediate furrow de-siltation "
                    f"and soil rehabilitation needed to safeguard community food security and seasonal livelihoods."
                )
            else:
                return f"Assigned HIGH priority ({score}/10) due to {severity} damage with Immediate intervention urgency."

        elif level == "MEDIUM":
            if cat_id == "habitats":
                return (
                    f"Assigned MEDIUM priority ({score}/10) because ecological riparian corridors require ground field verification "
                    f"to assess biodiversity displacement before committing intervention resources."
                )
            elif cat_id == "soil_land":
                return (
                    f"Assigned MEDIUM priority ({score}/10) due to Moderate waterlogging; targeted drainage swale clearing "
                    f"is recommended over the Medium-Term to prevent soil compaction."
                )
            else:
                return (
                    f"Assigned MEDIUM priority ({score}/10) reflecting Moderate damage severity with Medium-Term intervention timeline."
                )

        else:
            return (
                f"Assigned LOW priority ({score}/10) due to Low/Moderate damage severity and adequate natural drainage/stabilization."
            )

    def _get_resource_metadata(self, cat_id: str, severity: str, priority_level: str) -> tuple[str, str]:
        """Return estimated effort and domain tags for Part 4 readiness."""
        domain_map = {
            "buildings": "Structural & Civil Engineering",
            "roads": "Transportation & Highway Maintenance",
            "drainage": "Municipal Drainage & Public Works",
            "agriculture": "Agronomic & Soil Conditioning",
            "soil_land": "Land Stabilization & Bio-Engineering",
            "habitats": "Ecological Survey & Conservation",
            "water_wetlands": "Hydrological Remote Sensing",
            "vegetation": "Satellite Vegetation Monitoring",
        }
        domain = domain_map.get(cat_id, "Environmental Planning")

        if priority_level == "HIGH":
            effort = "High" if cat_id in ("buildings", "roads") else "Moderate"
        elif priority_level == "MEDIUM":
            effort = "Moderate"
        else:
            effort = "Low"

        return effort, domain
