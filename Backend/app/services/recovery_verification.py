"""
Recovery Verification Service (Sustainability Extension Part 7).

Evaluates whether recommended or funded recovery interventions produced measurable improvement
based on available empirical satellite observations and monitoring evidence.
Enforces strict data integrity: simulated/modeled timeline projections are transparently
classified as 'INSUFFICIENT DATA' rather than false-positive verified recovery.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecoveryVerificationService:
    """
    Evidence-based recovery verification engine tracking intervention outcomes.
    """

    # Domain-specific indicator configurations and recovery directions
    DOMAIN_CONFIGS = {
        "vegetation": {
            "indicator": "Sentinel-2 NDVI (Normalized Difference Vegetation Index)",
            "expected_direction": "Increasing (Toward Pre-Flood Baseline)",
            "inverted": False,
            "field_required_on_verified": False,
        },
        "agriculture": {
            "indicator": "Sentinel-2 SAVI (Soil-Adjusted Vegetation Index)",
            "expected_direction": "Increasing (Toward Pre-Flood Baseline)",
            "inverted": False,
            "field_required_on_verified": False,
        },
        "water_wetlands": {
            "indicator": "Sentinel-2 NDWI (Water Extent Normalization Index)",
            "expected_direction": "Decreasing (Receding Toward Normal)",
            "inverted": True,
            "field_required_on_verified": False,
        },
        "soil_land": {
            "indicator": "Sentinel-2 NDTI (Normalized Difference Turbidity & Moisture)",
            "expected_direction": "Decreasing (Receding Toward Normal)",
            "inverted": True,
            "field_required_on_verified": False,
        },
        "habitats": {
            "indicator": "Multispectral Riparian Corridor Coherence Index",
            "expected_direction": "Increasing (Toward Pre-Flood Baseline)",
            "inverted": False,
            "field_required_on_verified": True,
        },
        "buildings": {
            "indicator": "Sentinel-1 SAR Double-Bounce Backscatter σ°",
            "expected_direction": "Increasing (Toward Pre-Flood Baseline)",
            "inverted": False,
            "field_required_on_verified": True,
        },
        "roads": {
            "indicator": "Optical Transport Corridor Clearance & Surface Coherence",
            "expected_direction": "Increasing (Toward Pre-Flood Baseline)",
            "inverted": False,
            "field_required_on_verified": False,
        },
        "drainage": {
            "indicator": "Stormwater Channel Silt Inundation & Flow Capacity Index",
            "expected_direction": "Increasing (Toward Pre-Flood Baseline)",
            "inverted": False,
            "field_required_on_verified": False,
        },
    }

    def __init__(self) -> None:
        pass

    def verify_recovery(
        self,
        damage_assessment: Dict[str, Any],
        recovery_recommendations: Optional[Dict[str, Any]] = None,
        recovery_priorities: Optional[Dict[str, Any]] = None,
        resource_optimization: Optional[Dict[str, Any]] = None,
        recovery_monitoring: Optional[Dict[str, Any]] = None,
        recovery_diagnosis: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        region: Optional[str] = None,
        empirical_observations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Verify post-flood recovery outcomes across all evaluated sectors.

        Args:
            damage_assessment: Dict from DamageAssessmentService.
            recovery_recommendations: Optional dict from RecoveryRecommendationService.
            recovery_priorities: Optional dict from RecoveryPriorityService.
            resource_optimization: Optional dict from ResourceOptimizationService.
            recovery_monitoring: Optional dict from RecoveryMonitoringService.
            recovery_diagnosis: Optional dict from RecoveryStallDiagnosisService.
            session_id: Optional session identifier.
            region: Optional region name ('kerala', 'nepal').
            empirical_observations: Optional real empirical follow-up observations.

        Returns:
            Dict matching RecoveryVerificationResult schema.
        """
        categories = damage_assessment.get("categories", [])
        active_region = region or damage_assessment.get("region", "kerala")
        active_session = session_id or damage_assessment.get("session_id")

        # Map recommendations
        recs_map: Dict[str, Any] = {}
        if recovery_recommendations:
            for r in recovery_recommendations.get("recommendations", []):
                recs_map[r.get("category_id", "")] = r

        # Map funded status from Part 4
        funded_categories = set()
        if resource_optimization:
            for s in resource_optimization.get("selected_sites", []):
                funded_categories.add(s.get("category"))

        # Map timelines from Part 5
        timelines_map: Dict[str, Any] = {}
        if recovery_monitoring:
            for t in recovery_monitoring.get("timelines", []):
                timelines_map[t.get("category", "")] = t

        # Map diagnoses from Part 6
        diag_map: Dict[str, Any] = {}
        if recovery_diagnosis:
            for d in recovery_diagnosis.get("diagnoses", []):
                diag_map[d.get("category", "")] = d

        verifications: List[Dict[str, Any]] = []

        for cat in categories:
            cat_id = cat.get("category_id", "")
            cat_name = cat.get("category_name", cat_id)
            cat_type = cat.get("category_type", "environmental")
            location = cat.get("geographic_location")
            damage_desc = cat.get("damage_description", "Post-flood inundation impact.")
            severity = cat.get("severity", "Moderate")

            rec_obj = recs_map.get(cat_id, {})
            recommended_action = rec_obj.get("recommended_action") or cat.get("recovery_notes") or "Routine Satellite Monitoring"
            is_funded = cat_id in funded_categories

            timeline_obj = timelines_map.get(cat_id, {})
            diag_obj = diag_map.get(cat_id, {})

            ver_item = self._evaluate_sector_verification(
                cat_id=cat_id,
                cat_name=cat_name,
                cat_type=cat_type,
                location=location,
                damage_desc=damage_desc,
                severity=severity,
                recommended_action=recommended_action,
                is_funded=is_funded,
                timeline_obj=timeline_obj,
                diag_obj=diag_obj,
                empirical_obs=empirical_observations,
            )
            verifications.append(ver_item)

        # Summary statistics
        verified_cnt = sum(1 for v in verifications if v["verification_status"] == "VERIFIED RECOVERY")
        partial_cnt = sum(1 for v in verifications if v["verification_status"] == "PARTIAL / IMPROVING")
        not_verified_cnt = sum(1 for v in verifications if v["verification_status"] == "NOT VERIFIED")
        insufficient_cnt = sum(1 for v in verifications if v["verification_status"] == "INSUFFICIENT DATA")
        simulated_cnt = sum(1 for v in verifications if v["data_is_simulated"])
        field_req_cnt = sum(1 for v in verifications if v["field_verification_required"])

        summary = {
            "total_evaluated_sectors": len(verifications),
            "verified_recovery_count": verified_cnt,
            "partial_improving_count": partial_cnt,
            "not_verified_count": not_verified_cnt,
            "insufficient_data_count": insufficient_cnt,
            "simulated_projections_count": simulated_cnt,
            "requires_field_verification_count": field_req_cnt,
        }

        methodology_notes = [
            "Recovery verification audits whether observable spectral and radar indicators demonstrate measurable improvement in the expected direction.",
            "DATA INTEGRITY STANDARD: Modeled or simulated timeline projections are classified as 'INSUFFICIENT DATA' to prevent false-positive recovery claims.",
            "Verification classifications: VERIFIED RECOVERY (empirical recovery ≥80% in expected direction), PARTIAL / IMPROVING (25% - 79% empirical progress), NOT VERIFIED (<25% progress or indicator deterioration), INSUFFICIENT DATA (simulated-only or missing follow-up data).",
            "A recovery action being funded or recommended does not automatically verify real-world restoration success.",
        ]

        return {
            "session_id": active_session,
            "region": active_region,
            "summary": summary,
            "verifications": verifications,
            "methodology_notes": methodology_notes,
            "disclaimer": (
                "Recovery verification evaluates whether observable spectral indicators (NDVI, NDWI, NDTI) and "
                "radar backscatter (SAR σ°) demonstrate measurable improvement toward pre-flood baselines. "
                "Modeled projections are transparently categorized as 'INSUFFICIENT DATA' for real verification. "
                "Satellite-derived verification reflects visible surface changes and does NOT constitute complete "
                "civil structural certification or biological ecosystem restoration without physical on-ground inspection."
            ),
        }

    def _evaluate_sector_verification(
        self,
        cat_id: str,
        cat_name: str,
        cat_type: str,
        location: Optional[Dict[str, Any]],
        damage_desc: str,
        severity: str,
        recommended_action: str,
        is_funded: bool,
        timeline_obj: Dict[str, Any],
        diag_obj: Dict[str, Any],
        empirical_obs: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Evaluate a single sector's recovery outcome against data integrity standards."""
        cfg = self.DOMAIN_CONFIGS.get(cat_id, {
            "indicator": "Multispectral Change Index",
            "expected_direction": "Increasing (Toward Pre-Flood Baseline)",
            "inverted": False,
            "field_required_on_verified": True,
        })

        indicator_name = timeline_obj.get("primary_indicator_name") or cfg["indicator"]
        expected_direction = cfg["expected_direction"]
        inverted = cfg["inverted"]

        observations = timeline_obj.get("observations", [])
        data_is_simulated = bool(timeline_obj.get("data_is_simulated", True))

        # Check if empirical observations override simulated status
        if empirical_obs:
            matched_emp = [o for o in empirical_obs if o.get("category") == cat_id]
            if matched_emp:
                observations = matched_emp
                data_is_simulated = False

        if observations:
            obs_t0 = observations[0]
            obs_latest = observations[-1]
            base_date = obs_t0.get("date", "T+0")
            latest_date = obs_latest.get("date", "T+Latest")
            base_val = obs_t0.get("value")
            target_val = obs_t0.get("baseline_value")
            latest_val = obs_latest.get("value")
            measured_delta = round(latest_val - base_val, 2) if (latest_val is not None and base_val is not None) else None
            base_desc = f"Post-Flood Baseline ({base_date}): {indicator_name} at {base_val}"
            latest_desc = f"Latest Observation ({latest_date}): {indicator_name} at {latest_val}"
        else:
            base_desc = "Baseline observation not recorded."
            latest_desc = "Follow-up satellite observation not recorded."
            base_val = None
            target_val = None
            latest_val = None
            measured_delta = None

        # STRICT DATA INTEGRITY CHECK:
        # If observations are simulated / modeled projection, it CANNOT be marked as VERIFIED RECOVERY
        if data_is_simulated or not observations:
            verification_status = "INSUFFICIENT DATA"
            evidence = (
                "Modeled Projection — Modeled timeline progression is not sufficient for real-world recovery verification. "
                "Empirical follow-up satellite acquisitions (Sentinel-2 multispectral / Sentinel-1 SAR) or in-situ ground surveys are required."
            )
            confidence = "Requires Field Verification"
            field_required = True
            notes = (
                f"Verification status is INSUFFICIENT DATA because timeline data is a modeled projection. "
                f"Original damage: {damage_desc} (Severity: {severity}). Recommended action: {recommended_action}. "
                f"{'Funded in Part 4.' if is_funded else 'Unfunded / passive pathway.'}"
            )
        else:
            # Empirical follow-up observations available: evaluate actual mathematical progress
            denom = abs(base_val - target_val) if (base_val is not None and target_val is not None) else 0.0
            if denom == 0.0:
                progress_pct = 100.0
            elif inverted:
                # Lower value = better (e.g. NDWI dropping back to 0.32 from 0.82)
                progress_pct = ((base_val - latest_val) / denom) * 100.0
            else:
                # Higher value = better (e.g. NDVI rising to 0.74 from 0.28)
                progress_pct = ((latest_val - base_val) / denom) * 100.0

            # Evaluate direction correctness
            if inverted:
                moved_correctly = (latest_val <= base_val)
            else:
                moved_correctly = (latest_val >= base_val)

            if not moved_correctly or progress_pct < 25.0:
                verification_status = "NOT VERIFIED"
                evidence = (
                    f"Empirical satellite observation shows {indicator_name} at {latest_val} "
                    f"(delta: {measured_delta:+.2f} vs post-flood baseline {base_val}), indicating lack of expected recovery."
                )
                confidence = "High"
                field_required = True
                notes = f"Follow-up satellite evidence does not demonstrate expected recovery ({progress_pct:.1f}% progress). Remedial intervention required."
            elif progress_pct < 80.0:
                verification_status = "PARTIAL / IMPROVING"
                evidence = (
                    f"Empirical satellite observation confirms positive trend in {indicator_name} "
                    f"reaching {latest_val} ({progress_pct:.1f}% toward pre-flood normal {target_val}), but restoration remains incomplete."
                )
                confidence = "Moderate"
                field_required = True
                notes = f"Partial recovery confirmed via empirical satellite data ({progress_pct:.1f}% progress toward baseline)."
            else:
                verification_status = "VERIFIED RECOVERY"
                evidence = (
                    f"Empirical satellite observation confirms {indicator_name} reached {latest_val} "
                    f"({progress_pct:.1f}% restoration toward pre-flood normal benchmark {target_val})."
                )
                confidence = "High"
                field_required = cfg.get("field_required_on_verified", False)
                notes = f"Empirical satellite data verifies observable surface restoration ({progress_pct:.1f}% recovery)."

        return {
            "category": cat_id,
            "category_name": cat_name,
            "category_type": cat_type,
            "location": location,
            "original_damage": damage_desc,
            "damage_severity": severity,
            "recommended_intervention": recommended_action,
            "funded_or_selected": is_funded,
            "baseline_observation": base_desc,
            "latest_observation": latest_desc,
            "indicator": indicator_name,
            "baseline_value": base_val,
            "target_baseline_value": target_val,
            "latest_value": latest_val,
            "measured_change": measured_delta,
            "expected_recovery_direction": expected_direction,
            "verification_status": verification_status,
            "evidence": evidence,
            "confidence": confidence,
            "field_verification_required": field_required,
            "data_is_simulated": data_is_simulated,
            "verification_notes": notes,
        }
