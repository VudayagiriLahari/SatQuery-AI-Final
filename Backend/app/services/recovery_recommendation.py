"""
Natural Recovery Assessment & Sustainable Recovery Recommendation Engine Service.

Implements Part 2 of the SatQuery Sustainability Extension:
- Evaluates damage assessment output across Environmental and Infrastructure domains.
- Determines whether active human intervention is truly necessary or if natural ecological processes suffice.
- Generates evidence-based, sustainable recommendations matching Damage Type + Severity + Recovery Condition.
- Provides transparent reasoning for every recommended action.
- Prepares structured data directly consumable by future downstream components.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecoveryRecommendationService:
    """
    Service for assessing natural recovery potential and generating sustainable,
    evidence-based recovery recommendations.
    """

    # Normalized 4-tier recovery conditions
    COND_NATURAL = "Likely Natural Recovery"
    COND_ASSISTANCE = "Recovery Assistance Needed"
    COND_SEVERE = "Severely/Persistently Damaged"
    COND_VERIFICATION = "Field Verification Required"

    def __init__(self) -> None:
        pass

    def generate_recommendations(
        self,
        damage_assessment: Dict[str, Any],
        session_id: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate decision-support recovery recommendations for all assessed categories.

        Args:
            damage_assessment: Output from DamageAssessmentService.assess_damage (dict or model_dump).
            session_id: Optional active session id.
            region: Optional region name ('kerala', 'nepal', etc.).

        Returns:
            Dict matching RecoveryRecommendationsResult schema.
        """
        categories = damage_assessment.get("categories", [])
        active_region = region or damage_assessment.get("region")
        active_session = session_id or damage_assessment.get("session_id")

        recommendations: List[Dict[str, Any]] = []

        natural_recovery_count = 0
        intervention_needed_count = 0
        field_verification_count = 0

        for cat in categories:
            rec = self._evaluate_category(cat, active_region)
            recommendations.append(rec)

            cond = rec["recovery_classification"]
            if cond == self.COND_NATURAL:
                natural_recovery_count += 1
            elif cond in (self.COND_ASSISTANCE, self.COND_SEVERE):
                intervention_needed_count += 1
            elif cond == self.COND_VERIFICATION:
                field_verification_count += 1

        return {
            "session_id": active_session,
            "region": active_region,
            "total_recommendations": len(recommendations),
            "natural_recovery_count": natural_recovery_count,
            "intervention_needed_count": intervention_needed_count,
            "field_verification_count": field_verification_count,
            "recommendations": recommendations,
            "disclaimer": (
                "Recommendations are decision-support guidelines derived from satellite observations and "
                "available GIS layers. They are not guaranteed instructions and must be validated by local "
                "authorities and licensed engineers."
            ),
        }

    # ------------------------------------------------------------------
    # Category Evaluation Logic
    # ------------------------------------------------------------------

    def _evaluate_category(self, cat: Dict[str, Any], region: Optional[str]) -> Dict[str, Any]:
        """Generate tailored recommendation for a single damaged category."""
        cat_id = cat.get("category_id", "")
        cat_name = cat.get("category_name", "Unknown Category")
        cat_type = cat.get("category_type", "environmental")
        severity = cat.get("severity", "Moderate")
        raw_rec_class = cat.get("recovery_classification", "")
        geo_loc = cat.get("geographic_location")
        confidence = cat.get("confidence_level", "Moderate")
        affected_area = cat.get("affected_area_km2")
        affected_count = cat.get("affected_count")
        affected_length = cat.get("affected_length_km")

        # Map raw Part 1 classification into standard Part 2 Condition
        condition = self._normalize_condition(raw_rec_class)

        # Dispatch to category-specific rule engine
        if cat_id == "vegetation":
            return self._recommend_vegetation(cat_name, cat_type, severity, condition, geo_loc, confidence, affected_area)
        elif cat_id == "agriculture":
            return self._recommend_agriculture(cat_name, cat_type, severity, condition, geo_loc, confidence, affected_area)
        elif cat_id == "water_wetlands":
            return self._recommend_water_wetlands(cat_name, cat_type, severity, condition, geo_loc, confidence, affected_area)
        elif cat_id == "soil_land":
            return self._recommend_soil_land(cat_name, cat_type, severity, condition, geo_loc, confidence, affected_area)
        elif cat_id == "habitats":
            return self._recommend_habitats(cat_name, cat_type, severity, condition, geo_loc, confidence, affected_area)
        elif cat_id == "buildings":
            return self._recommend_buildings(cat_name, cat_type, severity, condition, geo_loc, confidence, affected_count)
        elif cat_id == "roads":
            return self._recommend_roads(cat_name, cat_type, severity, condition, geo_loc, confidence, affected_length)
        elif cat_id == "drainage":
            return self._recommend_drainage(cat_name, cat_type, severity, condition, geo_loc, confidence, affected_length)
        else:
            # Generic fallback
            return {
                "category": cat_id,
                "category_name": cat_name,
                "category_type": cat_type,
                "location": geo_loc,
                "damage_severity": severity,
                "recovery_classification": condition,
                "recommended_action": "Routine Monitoring & Periodic Assessment",
                "intervention_type": "monitoring",
                "reason": "Baseline observation indicates moderate change; monitor for natural stabilization.",
                "confidence": confidence,
                "requires_field_verification": condition == self.COND_VERIFICATION,
                "sustainable_practices": ["Periodic satellite monitoring", "Prevent unauthorized land-use alterations"],
                "urgency": "Routine Monitoring",
            }

    def _normalize_condition(self, raw_class: str) -> str:
        """Map Part 1 recovery strings to Part 2 standardized recovery conditions."""
        rc = raw_class.lower().strip()
        if "natural" in rc or "likely" in rc:
            return self.COND_NATURAL
        elif "assistance" in rc or "needed" in rc or "requires" in rc and "field" not in rc:
            return self.COND_ASSISTANCE
        elif "severe" in rc or "persistent" in rc:
            return self.COND_SEVERE
        elif "field" in rc or "verification" in rc:
            return self.COND_VERIFICATION
        return self.COND_NATURAL

    # ------------------------------------------------------------------
    # Sector Specific Recommendation Builders
    # ------------------------------------------------------------------

    def _recommend_vegetation(
        self, name: str, ctype: str, severity: str, condition: str, loc: Any, conf: str, area: Optional[float]
    ) -> Dict[str, Any]:
        area_str = f"{area:.2f} km²" if area else "vegetation extent"
        if condition == self.COND_NATURAL:
            action = "Natural Regeneration Monitoring (Passive Recovery)"
            itype = "monitoring"
            reason = (
                f"Satellite observations indicate {area_str} of inundated green cover without major structural soil loss. "
                "Native riparian and terrestrial flora exhibit high ecological resilience; active intervention is unnecessary "
                "and passive natural recovery is recommended."
            )
            field_req = False
            urgency = "Routine Monitoring"
            practices = [
                "Passive natural succession protection",
                "Periodic bi-weekly satellite NDVI vigor monitoring",
                "Screening for post-flood opportunistic invasive weeds",
            ]
        elif condition == self.COND_ASSISTANCE:
            action = "Assisted Regeneration & Native Species Re-Seeding"
            itype = "assisted_regeneration"
            reason = (
                f"Prolonged waterlogging over {area_str} has impaired local seedbank viability. "
                "Targeted replanting with native flood-tolerant shrubs and grasses will accelerate canopy stabilization and prevent erosion."
            )
            field_req = True
            urgency = "Medium-Term"
            practices = [
                "Broadcasting indigenous grass and shrub seeds",
                "Coir-mat bio-revetment along vulnerable slopes",
                "Manual removal of invasive weeds",
            ]
        else:
            action = "Comprehensive Ecological Restoration & Bio-Engineering"
            itype = "ecological_restoration"
            reason = (
                f"Severe biomass stripping and root scour detected across {area_str}. "
                "Active ecological engineering is necessary to re-establish vegetative cover and topsoil retention."
            )
            field_req = True
            urgency = "Medium-Term"
            practices = [
                "Live willow/bamboo staking for root anchoring",
                "Terraced bio-engineering re-vegetation",
                "Long-term flora diversity monitoring",
            ]

        return {
            "category": "vegetation",
            "category_name": name,
            "category_type": ctype,
            "location": loc,
            "damage_severity": severity,
            "recovery_classification": condition,
            "recommended_action": action,
            "intervention_type": itype,
            "reason": reason,
            "confidence": conf,
            "requires_field_verification": field_req,
            "sustainable_practices": practices,
            "urgency": urgency,
        }

    def _recommend_agriculture(
        self, name: str, ctype: str, severity: str, condition: str, loc: Any, conf: str, area: Optional[float]
    ) -> Dict[str, Any]:
        area_str = f"{area:.2f} km²" if area else "agricultural area"
        if condition == self.COND_NATURAL:
            action = "Farmland Drainage & Natural Soil Aeration Monitoring"
            itype = "monitoring"
            reason = (
                f"Minor standing water detected over {area_str} with minimal silt accumulation. "
                "Natural gravity drainage will restore field conditions without mechanical soil disruption."
            )
            field_req = False
            urgency = "Routine Monitoring"
            practices = [
                "Allow natural percolation without heavy machinery compaction",
                "Visual inspection of furrow drainage",
            ]
        elif condition == self.COND_ASSISTANCE:
            action = "Agricultural Rehabilitation & Soil Recovery Assessment"
            itype = "rehabilitation"
            reason = (
                f"Standing inundation over {area_str} of agricultural floodplain has caused topsoil siltation and anaerobic conditions in furrows. "
                "Assistance is required for furrow de-siltation, soil aeration, and seed supply support before the next cropping cycle."
            )
            field_req = True
            urgency = "Immediate"
            practices = [
                "De-siltation of agricultural furrows and low-impact swales",
                "Subsoil mechanical aeration using low-ground-pressure equipment",
                "Organic composting and green manuring to re-establish microbial activity",
            ]
        else:
            action = "Comprehensive Soil Rehabilitation & Land Leveling"
            itype = "rehabilitation"
            reason = (
                f"Heavy sediment deposition and severe furrow wash-out detected across {area_str}. "
                "Specialized agricultural recovery assistance is needed to restore arable soil profile."
            )
            field_req = True
            urgency = "Immediate"
            practices = [
                "Mechanical removal of coarse sediment layers",
                "Soil pH conditioning and micronutrient replenishment",
                "Crop diversification with flood-tolerant varieties",
            ]

        return {
            "category": "agriculture",
            "category_name": name,
            "category_type": ctype,
            "location": loc,
            "damage_severity": severity,
            "recovery_classification": condition,
            "recommended_action": action,
            "intervention_type": itype,
            "reason": reason,
            "confidence": conf,
            "requires_field_verification": field_req,
            "sustainable_practices": practices,
            "urgency": urgency,
        }

    def _recommend_water_wetlands(
        self, name: str, ctype: str, severity: str, condition: str, loc: Any, conf: str, area: Optional[float]
    ) -> Dict[str, Any]:
        area_str = f"{area:.2f} km²" if area else "wetland surface"
        if condition == self.COND_NATURAL:
            action = "Hydrological Buffering & Wetland Boundary Monitoring"
            itype = "monitoring"
            reason = (
                f"Natural wetlands and retention basins operated as intended by buffering {area_str} of flood surge. "
                "Surface water levels will normalize naturally through regional drainage channels without dredging intervention."
            )
            field_req = False
            urgency = "Routine Monitoring"
            practices = [
                "Preserve natural riparian floodplains without artificial embankments",
                "Monitor post-flood wetland shoreline morphology",
                "Prevent debris dumping in natural retention basins",
            ]
        elif condition == self.COND_ASSISTANCE:
            action = "Wetland Reconnection & Flow Obstruction Assessment"
            itype = "wetland_restoration"
            reason = (
                f"Debris accumulation has partially constricted natural wetland outflow paths across {area_str}. "
                "Targeted debris removal will restore baseline hydrological connectivity and water circulation."
            )
            field_req = True
            urgency = "Medium-Term"
            practices = [
                "Non-invasive debris extraction at channel choke points",
                "Restoration of natural oxbow tidal exchanges",
                "Bio-filter vegetative planting",
            ]
        else:
            action = "Further Environmental & Wetland Restoration Assessment"
            itype = "field_assessment"
            reason = (
                f"Substantial alteration to natural wetland boundary ({area_str}) detected. "
                "Detailed environmental and bathymetric surveys are required to assess long-term wetland water balance."
            )
            field_req = True
            urgency = "Medium-Term"
            practices = [
                "In-situ water depth and retention capacity survey",
                "Riparian wetland conservation zoning",
            ]

        return {
            "category": "water_wetlands",
            "category_name": name,
            "category_type": ctype,
            "location": loc,
            "damage_severity": severity,
            "recovery_classification": condition,
            "recommended_action": action,
            "intervention_type": itype,
            "reason": reason,
            "confidence": conf,
            "requires_field_verification": field_req,
            "sustainable_practices": practices,
            "urgency": urgency,
        }

    def _recommend_soil_land(
        self, name: str, ctype: str, severity: str, condition: str, loc: Any, conf: str, area: Optional[float]
    ) -> Dict[str, Any]:
        area_str = f"{area:.2f} km²" if area else "lowland terrain"
        if condition == self.COND_NATURAL:
            action = "Passive Drainage & Soil Moisture Stabilization Monitoring"
            itype = "monitoring"
            reason = (
                f"Adequate terrain slope ensures natural gravity drainage for {area_str}. "
                "Soils will de-saturate naturally as regional base river levels drop."
            )
            field_req = False
            urgency = "Routine Monitoring"
            practices = [
                "Allow natural soil drying without heavy machinery traffic",
                "Monitor for surface crusting",
            ]
        elif condition == self.COND_ASSISTANCE:
            action = "Drainage Improvement & Soil De-Waterlogging Intervention"
            itype = "drainage_intervention"
            reason = (
                f"Prolonged waterlogging in low-slope terrain ({area_str}) creates high risk of anaerobic soil conditions and compaction. "
                "Targeted swale clearance and deep aeration are recommended to expedite soil drying."
            )
            field_req = True
            urgency = "Immediate"
            practices = [
                "Vegetated drainage swale maintenance",
                "Low-impact shallow subsoiling",
                "Application of biochar or agricultural gypsum for soil structure restoration",
            ]
        else:
            action = "Erosion Control Assessment & Land Stabilization"
            itype = "land_stabilization"
            reason = (
                f"Steep slope gradient combined with heavy flood runoff indicates severe topsoil scouring across {area_str}. "
                "Land stabilization and erosion barriers are required to prevent secondary landslides."
            )
            field_req = True
            urgency = "Immediate"
            practices = [
                "Coir geotextile slope covering",
                "Bio-check dams using local stone and bamboo",
                "Vetiver grass contour hedging for deep soil anchoring",
            ]

        return {
            "category": "soil_land",
            "category_name": name,
            "category_type": ctype,
            "location": loc,
            "damage_severity": severity,
            "recovery_classification": condition,
            "recommended_action": action,
            "intervention_type": itype,
            "reason": reason,
            "confidence": conf,
            "requires_field_verification": field_req,
            "sustainable_practices": practices,
            "urgency": urgency,
        }

    def _recommend_habitats(
        self, name: str, ctype: str, severity: str, condition: str, loc: Any, conf: str, area: Optional[float]
    ) -> Dict[str, Any]:
        area_str = f"{area:.2f} km²" if area else "riparian corridor"
        if condition == self.COND_NATURAL:
            action = "Habitat Protection & Ecological Baseline Monitoring"
            itype = "monitoring"
            reason = (
                f"Riparian flora across {area_str} is naturally adapted to seasonal inundation cycles. "
                "Protecting the corridor from human encroachment is sufficient for natural recovery."
            )
            field_req = False
            urgency = "Routine Monitoring"
            practices = [
                "Strict buffer zone enforcement (no construction/clearing)",
                "Periodic wildlife corridor remote sensing checks",
            ]
        elif condition == self.COND_VERIFICATION:
            action = "On-Ground Ecological Habitat Assessment & Survey"
            itype = "ecological_assessment"
            reason = (
                f"Satellite imagery shows inundation across {area_str} of sensitive riparian corridor, but cannot assess micro-faunal impact. "
                "Physical field validation is required to survey riverbank stability, native flora displacement, and wildlife movement."
            )
            field_req = True
            urgency = "Medium-Term"
            practices = [
                "Non-invasive ground biodiversity assessment",
                "Identification of eroded riverbank segments for bio-shielding",
                "Community-based riparian habitat monitoring",
            ]
        else:
            action = "Targeted Riparian Habitat Restoration & Bank Protection"
            itype = "habitat_restoration"
            reason = (
                f"Significant riverbank scour detected along {area_str}. "
                "Assisted replanting of indigenous riparian species is needed to restore habitat connectivity."
            )
            field_req = True
            urgency = "Medium-Term"
            practices = [
                "Native riparian tree and reed planting",
                "Eco-friendly brush mattress bank revetments",
            ]

        return {
            "category": "habitats",
            "category_name": name,
            "category_type": ctype,
            "location": loc,
            "damage_severity": severity,
            "recovery_classification": condition,
            "recommended_action": action,
            "intervention_type": itype,
            "reason": reason,
            "confidence": conf,
            "requires_field_verification": field_req,
            "sustainable_practices": practices,
            "urgency": urgency,
        }

    def _recommend_buildings(
        self, name: str, ctype: str, severity: str, condition: str, loc: Any, conf: str, count: Optional[int]
    ) -> Dict[str, Any]:
        bld_count = count if count is not None else 0
        if bld_count == 0:
            action = "Structural Baseline Monitoring (No Submerged Structures)"
            itype = "monitoring"
            reason = "Zero building footprints intersected detected flood extent; no immediate structural intervention required."
            field_req = False
            urgency = "Routine Monitoring"
            practices = ["Standard municipal building code compliance"]
        else:
            action = "Structural Safety Inspection & Residential Rehabilitation"
            itype = "inspection"
            reason = (
                f"{bld_count} building footprints were submerged within satellite flood boundaries. "
                "Mandatory structural integrity inspections, electrical safety audits, and moisture/mold remediation are required before civilian re-occupancy."
            )
            field_req = True
            urgency = "Immediate"
            practices = [
                "Certified structural foundation and wall stability inspection",
                "Eco-friendly non-toxic disinfectant and moisture drying",
                "Elevated electrical breaker retrofitting above high-water mark",
            ]

        return {
            "category": "buildings",
            "category_name": name,
            "category_type": ctype,
            "location": loc,
            "damage_severity": severity,
            "recovery_classification": condition,
            "recommended_action": action,
            "intervention_type": itype,
            "reason": reason,
            "confidence": conf,
            "requires_field_verification": field_req,
            "sustainable_practices": practices,
            "urgency": urgency,
        }

    def _recommend_roads(
        self, name: str, ctype: str, severity: str, condition: str, loc: Any, conf: str, length: Optional[float]
    ) -> Dict[str, Any]:
        road_km = length if length is not None else 0.0
        if road_km == 0.0:
            action = "Transportation Corridor Monitoring (No Inundated Corridors)"
            itype = "monitoring"
            reason = "No road network segments intersected the flood extent; roads remain fully operational."
            field_req = False
            urgency = "Routine Monitoring"
            practices = ["Standard road asset management"]
        else:
            action = "Critical-Route Road Repair & Connectivity Restoration"
            itype = "repair"
            reason = (
                f"{road_km:.2f} km of transport corridor was submerged, creating physical access barriers. "
                "Roadbed subbase assessment, culvert wash-out inspection, and asphalt resurfacing are required to restore emergency and civilian transit."
            )
            field_req = True
            urgency = "Immediate"
            practices = [
                "Subgrade wash-out inspection prior to heavy vehicle reopening",
                "Permeable gravel shoulder reinforcement for drainage relief",
                "Re-use of recycled asphalt pavement (RAP) in non-structural base repairs",
            ]

        return {
            "category": "roads",
            "category_name": name,
            "category_type": ctype,
            "location": loc,
            "damage_severity": severity,
            "recovery_classification": condition,
            "recommended_action": action,
            "intervention_type": itype,
            "reason": reason,
            "confidence": conf,
            "requires_field_verification": field_req,
            "sustainable_practices": practices,
            "urgency": urgency,
        }

    def _recommend_drainage(
        self, name: str, ctype: str, severity: str, condition: str, loc: Any, conf: str, length: Optional[float]
    ) -> Dict[str, Any]:
        drainage_km = f"{length:.2f} km" if length else "drainage network"
        if condition == self.COND_NATURAL:
            action = "Drainage Capacity Baseline Monitoring"
            itype = "monitoring"
            reason = "Drainage channels operated within design thresholds; regular scheduled maintenance is adequate."
            field_req = False
            urgency = "Routine Monitoring"
            practices = ["Routine vegetative swale trimming"]
        else:
            action = "Drainage Infrastructure Inspection & Mechanized Desiltation"
            itype = "maintenance"
            reason = (
                f"Floodwaters transported substantial sediment and debris into stormwater channels and culverts ({drainage_km} affected). "
                "Immediate mechanized desiltation, debris rack clearing, and outfall bank reinforcement are required to restore baseline discharge capacity."
            )
            field_req = True
            urgency = "Immediate"
            practices = [
                "Mechanized suction desiltation preserving natural channel bed morphology",
                "Installation of sustainable debris trash racks at culvert headwalls",
                "Naturalized vegetative bioswale integration for stormwater pre-treatment",
            ]

        return {
            "category": "drainage",
            "category_name": name,
            "category_type": ctype,
            "location": loc,
            "damage_severity": severity,
            "recovery_classification": condition,
            "recommended_action": action,
            "intervention_type": itype,
            "reason": reason,
            "confidence": conf,
            "requires_field_verification": field_req,
            "sustainable_practices": practices,
            "urgency": urgency,
        }
