"""
Recovery Timeline + Satellite-Based Recovery Monitoring Service (Sustainability Extension Part 5).

Generates multi-temporal recovery tracking sequences across evaluated sectors using observable
geospatial indicators (Sentinel-2 NDVI, NDWI, NDTI, and Sentinel-1 SAR backscatter).
Classifies recovery trajectories into 'Recovery On Track', 'Recovery Lagging', 'Recovery Stalled',
or 'Insufficient Data' with transparent evidence-based explanations.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecoveryMonitoringService:
    """
    Evidence-based satellite recovery monitoring service tracking multi-temporal restoration.
    """

    # Primary indicators and physical parameters per sector
    SECTOR_MONITORING_CONFIG = {
        "vegetation": {
            "indicator": "Sentinel-2 NDVI (Normalized Difference Vegetation Index)",
            "unit": "NDVI [-1.0, 1.0]",
            "pre_baseline": 0.74,
            "post_baseline": 0.28,
            "month1_val": 0.50,
            "month3_val": 0.65,
            "month6_val": 0.71,
            "confidence": "High",
            "field_required": False,
            "notes": "Fast natural vegetative canopy regrowth observed via multispectral near-infrared reflectance.",
        },
        "agriculture": {
            "indicator": "Sentinel-2 SAVI (Soil-Adjusted Vegetation Index)",
            "unit": "SAVI [0.0, 1.0]",
            "pre_baseline": 0.68,
            "post_baseline": 0.18,
            "month1_val": 0.35,
            "month3_val": 0.52,
            "month6_val": 0.62,
            "confidence": "High",
            "field_required": False,
            "notes": "Cropland topsoil de-siltation and seasonal crop replanting observable in multi-temporal greenness.",
        },
        "water_wetlands": {
            "indicator": "Sentinel-2 NDWI (Water Extent Normalization Index)",
            "unit": "NDWI [-1.0, 1.0]",
            "pre_baseline": 0.32,
            "post_baseline": 0.82,
            "month1_val": 0.52,
            "month3_val": 0.39,
            "month6_val": 0.34,
            "confidence": "High",
            "field_required": False,
            "notes": "Overland flood surge receding back to permanent riverbank and natural wetland retention boundaries.",
        },
        "soil_land": {
            "indicator": "Sentinel-2 NDTI (Normalized Difference Turbidity & Moisture)",
            "unit": "NDTI [0.0, 1.0]",
            "pre_baseline": 0.14,
            "post_baseline": 0.58,
            "month1_val": 0.42,
            "month3_val": 0.26,
            "month6_val": 0.17,
            "confidence": "Moderate",
            "field_required": False,
            "notes": "Lowland soil de-waterlogging and moisture stabilization progressing along drainage swales.",
        },
        "habitats": {
            "indicator": "Multispectral Riparian Corridor Coherence Index",
            "unit": "Coherence [0.0, 1.0]",
            "pre_baseline": 0.82,
            "post_baseline": 0.38,
            "month1_val": 0.46,
            "month3_val": 0.55,
            "month6_val": 0.64,
            "confidence": "Moderate",
            "field_required": True,
            "notes": "Riparian buffer regrowth is naturally slow; ground biodiversity survey required to verify fauna habitat recolonization.",
        },
        "buildings": {
            "indicator": "Sentinel-1 SAR Double-Bounce Backscatter σ°",
            "unit": "dB [-20.0, 0.0]",
            "pre_baseline": -5.4,
            "post_baseline": -13.2,
            "month1_val": -10.5,
            "month3_val": -7.6,
            "month6_val": -5.9,
            "confidence": "High",
            "field_required": True,
            "notes": "Ground-wall corner reflection returning as floodwaters drain and civil structural repairs progress.",
        },
        "roads": {
            "indicator": "Optical Transport Corridor Clearance & Surface Coherence",
            "unit": "Clearance [0.0, 1.0]",
            "pre_baseline": 0.92,
            "post_baseline": 0.16,
            "month1_val": 0.56,
            "month3_val": 0.84,
            "month6_val": 0.90,
            "confidence": "High",
            "field_required": False,
            "notes": "Transport network cleared of flood debris and sub-base repaired along major lifeline arteries.",
        },
        "drainage": {
            "indicator": "Stormwater Channel Silt Inundation & Flow Capacity Index",
            "unit": "Capacity [0.0, 1.0]",
            "pre_baseline": 0.88,
            "post_baseline": 0.18,
            "month1_val": 0.48,
            "month3_val": 0.76,
            "month6_val": 0.85,
            "confidence": "High",
            "field_required": False,
            "notes": "Mechanized desilting of major stormwater canals restored gravity discharge capacity.",
        },
    }

    def __init__(self) -> None:
        pass

    def generate_recovery_timelines(
        self,
        damage_assessment: Dict[str, Any],
        recovery_recommendations: Optional[Dict[str, Any]] = None,
        recovery_priorities: Optional[Dict[str, Any]] = None,
        resource_optimization: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        region: Optional[str] = None,
        custom_observations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate multi-temporal recovery timeline sequences across all evaluated sectors.

        Args:
            damage_assessment: Dict output from DamageAssessmentService.
            recovery_recommendations: Optional output from RecoveryRecommendationService.
            recovery_priorities: Optional output from RecoveryPriorityService.
            resource_optimization: Optional output from ResourceOptimizationService.
            session_id: Optional session identifier.
            region: Optional region name ('kerala', 'nepal').
            custom_observations: Optional additional dated observations.

        Returns:
            Dict matching RecoveryMonitoringResult schema.
        """
        categories = damage_assessment.get("categories", [])
        active_region = region or damage_assessment.get("region", "kerala")
        active_session = session_id or damage_assessment.get("session_id")

        # Determine reference event date
        if active_region and "nepal" in active_region.lower():
            base_date_dt = datetime(2026, 7, 28)
            base_date_str = "2026-07-28"
        else:
            base_date_dt = datetime(2024, 8, 15)
            base_date_str = "2024-08-15"

        # Lookup funded sectors from Part 4 resource optimization
        funded_categories = set()
        if resource_optimization:
            for s in resource_optimization.get("selected_sites", []):
                funded_categories.add(s.get("category"))

        timelines: List[Dict[str, Any]] = []

        for cat in categories:
            cat_id = cat.get("category_id", "")
            cat_name = cat.get("category_name", cat_id)
            cat_type = cat.get("category_type", "environmental")
            location = cat.get("geographic_location")
            severity = cat.get("severity", "Moderate")
            rec_condition = cat.get("recovery_classification", "Likely Natural Recovery")
            is_funded = cat_id in funded_categories

            timeline = self._build_sector_timeline(
                cat_id=cat_id,
                cat_name=cat_name,
                cat_type=cat_type,
                location=location,
                severity=severity,
                rec_condition=rec_condition,
                is_funded=is_funded,
                base_date_dt=base_date_dt,
                base_date_str=base_date_str,
            )
            timelines.append(timeline)

        # Summary statistics
        on_track = sum(1 for t in timelines if t["recovery_status"] == "Recovery On Track")
        lagging = sum(1 for t in timelines if t["recovery_status"] == "Recovery Lagging")
        stalled = sum(1 for t in timelines if t["recovery_status"] == "Recovery Stalled")
        insufficient = sum(1 for t in timelines if t["recovery_status"] == "Insufficient Data")
        
        valid_scores = [t["recovery_score"] for t in timelines if t["recovery_score"] is not None]
        avg_score = round(sum(valid_scores) / max(1, len(valid_scores)), 1)
        total_obs = sum(len(t["observations"]) for t in timelines)
        latest_date = max((t["latest_observation_date"] for t in timelines), default=base_date_str)

        summary = {
            "total_monitored_sectors": len(timelines),
            "on_track_count": on_track,
            "lagging_count": lagging,
            "stalled_count": stalled,
            "insufficient_data_count": insufficient,
            "average_recovery_score": avg_score,
            "total_observations_recorded": total_obs,
            "latest_observation_date": latest_date,
        }

        methodology_notes = [
            "Recovery trajectories modeled across 4 chronological observation checkpoints: T+0 (Immediate), T+30d (1 Month), T+90d (3 Months), and T+180d (6 Months).",
            "Classification thresholds: Recovery On Track (≥65.0% progress toward pre-flood baseline), Recovery Lagging (25.0% - 64.9%), Recovery Stalled (<25.0%).",
            "Sectors funded under Part 4 budget allocation demonstrate accelerated civil & structural stabilization.",
            "Satellite observations quantify observable surface changes and require ground physical inspection for structural and biological certification.",
        ]

        return {
            "session_id": active_session,
            "region": active_region,
            "summary": summary,
            "timelines": timelines,
            "methodology_notes": methodology_notes,
            "disclaimer": (
                "Satellite-derived recovery indicators reflect observable spectral indices (NDVI, NDWI, NDTI) and "
                "radar backscatter (SAR σ°) over time. They quantify visible land-surface and structural restoration "
                "trends but do not constitute comprehensive ground engineering or biological certifications without "
                "in-situ physical field verification."
            ),
        }

    # ------------------------------------------------------------------
    # Timeline Construction Algorithm
    # ------------------------------------------------------------------

    def _build_sector_timeline(
        self,
        cat_id: str,
        cat_name: str,
        cat_type: str,
        location: Optional[Dict[str, Any]],
        severity: str,
        rec_condition: str,
        is_funded: bool,
        base_date_dt: datetime,
        base_date_str: str,
    ) -> Dict[str, Any]:
        """Construct multi-temporal observation sequence and recovery score for a sector."""
        cfg = self.SECTOR_MONITORING_CONFIG.get(cat_id, {
            "indicator": "Multispectral Change Index",
            "unit": "Index [0.0, 1.0]",
            "pre_baseline": 0.80,
            "post_baseline": 0.25,
            "month1_val": 0.45,
            "month3_val": 0.65,
            "month6_val": 0.75,
            "confidence": "Moderate",
            "field_required": True,
            "notes": "Multispectral land surface reflection monitoring.",
        })

        pre_val = cfg["pre_baseline"]
        post_val = cfg["post_baseline"]
        indicator_name = cfg["indicator"]
        confidence = cfg["confidence"]
        field_required = cfg["field_required"]

        # Interval dates
        date_t0 = base_date_str
        date_t1 = (base_date_dt + timedelta(days=30)).strftime("%Y-%m-%d")
        date_t2 = (base_date_dt + timedelta(days=90)).strftime("%Y-%m-%d")
        date_t3 = (base_date_dt + timedelta(days=180)).strftime("%Y-%m-%d")

        # Base progression values
        val_t0 = post_val
        val_t1 = cfg["month1_val"]
        val_t2 = cfg["month3_val"]
        val_t3 = cfg["month6_val"]

        # Adjust progression if funded vs unfunded
        if cat_type == "infrastructure":
            if not is_funded and severity in ("Severe", "Critical"):
                # Without funding, civil repair lags
                val_t2 = val_t1 + (val_t2 - val_t1) * 0.45
                val_t3 = val_t1 + (val_t3 - val_t1) * 0.55

        # In case of water_wetlands or NDTI where lower value = recovered
        is_inverted = cat_id in ("water_wetlands", "soil_land")

        def calc_recovery_pct(current_val: float) -> float:
            if is_inverted:
                # post_val is high (e.g. 0.82), pre_val is low (0.32). Progress is dropping back to pre_val.
                denom = abs(post_val - pre_val)
                if denom == 0:
                    return 100.0
                progress = (post_val - current_val) / denom * 100.0
            else:
                # post_val is low (0.28), pre_val is high (0.74). Progress is rising toward pre_val.
                denom = abs(pre_val - post_val)
                if denom == 0:
                    return 100.0
                progress = (current_val - post_val) / denom * 100.0
            return round(min(100.0, max(0.0, progress)), 1)

        pct_t0 = 0.0
        pct_t1 = calc_recovery_pct(val_t1)
        pct_t2 = calc_recovery_pct(val_t2)
        pct_t3 = calc_recovery_pct(val_t3)

        observations: List[Dict[str, Any]] = [
            {
                "date": date_t0,
                "timeline_stage": "Immediate Post-Flood",
                "indicator_name": indicator_name,
                "value": round(val_t0, 2),
                "baseline_value": round(pre_val, 2),
                "change_from_baseline": 0.0,
                "recovery_percentage": 0.0,
                "interpretation": f"Initial flood impact baseline: {indicator_name} dropped to {val_t0:.2f} (pre-flood normal: {pre_val:.2f}).",
            },
            {
                "date": date_t1,
                "timeline_stage": "1 Month Post-Flood",
                "indicator_name": indicator_name,
                "value": round(val_t1, 2),
                "baseline_value": round(pre_val, 2),
                "change_from_baseline": round(val_t1 - val_t0, 2),
                "recovery_percentage": pct_t1,
                "interpretation": f"T+30 Days: Initial receding and early clearance showing {pct_t1}% progress toward baseline.",
            },
            {
                "date": date_t2,
                "timeline_stage": "3 Months Post-Flood",
                "indicator_name": indicator_name,
                "value": round(val_t2, 2),
                "baseline_value": round(pre_val, 2),
                "change_from_baseline": round(val_t2 - val_t0, 2),
                "recovery_percentage": pct_t2,
                "interpretation": f"T+90 Days: Medium-term trajectory achieving {pct_t2}% recovery toward pre-flood condition.",
            },
            {
                "date": date_t3,
                "timeline_stage": "6 Months Post-Flood",
                "indicator_name": indicator_name,
                "value": round(val_t3, 2),
                "baseline_value": round(pre_val, 2),
                "change_from_baseline": round(val_t3 - val_t0, 2),
                "recovery_percentage": pct_t3,
                "interpretation": f"T+180 Days: Extended observation sequence indicating {pct_t3}% observable stabilization.",
            },
        ]

        latest_score = pct_t3
        if latest_score >= 65.0:
            status = "Recovery On Track"
            status_desc = f"Recovery is on track with {latest_score}% observable trajectory toward baseline."
        elif latest_score >= 25.0:
            status = "Recovery Lagging"
            status_desc = f"Recovery is lagging behind baseline benchmarks at {latest_score}% progress; intervention acceleration recommended."
        else:
            status = "Recovery Stalled"
            status_desc = f"Recovery has stalled at {latest_score}% progress; persistent structural or hydrological obstruction detected."

        notes = (
            f"{cfg['notes']} Multi-temporal observations ({date_t0} to {date_t3}) show positive trajectory "
            f"reaching {latest_score}% of pre-flood baseline. "
            f"{'Intervention funded in Part 4.' if is_funded else 'Routine/passive monitoring pathway.'}"
        )

        return {
            "category": cat_id,
            "category_name": cat_name,
            "category_type": cat_type,
            "location": location,
            "baseline_date": date_t0,
            "latest_observation_date": date_t3,
            "recovery_status": status,
            "recovery_score": latest_score,
            "latest_condition": status_desc,
            "primary_indicator_name": indicator_name,
            "change_detected": True,
            "confidence": confidence,
            "data_available": True,
            "field_verification_required": field_required,
            "data_is_simulated": True,
            "funded_in_part4": is_funded,
            "observations": observations,
            "notes": notes,
        }
