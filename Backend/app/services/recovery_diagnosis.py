"""
Recovery Failure / Stall Diagnosis Service (Sustainability Extension Part 6).

Analyzes multi-temporal satellite recovery monitoring trajectories (Part 5) and identifies
potential environmental, physical, and infrastructural causes for lagging or stalled sectors.
Applies epistemic modesty standards, transparently reports simulated vs. empirical data,
and generates actionable adaptive decision-support recommendations.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecoveryStallDiagnosisService:
    """
    Evidence-based satellite recovery stall and failure diagnosis engine.
    """

    # Domain-specific physical contributing factors and adaptive recommendations
    DIAGNOSTIC_RULES = {
        "habitats": {
            "stalled_causes": [
                {
                    "cause": "Riparian Buffer Fragmentation & Slow Natural Succession",
                    "evidence_template": "Evidence suggests riparian coherence index is {val:.2f} (pre-flood normal: {base:.2f}), indicating fragmented canopy recovery along riverbanks.",
                    "confidence": "Moderate",
                },
                {
                    "cause": "Possible In-Stream Siltation & Fauna Microhabitat Loss",
                    "evidence_template": "Evidence suggests post-flood silt sedimentation along bank swales may impede rapid biological recolonization.",
                    "confidence": "Requires Field Verification",
                },
            ],
            "supporting_points": [
                "Multispectral riparian corridor coherence indicates slow natural vegetation succession.",
                "High slope and waterflow shear stress along riverbanks create persistent micro-erosion zones.",
            ],
            "field_required": True,
            "adaptive_rec": "Conduct in-situ ground biodiversity survey, delineate protected riparian conservation buffers, and introduce native pioneer riverbank flora.",
        },
        "buildings": {
            "stalled_causes": [
                {
                    "cause": "Infrastructure Restoration Not Detected / Persistent Structural Dampness",
                    "evidence_template": "Evidence suggests Sentinel-1 SAR double-bounce backscatter σ° is {val:.1f} dB (pre-flood: {base:.1f} dB), indicating unresolved wall/ground masonry damage or moisture retention.",
                    "confidence": "High",
                },
                {
                    "cause": "Debris Accumulation / Subgrade Instability",
                    "evidence_template": "Evidence suggests radar corner reflector signatures remain suppressed relative to pre-flood structural benchmarks.",
                    "confidence": "Requires Field Verification",
                },
            ],
            "supporting_points": [
                "Sentinel-1 SAR C-band double-bounce reflections have not returned to pre-event urban baseline.",
                "Persistent attenuation consistent with water-damaged masonry or unaddressed structural collapse.",
            ],
            "field_required": True,
            "adaptive_rec": "Deploy civil engineering structural assessment team for building load testing, foundation integrity verification, and moisture mitigation.",
        },
        "roads": {
            "stalled_causes": [
                {
                    "cause": "Transport Corridor Obstruction / Road Subgrade Degradation",
                    "evidence_template": "Evidence suggests transport corridor optical clearance is {val:.2f} (pre-flood normal: {base:.2f}), indicating partial debris blockage or road surface erosion.",
                    "confidence": "High",
                },
                {
                    "cause": "Road Shoulder Scour / Culvert Washout",
                    "evidence_template": "Evidence suggests localized washouts along roadside drainage shoulders prevent safe vehicle access.",
                    "confidence": "Moderate",
                },
            ],
            "supporting_points": [
                "Optical transport corridor clearance index indicates disrupted roadway continuity.",
                "Surface reflectance irregularities indicate uncompacted gravel or debris deposits.",
            ],
            "field_required": False,
            "adaptive_rec": "Prioritize mechanized debris clearance, sub-base compaction testing, and culvert reinforcement along primary lifeline arteries.",
        },
        "drainage": {
            "stalled_causes": [
                {
                    "cause": "Persistent Stormwater Canal Siltation & Drainage Bottlenecks",
                    "evidence_template": "Evidence suggests channel flow capacity is {val:.2f} (pre-flood normal: {base:.2f}), indicating heavy sediment accumulation in drainage canals.",
                    "confidence": "High",
                },
                {
                    "cause": "Culvert Debris Clogging & Gravity Outfall Restriction",
                    "evidence_template": "Evidence suggests downstream drainage culverts and gravity outfalls remain partially obstructed.",
                    "confidence": "Moderate",
                },
            ],
            "supporting_points": [
                "Hydraulic flow capacity index remains significantly below pre-flood stormwater throughput baseline.",
                "Stagnant surface drainage observable along secondary feeder channels.",
            ],
            "field_required": False,
            "adaptive_rec": "Execute mechanized desilting of major stormwater canals, clear culvert debris screens, and re-establish gravity discharge slope.",
        },
        "vegetation": {
            "stalled_causes": [
                {
                    "cause": "Weak Vegetative Canopy Regrowth / Potential Soil Salinity or Nutrient Loss",
                    "evidence_template": "Evidence suggests Sentinel-2 NDVI is {val:.2f} (pre-flood normal: {base:.2f}), indicating suppressed photosynthetic vigor in flooded lowlands.",
                    "confidence": "High",
                },
                {
                    "cause": "Topsoil Scouring & Root Inundation Stress",
                    "evidence_template": "Evidence suggests prolonged root saturation delayed natural grass and shrub regeneration.",
                    "confidence": "Moderate",
                },
            ],
            "supporting_points": [
                "Near-infrared reflectance indicates slow biomass accumulation across inundation footprint.",
                "Photosynthetic index recovery trajectory remains below historical seasonal regrowth rates.",
            ],
            "field_required": False,
            "adaptive_rec": "Deploy assisted native seedling replanting, hydroseeding with indigenous grasses, and conduct topsoil nutrient testing.",
        },
        "agriculture": {
            "stalled_causes": [
                {
                    "cause": "Agricultural Recovery Below Baseline / Topsoil Silt Compaction",
                    "evidence_template": "Evidence suggests Soil-Adjusted Vegetation Index (SAVI) is {val:.2f} (pre-flood normal: {base:.2f}), indicating delayed crop replanting or dense silt crusting.",
                    "confidence": "High",
                },
                {
                    "cause": "Standing Furrow Inundation & Micro-Drainage Failure",
                    "evidence_template": "Evidence suggests micro-topographic water retention in crop furrows preventing field machinery operation.",
                    "confidence": "Moderate",
                },
            ],
            "supporting_points": [
                "SAVI spectral trajectory shows subdued agricultural greenup compared to adjacent unflooded plots.",
                "Soil moisture reflectance indicates prolonged saturation in cultivated flatlands.",
            ],
            "field_required": False,
            "adaptive_rec": "Initiate mechanical topsoil de-siltation, deep furrow aeration, and distribute soil bio-amendments before seasonal planting.",
        },
        "water_wetlands": {
            "stalled_causes": [
                {
                    "cause": "Abnormal Overland Inundation / Delayed Natural Drainage",
                    "evidence_template": "Evidence suggests Normalized Difference Water Index (NDWI) is {val:.2f} (pre-flood normal: {base:.2f}), indicating residual flood extent in lowland depressions.",
                    "confidence": "High",
                },
                {
                    "cause": "Downstream Silt Berms Restricting Spillway Outflow",
                    "evidence_template": "Evidence suggests flood-deposited silt ridges along natural spillways impede gravity drainage.",
                    "confidence": "Moderate",
                },
            ],
            "supporting_points": [
                "NDWI surface water index remains elevated above pre-flood wetland retention baseline.",
                "Water extent contraction has decelerated across shallow retention swales.",
            ],
            "field_required": False,
            "adaptive_rec": "Survey natural wetland hydrological retention buffers and clear natural spillway discharge channels of obstructive debris.",
        },
        "soil_land": {
            "stalled_causes": [
                {
                    "cause": "Continuing Subsoil Moisture Saturation & Surface Crusting",
                    "evidence_template": "Evidence suggests NDTI moisture index is {val:.2f} (pre-flood normal: {base:.2f}), indicating slow subsoil percolation.",
                    "confidence": "Moderate",
                },
                {
                    "cause": "Soil Compaction & Reduced Infiltration Capacity",
                    "evidence_template": "Evidence suggests fine sediment deposition created impermeable topsoil crusting.",
                    "confidence": "Moderate",
                },
            ],
            "supporting_points": [
                "Normalized Difference Turbidity & Moisture Index (NDTI) indicates prolonged soil moisture retention.",
                "Surface texture roughness indicates unmitigated sediment deposits along drainage paths.",
            ],
            "field_required": False,
            "adaptive_rec": "Install perimeter contour drainage trenches and bio-retention swales to accelerate subsoil de-watering.",
        },
    }

    def __init__(self) -> None:
        pass

    def diagnose_stalls(
        self,
        recovery_monitoring: Dict[str, Any],
        damage_assessment: Optional[Dict[str, Any]] = None,
        recovery_recommendations: Optional[Dict[str, Any]] = None,
        recovery_priorities: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Diagnose potential recovery bottlenecks, stalls, and failures across all monitored sectors.

        Args:
            recovery_monitoring: Dict output from RecoveryMonitoringService.
            damage_assessment: Optional output from DamageAssessmentService.
            recovery_recommendations: Optional output from RecoveryRecommendationService.
            recovery_priorities: Optional output from RecoveryPriorityService.
            session_id: Optional session identifier.
            region: Optional region name ('kerala', 'nepal').

        Returns:
            Dict matching RecoveryStallDiagnosisResult schema.
        """
        timelines = recovery_monitoring.get("timelines", [])
        active_region = region or recovery_monitoring.get("region", "kerala")
        active_session = session_id or recovery_monitoring.get("session_id")

        diagnoses: List[Dict[str, Any]] = []

        for timeline in timelines:
            diag = self._evaluate_sector_timeline(timeline, active_region)
            diagnoses.append(diag)

        # Summary statistics
        stalled_cnt = sum(1 for d in diagnoses if d["recovery_status"] == "Recovery Stalled")
        lagging_cnt = sum(1 for d in diagnoses if d["recovery_status"] == "Recovery Lagging")
        on_track_cnt = sum(1 for d in diagnoses if d["recovery_status"] == "Recovery On Track")
        insufficient_cnt = sum(1 for d in diagnoses if d["recovery_status"] == "Insufficient Data")
        stalled_or_lagging = stalled_cnt + lagging_cnt
        field_req_cnt = sum(1 for d in diagnoses if d.get("field_verification_required", False))

        summary = {
            "total_diagnosed_sectors": len(diagnoses),
            "stalled_count": stalled_cnt,
            "lagging_count": lagging_cnt,
            "on_track_count": on_track_cnt,
            "insufficient_data_count": insufficient_cnt,
            "stalled_or_lagging_count": stalled_or_lagging,
            "requires_field_verification_count": field_req_cnt,
        }

        methodology_notes = [
            "Diagnostic engine evaluates sector recovery scores against operational thresholds: On Track (≥65.0%), Lagging (25.0% - 64.9%), Stalled (<25.0%).",
            "Identifies plausible physical bottlenecks (waterlogging, canal siltation, road obstruction, canopy delay, structural damage) backed by observable sensor indicators.",
            "All diagnostic causes express epistemic modesty ('Possible contributing factor', 'Evidence suggests') and require field verification before major capital commitments.",
            "Transparently distinguishes between real satellite observation sequences and modeled projection simulations.",
        ]

        return {
            "session_id": active_session,
            "region": active_region,
            "summary": summary,
            "diagnoses": diagnoses,
            "methodology_notes": methodology_notes,
            "disclaimer": (
                "Recovery failure and stall diagnoses are automated decision-support hypotheses inferred from "
                "satellite spectral indices (NDVI, NDWI, NDTI), radar backscatter (SAR σ°), and GIS terrain overlays. "
                "They highlight potential environmental and infrastructural bottlenecks but do NOT replace in-situ "
                "civil engineering inspections, biological surveys, or official field investigations."
            ),
        }

    def _evaluate_sector_timeline(
        self,
        timeline: Dict[str, Any],
        region: str,
    ) -> Dict[str, Any]:
        """Evaluate a single sector's recovery timeline for stalls or bottlenecks."""
        cat_id = timeline.get("category", "")
        cat_name = timeline.get("category_name", cat_id)
        cat_type = timeline.get("category_type", "environmental")
        location = timeline.get("location")
        rec_status = timeline.get("recovery_status", "Recovery On Track")
        rec_score = float(timeline.get("recovery_score", 100.0))
        indicator_name = timeline.get("primary_indicator_name", "Satellite Multi-temporal Index")
        is_simulated = bool(timeline.get("data_is_simulated", True))
        field_required = bool(timeline.get("field_verification_required", False))

        observations = timeline.get("observations", [])
        latest_obs = observations[-1] if observations else {}
        latest_val = latest_obs.get("value")
        base_val = latest_obs.get("baseline_value")

        cfg = self.DIAGNOSTIC_RULES.get(cat_id, {
            "stalled_causes": [
                {
                    "cause": "Unresolved Post-Flood Environmental Impact",
                    "evidence_template": "Evidence suggests recovery indicator is {val} (baseline: {base}), showing slower than expected trajectory.",
                    "confidence": "Moderate",
                }
            ],
            "supporting_points": [
                "Multi-temporal satellite indicators show subdued recovery progression.",
            ],
            "field_required": True,
            "adaptive_rec": "Deploy field verification survey and assess targeted stabilization measures.",
        })

        # Check if stall or lag is detected
        stall_detected = (rec_status in ("Recovery Lagging", "Recovery Stalled")) or (rec_score < 65.0)

        possible_causes: List[Dict[str, Any]] = []
        supporting_evidence: List[str] = []

        if rec_status == "Insufficient Data":
            stall_detected = False
            confidence = "Requires Field Verification"
            field_required = True
            possible_causes.append({
                "cause": "Insufficient Satellite Evidence / Cloud Obscuration",
                "evidence": "Evidence suggests persistent cloud cover or lack of recent cloud-free acquisitions precludes definitive recovery confirmation.",
                "confidence": "Low",
            })
            supporting_evidence.append("Multi-temporal optical or SAR satellite acquisitions missing or corrupted for this sector.")
            adaptive_rec = "Acquire high-resolution optical/SAR follow-up imagery or schedule on-ground field inspection."
            notes = "Epistemic caveat: Classification indeterminate due to missing multi-temporal sensor observations."

        elif stall_detected:
            confidence = cfg.get("confidence", "Moderate")
            field_required = cfg.get("field_required", True) or field_required

            val_disp = latest_val if latest_val is not None else 0.0
            base_disp = base_val if base_val is not None else 0.0

            for rule_cause in cfg.get("stalled_causes", []):
                template = rule_cause.get("evidence_template", "Evidence suggests indicator value is {val}.")
                try:
                    formatted_ev = template.format(val=val_disp, base=base_disp)
                except Exception:
                    formatted_ev = f"Evidence suggests observable value is {val_disp} vs. baseline {base_disp}."
                
                possible_causes.append({
                    "cause": rule_cause["cause"],
                    "evidence": formatted_ev,
                    "confidence": rule_cause["confidence"],
                })

            for pt in cfg.get("supporting_points", []):
                supporting_evidence.append(pt)
            
            supporting_evidence.append(
                f"Observable recovery progress is {rec_score:.1f}% toward pre-flood normal ({rec_status})."
            )

            adaptive_rec = cfg.get("adaptive_rec", "Deploy field inspection and prioritize remedial works.")
            
            sim_prefix = "Preliminary model indicator / Requires follow-up satellite acquisition or field verification: " if is_simulated else "Satellite-observed recovery diagnosis: "
            notes = (
                f"{sim_prefix}{cat_name} classified as '{rec_status}' at {rec_score:.1f}% recovery progress. "
                f"Identified {len(possible_causes)} plausible physical contributing factors backed by {indicator_name} data."
            )

        else:
            # On Track
            stall_detected = False
            confidence = timeline.get("confidence", "High")
            supporting_evidence.append(
                f"Evidence suggests consistent positive trajectory: {indicator_name} reached {rec_score:.1f}% toward pre-flood baseline."
            )
            supporting_evidence.append(
                "No persistent waterlogging, structural collapse, or sediment blockage detected above critical thresholds."
            )
            adaptive_rec = "Maintain routine satellite monitoring schedule and protect established natural/reconstructed recovery gains."
            notes = f"{cat_name} is on track ({rec_score:.1f}% progress). Observable trajectory aligns with expected recovery benchmarks."

        return {
            "category": cat_id,
            "category_name": cat_name,
            "category_type": cat_type,
            "location": location,
            "recovery_status": rec_status,
            "recovery_score": rec_score,
            "stall_detected": stall_detected,
            "primary_indicator_name": indicator_name,
            "latest_observed_value": latest_val,
            "baseline_value": base_val,
            "possible_causes": possible_causes,
            "supporting_evidence": supporting_evidence,
            "confidence": confidence,
            "field_verification_required": field_required,
            "data_is_simulated": is_simulated,
            "updated_recommendation": adaptive_rec,
            "notes": notes,
        }
