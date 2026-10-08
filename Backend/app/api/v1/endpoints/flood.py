"""
Flood Analysis API Endpoints for SatQuery Phase 1.

Provides endpoints for:
- Image upload validation
- Flood detection
- Polygon generation
- Impact analysis
- Evacuation candidate analysis
- Full pipeline execution
"""

import os
import uuid
import tempfile
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse, FileResponse

from app.core.config import settings
from app.schemas.flood import (
    UploadValidationResponse,
    ImageValidationResult,
    FloodDetectionResult,
    FloodPolygonResult,
    ImageStudyResult,
    ImpactMetrics,
    AffectedVillage,
    PriorityScore,
    EvacuationCandidatesResult,
    EvacuationCandidate,
    VLMAnalysisResult,
    PipelineResult,
)
from app.schemas.damage_assessment import (
    DamageAssessmentResult,
    DamageCategoryAssessment,
    DamageAssessmentSummary,
)
from app.schemas.recovery_recommendation import (
    RecoveryRecommendationsResult,
    RecoveryRecommendation,
)
from app.schemas.recovery_priority import (
    RecoveryPrioritiesResult,
    SectorRecoveryPriority,
)
from app.schemas.resource_optimization import (
    ResourceOptimizationResult,
    ResourceOptimizationSummary,
    AllocatedSectorSite,
    UnallocatedSectorSite,
)
from app.schemas.recovery_monitoring import (
    RecoveryMonitoringResult,
    RecoveryMonitoringSummary,
    MonitoredSectorTimeline,
    RecoveryObservation,
)
from app.schemas.recovery_diagnosis import (
    RecoveryStallDiagnosisResult,
    RecoveryStallDiagnosisSummary,
    StallDiagnosisItem,
    PossibleCause,
)
from app.schemas.recovery_verification import (
    RecoveryVerificationResult,
    RecoveryVerificationSummary,
    SectorRecoveryVerificationItem,
)



# In-memory session cache: session_id -> {mask_array, transform, crs, flood_geojson, pipeline_result, ...}
_session_cache: Dict[str, Dict[str, Any]] = {}

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_temp(upload_file: Any, suffix: str, tmpdir: str) -> str:
    """Save an uploaded file to a temp directory synchronously."""
    path = os.path.join(tmpdir, f"{uuid.uuid4().hex}{suffix}")
    content = upload_file.file.read()
    with open(path, "wb") as f:
        f.write(content)
    return path


def _cleanup_files(*paths: str) -> None:
    """Remove temporary files, ignoring errors."""
    for p in paths:
        try:
            if p and os.path.isfile(p):
                os.remove(p)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 1. Validate Image Pair
# ---------------------------------------------------------------------------

@router.post(
    "/validate",
    response_model=UploadValidationResponse,
    summary="Validate pre/post GeoTIFF image pair",
)
async def validate_images(
    background_tasks: BackgroundTasks,
    pre_flood: UploadFile = File(..., description="Pre-flood GeoTIFF image"),
    post_flood: UploadFile = File(..., description="Post-flood GeoTIFF image"),
) -> UploadValidationResponse:
    """
    Validate that both uploaded images are valid GeoTIFFs with geospatial metadata.
    Checks CRS, bounding box overlap, and dimension compatibility.
    """
    from app.services.image_validation import validate_image_pair

    tmpdir = tempfile.mkdtemp(prefix="satquery_")
    pre_path = _save_temp(pre_flood, ".tif", tmpdir)
    post_path = _save_temp(post_flood, ".tif", tmpdir)

    background_tasks.add_task(_cleanup_files, pre_path, post_path)

    result = validate_image_pair(pre_path, post_path)

    pre_result = ImageValidationResult(
        filename=pre_flood.filename or "pre_flood.tif", **{
            k: v for k, v in result["pre_flood"].items() if k != "filename"
        }
    )
    post_result = ImageValidationResult(
        filename=post_flood.filename or "post_flood.tif", **{
            k: v for k, v in result["post_flood"].items() if k != "filename"
        }
    )

    return UploadValidationResponse(
        pre_flood=pre_result,
        post_flood=post_result,
        compatible=result["compatible"],
        compatibility_notes=result["compatibility_notes"],
    )


# ---------------------------------------------------------------------------
# 2. Flood Detection
# ---------------------------------------------------------------------------

@router.post(
    "/detect",
    response_model=FloodDetectionResult,
    summary="Detect flood extent from image pair",
)
async def detect_flood(
    pre_flood: UploadFile = File(...),
    post_flood: UploadFile = File(...),
    method: str = Form("auto"),
    ndwi_green_band: int = Form(2),
    ndwi_nir_band: int = Form(4),
    morphology_iterations: int = Form(2),
    threshold: Optional[float] = Form(None),
    sar_polarization: Optional[str] = Form("auto"),
) -> FloodDetectionResult:
    """
    Run deterministic flood detection on uploaded GeoTIFF pair.
    Stores the flood mask in the session cache for downstream steps.
    """
    from app.services.flood_detection import FloodDetectionService

    session_id = uuid.uuid4().hex
    tmpdir = tempfile.mkdtemp(prefix="satquery_")
    pre_path = _save_temp(pre_flood, ".tif", tmpdir)
    post_path = _save_temp(post_flood, ".tif", tmpdir)

    options = {
        "method": method,
        "ndwi_green_band": ndwi_green_band,
        "ndwi_nir_band": ndwi_nir_band,
        "morphology_iterations": morphology_iterations,
        "threshold": threshold,
        "sar_polarization": sar_polarization,
    }

    result = FloodDetectionService().detect(pre_path, post_path, options)

    if result.get("success"):
        import rasterio
        with rasterio.open(pre_path) as ds:
            transform = ds.transform
            crs_wkt = ds.crs.to_wkt() if ds.crs else "EPSG:4326"

        _session_cache[session_id] = {
            "mask_array": result.pop("mask_array", None),
            "transform": transform,
            "crs_wkt": crs_wkt,
            "detection_result": result,
        }
        result["session_id"] = session_id

    _cleanup_files(pre_path, post_path)

    return FloodDetectionResult(**{k: v for k, v in result.items() if k in FloodDetectionResult.model_fields})


@router.post(
    "/detect/gee",
    response_model=FloodDetectionResult,
    summary="Detect real flood extent using Google Earth Engine Sentinel-1 GRD imagery",
)
async def detect_flood_gee(
    pre_start: str = Form("2019-10-15"),
    pre_end: str = Form("2019-11-04"),
    post_start: str = Form("2019-11-05"),
    post_end: str = Form("2019-11-15"),
    min_lon: float = Form(-1.25),
    min_lat: float = Form(53.50),
    max_lon: float = Form(-0.90),
    max_lat: float = Form(53.65),
    threshold_db: float = Form(-2.0),
    polarization: str = Form("VV"),
    pass_direction: str = Form("ASCENDING"),
) -> FloodDetectionResult:
    """
    Run real GEE Sentinel-1 SAR change detection for South Yorkshire / River Don (or custom AOI).
    Stores real flood mask and GeoJSON in session cache for downstream steps.
    """
    from app.services.gee_flood_detection import GEEFloodDetectionService

    session_id = uuid.uuid4().hex
    bbox = [min_lon, min_lat, max_lon, max_lat]

    gee_svc = GEEFloodDetectionService()
    result = gee_svc.detect_flood_sentinel1(
        bbox=bbox,
        pre_start=pre_start,
        pre_end=pre_end,
        post_start=post_start,
        post_end=post_end,
        threshold_db=threshold_db,
        polarization=polarization,
        pass_direction=pass_direction,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GEE Sentinel-1 flood detection failed: {result.get('error')}",
        )

    geojson = result.get("geojson")
    _session_cache[session_id] = {
        "flood_geojson": geojson,
        "detection_result": result,
        "crs_wkt": "EPSG:4326",
    }

    return FloodDetectionResult(**{k: v for k, v in result.items() if k in FloodDetectionResult.model_fields})


@router.post(
    "/image-study",
    response_model=ImageStudyResult,
    summary="Run Flood Image Study on dual georeferenced GeoTIFF rasters",
)
async def run_image_study(
    background_tasks: BackgroundTasks,
    pre_flood: UploadFile = File(..., description="Pre-flood georeferenced GeoTIFF image"),
    post_flood: UploadFile = File(..., description="Post-flood georeferenced GeoTIFF image"),
    method: str = Form("auto"),
) -> ImageStudyResult:
    """
    Run flood change detection and centroid calculation on two uploaded GeoTIFF rasters.
    Validates CRS/geotransform and rejects non-georeferenced images.
    Returns georeferenced flood GeoJSON, polygon count, flood area, and centroid coordinates.
    """
    from app.services.image_study import ImageStudyService

    session_id = uuid.uuid4().hex
    tmpdir = tempfile.mkdtemp(prefix="satquery_imagestudy_")
    pre_path = _save_temp(pre_flood, f"_pre_{session_id}.tif", tmpdir)
    post_path = _save_temp(post_flood, f"_post_{session_id}.tif", tmpdir)
    background_tasks.add_task(_cleanup_files, pre_path, post_path)

    try:
        svc = ImageStudyService()
        result = svc.analyze_pair(pre_path, post_path, options={"method": method})
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image Study processing failed: {exc}",
        )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Image Study analysis failed."),
        )

    result["session_id"] = session_id
    _session_cache[session_id] = {
        "flood_geojson": result.get("geojson"),
        "image_study_result": result,
    }

    return ImageStudyResult(**{k: v for k, v in result.items() if k in ImageStudyResult.model_fields})


# ---------------------------------------------------------------------------
# 3. Polygonize Flood Mask
# ---------------------------------------------------------------------------

@router.post(
    "/polygonize",
    response_model=FloodPolygonResult,
    summary="Convert flood mask to GeoJSON polygons",
)
async def polygonize(
    session_id: str = Form(...),
    simplify_tolerance: float = Form(0.0001),
) -> FloodPolygonResult:
    """
    Convert a previously computed flood mask to GeoJSON vector polygons.
    Requires a session_id from a prior /detect call.
    """
    from app.services.polygon_generation import PolygonGenerationService

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found. Run /detect first.",
        )

    mask_array = session.get("mask_array")
    transform = session.get("transform")
    crs_wkt = session.get("crs_wkt", "EPSG:4326")

    if mask_array is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Flood mask not found in session. Run /detect first.",
        )

    result = PolygonGenerationService().generate(mask_array, transform, crs_wkt, simplify_tolerance)

    if result.get("success") and result.get("geojson"):
        _session_cache[session_id]["flood_geojson"] = result["geojson"]
        _session_cache[session_id]["polygon_result"] = result

    return FloodPolygonResult(**{k: v for k, v in result.items() if k in FloodPolygonResult.model_fields})


# ---------------------------------------------------------------------------
# 4. Impact Analysis
# ---------------------------------------------------------------------------

@router.post(
    "/impact",
    summary="Calculate flood impact metrics from GIS datasets",
)
async def analyze_impact(session_id: str = Form(...)):
    """
    Compute flood impact metrics by overlaying flood polygons with available GIS datasets.
    Results depend on which datasets are loaded in the data/ directory.
    """
    from app.services.exposure_analysis import ExposureAnalysisService
    from app.services.impact_scoring import ImpactScoringService
    from app.services.gis_repository import GISRepository

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    flood_geojson = session.get("flood_geojson")
    if not flood_geojson:
        raise HTTPException(
            status_code=422,
            detail="Flood polygon GeoJSON not found. Run /polygonize first.",
        )

    gis_repo = GISRepository(settings.DATA_DIR)
    exposure_svc = ExposureAnalysisService()
    exposure = exposure_svc.calculate_exposure(flood_geojson, session_id, gis_repo)

    priority = ImpactScoringService().compute_priority_scores(exposure)

    _session_cache[session_id]["impact"] = exposure
    _session_cache[session_id]["priority_scores"] = priority

    return {
        "impact": exposure,
        "priority_scores": priority,
    }


# ---------------------------------------------------------------------------
# 5. Evacuation Candidates
# ---------------------------------------------------------------------------

@router.post(
    "/evacuation",
    summary="Identify candidate accessible sites for on-ground verification",
)
async def find_evacuation_candidates(
    session_id: str = Form(...),
    buffer_m: float = Form(100.0),
):
    """
    Identify candidate accessible sites outside the flood boundary.
    IMPORTANT: Results require on-ground verification. Not guaranteed safe zones.
    """
    from app.services.evacuation import EvacuationService
    from app.services.gis_repository import GISRepository

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    flood_geojson = session.get("flood_geojson")
    if not flood_geojson:
        raise HTTPException(
            status_code=422,
            detail="Flood polygon GeoJSON not found. Run /polygonize first.",
        )

    gis_repo = GISRepository(settings.DATA_DIR)
    evac_result = EvacuationService().find_candidates(flood_geojson, gis_repo, buffer_m)
    _session_cache[session_id]["evacuation"] = evac_result

    return evac_result


# ---------------------------------------------------------------------------
# 6. Full Pipeline
# ---------------------------------------------------------------------------

@router.post(
    "/pipeline",
    response_model=PipelineResult,
    summary="Run complete flood analysis pipeline end-to-end",
)
async def run_full_pipeline(
    pre_flood: UploadFile = File(...),
    post_flood: UploadFile = File(...),
    method: str = Form("auto"),
    simplify_tolerance: float = Form(0.0001),
    buffer_m: float = Form(100.0),
    threshold: Optional[float] = Form(None),
    sar_polarization: Optional[str] = Form("auto"),
) -> PipelineResult:
    """
    Execute the complete flood analysis pipeline in one request:
    Validate → Detect → Polygonize → Impact Analysis → Evacuation Candidates.

    Returns a consolidated PipelineResult. Optional steps that fail
    (due to missing GIS datasets) are reported but do not abort the pipeline.
    """
    from app.services.image_validation import validate_image_pair
    from app.services.flood_detection import FloodDetectionService
    from app.services.polygon_generation import PolygonGenerationService
    from app.services.exposure_analysis import ExposureAnalysisService
    from app.services.impact_scoring import ImpactScoringService
    from app.services.evacuation import EvacuationService
    from app.services.gis_repository import GISRepository

    session_id = uuid.uuid4().hex
    warnings = []
    tmpdir = tempfile.mkdtemp(prefix="satquery_")
    pre_path = _save_temp(pre_flood, f"_pre_{session_id}.tif", tmpdir)
    post_path = _save_temp(post_flood, f"_post_{session_id}.tif", tmpdir)

    pipeline = PipelineResult(session_id=session_id)

    # Step 1: Validate
    try:
        val_raw = validate_image_pair(pre_path, post_path)
        pre_r = ImageValidationResult(
            filename=pre_flood.filename or "pre_flood.tif",
            **{k: v for k, v in val_raw["pre_flood"].items() if k != "filename"},
        )
        post_r = ImageValidationResult(
            filename=post_flood.filename or "post_flood.tif",
            **{k: v for k, v in val_raw["post_flood"].items() if k != "filename"},
        )
        pipeline.validation = UploadValidationResponse(
            pre_flood=pre_r,
            post_flood=post_r,
            compatible=val_raw["compatible"],
            compatibility_notes=val_raw["compatibility_notes"],
        )
        if not val_raw["compatible"]:
            warnings.append("Image pair compatibility issues detected; proceeding anyway.")
    except Exception as exc:
        warnings.append(f"Validation step failed: {exc}")

    # Step 2: Detect
    detection_result_raw = None
    mask_array = None
    transform_obj = None
    crs_wkt = "EPSG:4326"
    try:
        options = {
            "method": method,
            "morphology_iterations": 2,
            "threshold": threshold,
            "sar_polarization": sar_polarization,
        }
        det_svc = FloodDetectionService()
        detection_result_raw = det_svc.detect(pre_path, post_path, options)
        mask_array = detection_result_raw.pop("mask_array", None)

        import rasterio
        with rasterio.open(pre_path) as ds:
            transform_obj = ds.transform
            crs_wkt = ds.crs.to_wkt() if ds.crs else "EPSG:4326"

        pipeline.detection = FloodDetectionResult(
            **{k: v for k, v in detection_result_raw.items() if k in FloodDetectionResult.model_fields}
        )
    except Exception as exc:
        warnings.append(f"Detection step failed: {exc}")
        pipeline.error = str(exc)

    # Step 3: Polygonize
    flood_geojson = None
    if mask_array is not None:
        try:
            poly_svc = PolygonGenerationService()
            poly_result = poly_svc.generate(mask_array, transform_obj, crs_wkt, simplify_tolerance)
            pipeline.polygons = FloodPolygonResult(
                **{k: v for k, v in poly_result.items() if k in FloodPolygonResult.model_fields}
            )
            flood_geojson = poly_result.get("geojson")
        except Exception as exc:
            warnings.append(f"Polygonization step failed: {exc}")

    # Step 4: Impact Analysis
    if flood_geojson:
        try:
            gis_repo = GISRepository(settings.DATA_DIR)
            exposure_svc = ExposureAnalysisService()
            exposure = exposure_svc.calculate_exposure(flood_geojson, session_id, gis_repo)

            affected_villages = [
                AffectedVillage(**v) for v in exposure.get("affected_villages", [])
            ]
            pipeline.impact = ImpactMetrics(
                affected_villages=affected_villages,
                affected_population=exposure.get("affected_population"),
                affected_buildings=exposure.get("affected_buildings"),
                affected_road_length_km=exposure.get("affected_road_length_km"),
                affected_villages_geojson=exposure.get("affected_villages_geojson"),
                affected_roads_geojson=exposure.get("affected_roads_geojson"),
                affected_buildings_geojson=exposure.get("affected_buildings_geojson"),
                data_availability=exposure.get("data_availability", {}),
                disclaimer=exposure.get("disclaimer", ""),
            )

            raw_priority = ImpactScoringService().compute_priority_scores(exposure)
            pipeline.priority_scores = [PriorityScore(**p) for p in raw_priority]
        except Exception as exc:
            warnings.append(f"Impact analysis step failed: {exc}")

        # Step 5: Evacuation Candidates
        try:
            gis_repo = GISRepository(settings.DATA_DIR)
            evac_raw = EvacuationService().find_candidates(flood_geojson, gis_repo, buffer_m)
            candidates = [EvacuationCandidate(**c) for c in evac_raw.get("candidates", [])]
            pipeline.evacuation = EvacuationCandidatesResult(
                candidates=candidates,
                total_found=evac_raw.get("total_found", 0),
                filtered_reason=evac_raw.get("filtered_reason", ""),
                disclaimer=evac_raw.get("disclaimer", ""),
            )
        except Exception as exc:
            warnings.append(f"Evacuation analysis step failed: {exc}")

        # Step 7: Post-Flood Environmental & Infrastructure Damage Assessment
        damage_raw = None
        try:
            from app.services.damage_assessment import DamageAssessmentService
            damage_svc = DamageAssessmentService()
            damage_raw = damage_svc.assess_damage(
                flood_geojson=flood_geojson,
                session_id=session_id,
                gis_repo=gis_repo,
                pre_path=pre_path,
                post_path=post_path,
                detection_result=detection_result_raw,
                exposure_result=exposure if 'exposure' in locals() else None,
            )
            categories = [DamageCategoryAssessment(**c) for c in damage_raw.get("categories", [])]
            summary = DamageAssessmentSummary(**damage_raw.get("summary", {}))
            pipeline.damage_assessment = DamageAssessmentResult(
                session_id=session_id,
                region=damage_raw.get("region"),
                summary=summary,
                categories=categories,
                data_availability=damage_raw.get("data_availability", {}),
                disclaimers=damage_raw.get("disclaimers", []),
            )
        except Exception as exc:
            warnings.append(f"Damage assessment step failed: {exc}")

        # Step 8: Sustainable Recovery Recommendations (Part 2)
        if pipeline.damage_assessment and damage_raw:
            try:
                from app.services.recovery_recommendation import RecoveryRecommendationService
                rec_svc = RecoveryRecommendationService()
                rec_raw = rec_svc.generate_recommendations(
                    damage_assessment=damage_raw,
                    session_id=session_id,
                    region=damage_raw.get("region"),
                )
                recommendations_list = [RecoveryRecommendation(**r) for r in rec_raw.get("recommendations", [])]
                pipeline.recovery_recommendations = RecoveryRecommendationsResult(
                    session_id=session_id,
                    region=rec_raw.get("region"),
                    total_recommendations=rec_raw.get("total_recommendations", len(recommendations_list)),
                    natural_recovery_count=rec_raw.get("natural_recovery_count", 0),
                    intervention_needed_count=rec_raw.get("intervention_needed_count", 0),
                    field_verification_count=rec_raw.get("field_verification_count", 0),
                    recommendations=recommendations_list,
                    disclaimer=rec_raw.get("disclaimer", ""),
                )
            except Exception as exc:
                warnings.append(f"Recovery recommendations step failed: {exc}")

        # Step 9: Recovery Priority Engine (Part 3)
        if pipeline.damage_assessment and pipeline.recovery_recommendations:
            try:
                from app.services.recovery_priority import RecoveryPriorityService
                prio_svc = RecoveryPriorityService()
                prio_raw = prio_svc.compute_recovery_priorities(
                    damage_assessment=damage_raw,
                    recovery_recommendations=rec_raw if 'rec_raw' in locals() and rec_raw else pipeline.recovery_recommendations.model_dump(),
                    exposure_data=exposure if 'exposure' in locals() else None,
                    session_id=session_id,
                    region=damage_raw.get("region"),
                )
                priorities_list = [SectorRecoveryPriority(**p) for p in prio_raw.get("priorities", [])]
                pipeline.recovery_priorities = RecoveryPrioritiesResult(
                    session_id=session_id,
                    region=prio_raw.get("region"),
                    total_sectors_evaluated=prio_raw.get("total_sectors_evaluated", len(priorities_list)),
                    high_priority_count=prio_raw.get("high_priority_count", 0),
                    medium_priority_count=prio_raw.get("medium_priority_count", 0),
                    low_priority_count=prio_raw.get("low_priority_count", 0),
                    priorities=priorities_list,
                    disclaimer=prio_raw.get("disclaimer", ""),
                )
            except Exception as exc:
                warnings.append(f"Recovery priorities step failed: {exc}")

        # Step 10: Resource / Budget Optimization (Part 4)
        if pipeline.recovery_priorities and 'prio_raw' in locals() and prio_raw:
            try:
                from app.services.resource_optimization import ResourceOptimizationService
                opt_svc = ResourceOptimizationService()
                opt_raw = opt_svc.optimize_resources(
                    recovery_priorities=prio_raw,
                    budget_lakhs=10.0,
                    max_capacity_sites=5,
                    allow_natural_recovery_funding=False,
                    session_id=session_id,
                    region=damage_raw.get("region") if damage_raw else None,
                )
                pipeline.resource_optimization = ResourceOptimizationResult(
                    session_id=session_id,
                    region=opt_raw.get("region"),
                    summary=ResourceOptimizationSummary(**opt_raw.get("summary", {})),
                    selected_sites=[AllocatedSectorSite(**s) for s in opt_raw.get("selected_sites", [])],
                    unselected_sites=[UnallocatedSectorSite(**u) for u in opt_raw.get("unselected_sites", [])],
                    allocation_notes=opt_raw.get("allocation_notes", []),
                    disclaimer=opt_raw.get("disclaimer", ""),
                )
            except Exception as exc:
                warnings.append(f"Resource optimization step failed: {exc}")

        # Step 11: Recovery Timeline & Satellite-Based Monitoring (Part 5)
        if pipeline.damage_assessment and damage_raw:
            try:
                from app.services.recovery_monitoring import RecoveryMonitoringService
                mon_svc = RecoveryMonitoringService()
                mon_raw = mon_svc.generate_recovery_timelines(
                    damage_assessment=damage_raw,
                    recovery_recommendations=rec_raw if 'rec_raw' in locals() and rec_raw else None,
                    recovery_priorities=prio_raw if 'prio_raw' in locals() and prio_raw else None,
                    resource_optimization=opt_raw if 'opt_raw' in locals() and opt_raw else None,
                    session_id=session_id,
                    region=damage_raw.get("region"),
                )
                timelines_list = []
                for t in mon_raw.get("timelines", []):
                    obs_list = [RecoveryObservation(**o) for o in t.get("observations", [])]
                    timelines_list.append(MonitoredSectorTimeline(
                        **{**t, "observations": obs_list}
                    ))
                pipeline.recovery_monitoring = RecoveryMonitoringResult(
                    session_id=session_id,
                    region=mon_raw.get("region"),
                    summary=RecoveryMonitoringSummary(**mon_raw.get("summary", {})),
                    timelines=timelines_list,
                    methodology_notes=mon_raw.get("methodology_notes", []),
                    disclaimer=mon_raw.get("disclaimer", ""),
                )
            except Exception as exc:
                warnings.append(f"Recovery monitoring step failed: {exc}")

        # Step 12: Recovery Failure / Stall Diagnosis (Part 6)
        if pipeline.recovery_monitoring and 'mon_raw' in locals() and mon_raw:
            try:
                from app.services.recovery_diagnosis import RecoveryStallDiagnosisService
                diag_svc = RecoveryStallDiagnosisService()
                diag_raw = diag_svc.diagnose_stalls(
                    recovery_monitoring=mon_raw,
                    damage_assessment=damage_raw if 'damage_raw' in locals() else None,
                    recovery_recommendations=rec_raw if 'rec_raw' in locals() else None,
                    recovery_priorities=prio_raw if 'prio_raw' in locals() else None,
                    session_id=session_id,
                    region=damage_raw.get("region") if damage_raw else None,
                )
                diag_items = []
                for d in diag_raw.get("diagnoses", []):
                    causes_list = [PossibleCause(**c) for c in d.get("possible_causes", [])]
                    diag_items.append(StallDiagnosisItem(
                        **{**d, "possible_causes": causes_list}
                    ))
                pipeline.recovery_diagnosis = RecoveryStallDiagnosisResult(
                    session_id=session_id,
                    region=diag_raw.get("region"),
                    summary=RecoveryStallDiagnosisSummary(**diag_raw.get("summary", {})),
                    diagnoses=diag_items,
                    methodology_notes=diag_raw.get("methodology_notes", []),
                    disclaimer=diag_raw.get("disclaimer", ""),
                )
            except Exception as exc:
                warnings.append(f"Recovery stall diagnosis step failed: {exc}")

        # Step 13: Recovery Verification (Part 7)
        if pipeline.damage_assessment and damage_raw:
            try:
                from app.services.recovery_verification import RecoveryVerificationService
                ver_svc = RecoveryVerificationService()
                ver_raw = ver_svc.verify_recovery(
                    damage_assessment=damage_raw,
                    recovery_recommendations=rec_raw if 'rec_raw' in locals() else None,
                    recovery_priorities=prio_raw if 'prio_raw' in locals() else None,
                    resource_optimization=opt_raw if 'opt_raw' in locals() else None,
                    recovery_monitoring=mon_raw if 'mon_raw' in locals() else None,
                    recovery_diagnosis=diag_raw if 'diag_raw' in locals() else None,
                    session_id=session_id,
                    region=damage_raw.get("region"),
                )
                ver_items = [SectorRecoveryVerificationItem(**v) for v in ver_raw.get("verifications", [])]
                pipeline.recovery_verification = RecoveryVerificationResult(
                    session_id=session_id,
                    region=ver_raw.get("region"),
                    summary=RecoveryVerificationSummary(**ver_raw.get("summary", {})),
                    verifications=ver_items,
                    methodology_notes=ver_raw.get("methodology_notes", []),
                    disclaimer=ver_raw.get("disclaimer", ""),
                )
            except Exception as exc:
                warnings.append(f"Recovery verification step failed: {exc}")



    # Step 6: VLM Visual Comparison (Gemini Multimodal visual change description)
    try:
        from app.services.orchestration import AgentOrchestrationService
        orchestration_svc = AgentOrchestrationService(api_key=settings.GEMINI_API_KEY)
        vlm_res = orchestration_svc.generate_visual_comparison(pre_path, post_path)
        pipeline.vlm_analysis = VLMAnalysisResult(**vlm_res)
    except Exception as exc:
        warnings.append(f"VLM visual comparison step encountered an error: {exc}")
        pipeline.vlm_analysis = VLMAnalysisResult(
            available=False,
            comparison="VLM visual comparison could not be performed.",
        )

    # Cache pipeline result for AI assistant
    pipeline.warnings = warnings
    _session_cache[session_id] = {
        "mask_array": mask_array,
        "transform": transform_obj,
        "crs_wkt": crs_wkt,
        "flood_geojson": flood_geojson,
        "pipeline_result": pipeline.model_dump(),
    }

    _cleanup_files(pre_path, post_path)
    return pipeline


# ---------------------------------------------------------------------------
# 6b. Post-Flood Damage Assessment On-Demand Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/damage-assessment",
    response_model=DamageAssessmentResult,
    summary="Run Post-Flood Environmental & Infrastructure Damage Assessment",
)
async def calculate_damage_assessment(
    session_id: str = Form(...),
) -> DamageAssessmentResult:
    """
    Compute post-flood environmental & infrastructure damage metrics across 8 categories
    with standardized 4-tier recovery classifications and epistemic modesty standards.
    """
    from app.services.damage_assessment import DamageAssessmentService
    from app.services.gis_repository import GISRepository

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    flood_geojson = session.get("flood_geojson")
    if not flood_geojson:
        raise HTTPException(
            status_code=422,
            detail="Flood polygon GeoJSON not found in session. Run /polygonize or /pipeline first.",
        )

    gis_repo = GISRepository(settings.DATA_DIR)
    damage_svc = DamageAssessmentService()
    exposure = session.get("impact")
    detection = session.get("detection_result")

    damage_raw = damage_svc.assess_damage(
        flood_geojson=flood_geojson,
        session_id=session_id,
        gis_repo=gis_repo,
        detection_result=detection,
        exposure_result=exposure,
    )

    categories = [DamageCategoryAssessment(**c) for c in damage_raw.get("categories", [])]
    summary = DamageAssessmentSummary(**damage_raw.get("summary", {}))
    result = DamageAssessmentResult(
        session_id=session_id,
        region=damage_raw.get("region"),
        summary=summary,
        categories=categories,
        data_availability=damage_raw.get("data_availability", {}),
        disclaimers=damage_raw.get("disclaimers", []),
    )
    _session_cache[session_id]["damage_assessment"] = result.model_dump()
    return result


# ---------------------------------------------------------------------------
# 6c. Sustainable Recovery Recommendations On-Demand Endpoint (Part 2)
# ---------------------------------------------------------------------------

@router.post(
    "/recommendations",
    response_model=RecoveryRecommendationsResult,
    summary="Generate Sustainable Recovery Recommendations",
)
async def generate_recovery_recommendations(
    session_id: str = Form(...),
) -> RecoveryRecommendationsResult:
    """
    Generate evidence-based sustainable recovery recommendations based on Damage Type + Severity + Recovery Condition.
    Includes explicit justifications for why intervention is or is not recommended.
    """
    from app.services.recovery_recommendation import RecoveryRecommendationService
    from app.services.damage_assessment import DamageAssessmentService
    from app.services.gis_repository import GISRepository

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    damage_dict = session.get("damage_assessment")
    if not damage_dict:
        # Compute damage assessment if not cached
        flood_geojson = session.get("flood_geojson")
        if not flood_geojson:
            raise HTTPException(
                status_code=422,
                detail="Flood polygon GeoJSON not found in session. Run /pipeline first.",
            )
        gis_repo = GISRepository(settings.DATA_DIR)
        damage_svc = DamageAssessmentService()
        exposure = session.get("impact")
        detection = session.get("detection_result")
        damage_dict = damage_svc.assess_damage(
            flood_geojson=flood_geojson,
            session_id=session_id,
            gis_repo=gis_repo,
            detection_result=detection,
            exposure_result=exposure,
        )
        session["damage_assessment"] = damage_dict

    rec_svc = RecoveryRecommendationService()
    rec_raw = rec_svc.generate_recommendations(
        damage_assessment=damage_dict,
        session_id=session_id,
        region=damage_dict.get("region"),
    )

    recommendations_list = [RecoveryRecommendation(**r) for r in rec_raw.get("recommendations", [])]
    result = RecoveryRecommendationsResult(
        session_id=session_id,
        region=rec_raw.get("region"),
        total_recommendations=rec_raw.get("total_recommendations", len(recommendations_list)),
        natural_recovery_count=rec_raw.get("natural_recovery_count", 0),
        intervention_needed_count=rec_raw.get("intervention_needed_count", 0),
        field_verification_count=rec_raw.get("field_verification_count", 0),
        recommendations=recommendations_list,
        disclaimer=rec_raw.get("disclaimer", ""),
    )
    _session_cache[session_id]["recovery_recommendations"] = result.model_dump()
    return result


# ---------------------------------------------------------------------------
# 6d. Recovery Priority Engine On-Demand Endpoint (Part 3)
# ---------------------------------------------------------------------------

@router.post(
    "/priorities",
    response_model=RecoveryPrioritiesResult,
    summary="Compute Recovery Priorities Across Evaluated Sectors",
)
async def calculate_recovery_priorities(
    session_id: str = Form(...),
) -> RecoveryPrioritiesResult:
    """
    Compute evidence-based recovery priorities (HIGH / MEDIUM / LOW) and ranking scores
    across all evaluated environmental and infrastructure sectors.
    """
    from app.services.recovery_priority import RecoveryPriorityService
    from app.services.recovery_recommendation import RecoveryRecommendationService
    from app.services.damage_assessment import DamageAssessmentService
    from app.services.gis_repository import GISRepository

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    damage_dict = session.get("damage_assessment")
    if not damage_dict:
        flood_geojson = session.get("flood_geojson")
        if not flood_geojson:
            raise HTTPException(
                status_code=422,
                detail="Flood polygon GeoJSON not found in session. Run /pipeline first.",
            )
        gis_repo = GISRepository(settings.DATA_DIR)
        damage_svc = DamageAssessmentService()
        exposure = session.get("impact")
        detection = session.get("detection_result")
        damage_dict = damage_svc.assess_damage(
            flood_geojson=flood_geojson,
            session_id=session_id,
            gis_repo=gis_repo,
            detection_result=detection,
            exposure_result=exposure,
        )
        session["damage_assessment"] = damage_dict

    rec_dict = session.get("recovery_recommendations")
    if not rec_dict:
        rec_svc = RecoveryRecommendationService()
        rec_dict = rec_svc.generate_recommendations(
            damage_assessment=damage_dict,
            session_id=session_id,
            region=damage_dict.get("region"),
        )
        session["recovery_recommendations"] = rec_dict

    prio_svc = RecoveryPriorityService()
    exposure = session.get("impact")
    prio_raw = prio_svc.compute_recovery_priorities(
        damage_assessment=damage_dict,
        recovery_recommendations=rec_dict,
        exposure_data=exposure,
        session_id=session_id,
        region=damage_dict.get("region"),
    )

    priorities_list = [SectorRecoveryPriority(**p) for p in prio_raw.get("priorities", [])]
    result = RecoveryPrioritiesResult(
        session_id=session_id,
        region=prio_raw.get("region"),
        total_sectors_evaluated=prio_raw.get("total_sectors_evaluated", len(priorities_list)),
        high_priority_count=prio_raw.get("high_priority_count", 0),
        medium_priority_count=prio_raw.get("medium_priority_count", 0),
        low_priority_count=prio_raw.get("low_priority_count", 0),
        priorities=priorities_list,
        disclaimer=prio_raw.get("disclaimer", ""),
    )
    _session_cache[session_id]["recovery_priorities"] = result.model_dump()
    return result


# ---------------------------------------------------------------------------
# 6e. Resource / Budget Optimization On-Demand Endpoint (Part 4)
# ---------------------------------------------------------------------------

@router.post(
    "/optimize-resources",
    response_model=ResourceOptimizationResult,
    summary="Simulate Resource and Budget Allocation Across Priorities",
)
async def optimize_recovery_resources(
    session_id: str = Form(...),
    budget_lakhs: float = Form(10.0),
    max_capacity_sites: int = Form(5),
    allow_natural_recovery: bool = Form(False),
    domain_filter: Optional[str] = Form(None),
) -> ResourceOptimizationResult:
    """
    Simulate optimal distribution of limited recovery resources (budget & workforce capacity)
    among prioritized sectors.
    """
    from app.services.resource_optimization import ResourceOptimizationService
    from app.services.recovery_priority import RecoveryPriorityService
    from app.services.recovery_recommendation import RecoveryRecommendationService
    from app.services.damage_assessment import DamageAssessmentService
    from app.services.gis_repository import GISRepository

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    prio_dict = session.get("recovery_priorities")
    if not prio_dict:
        damage_dict = session.get("damage_assessment")
        if not damage_dict:
            flood_geojson = session.get("flood_geojson")
            if not flood_geojson:
                raise HTTPException(
                    status_code=422,
                    detail="Flood polygon GeoJSON not found in session. Run /pipeline first.",
                )
            gis_repo = GISRepository(settings.DATA_DIR)
            damage_svc = DamageAssessmentService()
            exposure = session.get("impact")
            detection = session.get("detection_result")
            damage_dict = damage_svc.assess_damage(
                flood_geojson=flood_geojson,
                session_id=session_id,
                gis_repo=gis_repo,
                detection_result=detection,
                exposure_result=exposure,
            )
            session["damage_assessment"] = damage_dict

        rec_dict = session.get("recovery_recommendations")
        if not rec_dict:
            rec_svc = RecoveryRecommendationService()
            rec_dict = rec_svc.generate_recommendations(
                damage_assessment=damage_dict,
                session_id=session_id,
                region=damage_dict.get("region"),
            )
            session["recovery_recommendations"] = rec_dict

        prio_svc = RecoveryPriorityService()
        exposure = session.get("impact")
        prio_dict = prio_svc.compute_recovery_priorities(
            damage_assessment=damage_dict,
            recovery_recommendations=rec_dict,
            exposure_data=exposure,
            session_id=session_id,
            region=damage_dict.get("region"),
        )
        session["recovery_priorities"] = prio_dict

    opt_svc = ResourceOptimizationService()
    opt_raw = opt_svc.optimize_resources(
        recovery_priorities=prio_dict,
        budget_lakhs=budget_lakhs,
        max_capacity_sites=max_capacity_sites,
        allow_natural_recovery_funding=allow_natural_recovery,
        domain_filter=domain_filter,
        session_id=session_id,
        region=prio_dict.get("region"),
    )

    result = ResourceOptimizationResult(
        session_id=session_id,
        region=opt_raw.get("region"),
        summary=ResourceOptimizationSummary(**opt_raw.get("summary", {})),
        selected_sites=[AllocatedSectorSite(**s) for s in opt_raw.get("selected_sites", [])],
        unselected_sites=[UnallocatedSectorSite(**u) for u in opt_raw.get("unselected_sites", [])],
        allocation_notes=opt_raw.get("allocation_notes", []),
        disclaimer=opt_raw.get("disclaimer", ""),
    )
    _session_cache[session_id]["resource_optimization"] = result.model_dump()
    return result


# ---------------------------------------------------------------------------
# 6f. Recovery Timeline & Satellite-Based Monitoring On-Demand Endpoint (Part 5)
# ---------------------------------------------------------------------------

@router.post(
    "/monitoring",
    response_model=RecoveryMonitoringResult,
    summary="Generate Multi-Temporal Recovery Timeline & Satellite Monitoring",
)
async def generate_recovery_monitoring(
    session_id: str = Form(...),
) -> RecoveryMonitoringResult:
    """
    Generate chronological satellite recovery tracking sequence across all evaluated sectors.
    Classifies trajectories into 'Recovery On Track', 'Recovery Lagging', or 'Recovery Stalled'.
    """
    from app.services.recovery_monitoring import RecoveryMonitoringService
    from app.services.resource_optimization import ResourceOptimizationService
    from app.services.recovery_priority import RecoveryPriorityService
    from app.services.recovery_recommendation import RecoveryRecommendationService
    from app.services.damage_assessment import DamageAssessmentService
    from app.services.gis_repository import GISRepository

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    damage_dict = session.get("damage_assessment")
    if not damage_dict:
        flood_geojson = session.get("flood_geojson")
        if not flood_geojson:
            raise HTTPException(
                status_code=422,
                detail="Flood polygon GeoJSON not found in session. Run /pipeline first.",
            )
        gis_repo = GISRepository(settings.DATA_DIR)
        damage_svc = DamageAssessmentService()
        exposure = session.get("impact")
        detection = session.get("detection_result")
        damage_dict = damage_svc.assess_damage(
            flood_geojson=flood_geojson,
            session_id=session_id,
            gis_repo=gis_repo,
            detection_result=detection,
            exposure_result=exposure,
        )
        session["damage_assessment"] = damage_dict

    rec_dict = session.get("recovery_recommendations")
    if not rec_dict:
        rec_svc = RecoveryRecommendationService()
        rec_dict = rec_svc.generate_recommendations(
            damage_assessment=damage_dict,
            session_id=session_id,
            region=damage_dict.get("region"),
        )
        session["recovery_recommendations"] = rec_dict

    prio_dict = session.get("recovery_priorities")
    if not prio_dict:
        prio_svc = RecoveryPriorityService()
        exposure = session.get("impact")
        prio_dict = prio_svc.compute_recovery_priorities(
            damage_assessment=damage_dict,
            recovery_recommendations=rec_dict,
            exposure_data=exposure,
            session_id=session_id,
            region=damage_dict.get("region"),
        )
        session["recovery_priorities"] = prio_dict

    opt_dict = session.get("resource_optimization")

    mon_svc = RecoveryMonitoringService()
    mon_raw = mon_svc.generate_recovery_timelines(
        damage_assessment=damage_dict,
        recovery_recommendations=rec_dict,
        recovery_priorities=prio_dict,
        resource_optimization=opt_dict,
        session_id=session_id,
        region=damage_dict.get("region"),
    )

    timelines_list = []
    for t in mon_raw.get("timelines", []):
        obs_list = [RecoveryObservation(**o) for o in t.get("observations", [])]
        timelines_list.append(MonitoredSectorTimeline(
            **{**t, "observations": obs_list}
        ))

    result = RecoveryMonitoringResult(
        session_id=session_id,
        region=mon_raw.get("region"),
        summary=RecoveryMonitoringSummary(**mon_raw.get("summary", {})),
        timelines=timelines_list,
        methodology_notes=mon_raw.get("methodology_notes", []),
        disclaimer=mon_raw.get("disclaimer", ""),
    )
    _session_cache[session_id]["recovery_monitoring"] = result.model_dump()
    return result


# ---------------------------------------------------------------------------
# 6g. Recovery Failure / Stall Diagnosis On-Demand Endpoint (Part 6)
# ---------------------------------------------------------------------------

@router.post(
    "/diagnosis",
    response_model=RecoveryStallDiagnosisResult,
    summary="Diagnose Recovery Bottlenecks, Stalls, and Failures Across Sectors (Part 6)",
)
async def diagnose_recovery_stalls(
    session_id: str = Form(...),
) -> RecoveryStallDiagnosisResult:
    """
    Diagnose potential causes and environmental bottlenecks for lagging or stalled recovery trajectories.
    Identifies evidence-based physical mechanisms and delivers adaptive decision-support recommendations.
    """
    from app.services.recovery_diagnosis import RecoveryStallDiagnosisService
    from app.services.recovery_monitoring import RecoveryMonitoringService
    from app.services.resource_optimization import ResourceOptimizationService
    from app.services.recovery_priority import RecoveryPriorityService
    from app.services.recovery_recommendation import RecoveryRecommendationService
    from app.services.damage_assessment import DamageAssessmentService
    from app.services.gis_repository import GISRepository

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    mon_dict = session.get("recovery_monitoring")
    damage_dict = session.get("damage_assessment")

    if not mon_dict or not damage_dict:
        flood_geojson = session.get("flood_geojson")
        if not flood_geojson:
            raise HTTPException(
                status_code=422,
                detail="Flood polygon GeoJSON not found in session. Run /pipeline first.",
            )
        gis_repo = GISRepository(settings.DATA_DIR)
        damage_svc = DamageAssessmentService()
        exposure = session.get("impact")
        detection = session.get("detection_result")
        damage_dict = damage_svc.assess_damage(
            flood_geojson=flood_geojson,
            session_id=session_id,
            gis_repo=gis_repo,
            detection_result=detection,
            exposure_result=exposure,
        )
        session["damage_assessment"] = damage_dict

        rec_dict = session.get("recovery_recommendations")
        if not rec_dict:
            rec_svc = RecoveryRecommendationService()
            rec_dict = rec_svc.generate_recommendations(
                damage_assessment=damage_dict,
                session_id=session_id,
                region=damage_dict.get("region"),
            )
            session["recovery_recommendations"] = rec_dict

        prio_dict = session.get("recovery_priorities")
        if not prio_dict:
            prio_svc = RecoveryPriorityService()
            prio_dict = prio_svc.compute_recovery_priorities(
                damage_assessment=damage_dict,
                recovery_recommendations=rec_dict,
                exposure_data=exposure,
                session_id=session_id,
                region=damage_dict.get("region"),
            )
            session["recovery_priorities"] = prio_dict

        opt_dict = session.get("resource_optimization")

        mon_svc = RecoveryMonitoringService()
        mon_dict = mon_svc.generate_recovery_timelines(
            damage_assessment=damage_dict,
            recovery_recommendations=rec_dict,
            recovery_priorities=prio_dict,
            resource_optimization=opt_dict,
            session_id=session_id,
            region=damage_dict.get("region"),
        )
        session["recovery_monitoring"] = mon_dict

    diag_svc = RecoveryStallDiagnosisService()
    diag_raw = diag_svc.diagnose_stalls(
        recovery_monitoring=mon_dict,
        damage_assessment=damage_dict,
        recovery_recommendations=session.get("recovery_recommendations"),
        recovery_priorities=session.get("recovery_priorities"),
        session_id=session_id,
        region=damage_dict.get("region") if damage_dict else None,
    )

    diag_items = []
    for d in diag_raw.get("diagnoses", []):
        causes_list = [PossibleCause(**c) for c in d.get("possible_causes", [])]
        diag_items.append(StallDiagnosisItem(
            **{**d, "possible_causes": causes_list}
        ))

    result = RecoveryStallDiagnosisResult(
        session_id=session_id,
        region=diag_raw.get("region"),
        summary=RecoveryStallDiagnosisSummary(**diag_raw.get("summary", {})),
        diagnoses=diag_items,
        methodology_notes=diag_raw.get("methodology_notes", []),
        disclaimer=diag_raw.get("disclaimer", ""),
    )
    _session_cache[session_id]["recovery_diagnosis"] = result.model_dump()
    return result


# ---------------------------------------------------------------------------
# 6h. Recovery Verification On-Demand Endpoint (Part 7)
# ---------------------------------------------------------------------------

@router.post(
    "/verification",
    response_model=RecoveryVerificationResult,
    summary="Verify Post-Flood Recovery Outcomes Across Sectors (Part 7)",
)
async def verify_recovery_outcomes(
    session_id: str = Form(...),
) -> RecoveryVerificationResult:
    """
    Evaluate whether recommended or funded recovery interventions produced measurable improvement
    based on available satellite observations and monitoring evidence.
    Modeled projections are transparently categorized as 'INSUFFICIENT DATA'.
    """
    from app.services.recovery_verification import RecoveryVerificationService
    from app.services.recovery_diagnosis import RecoveryStallDiagnosisService
    from app.services.recovery_monitoring import RecoveryMonitoringService
    from app.services.resource_optimization import ResourceOptimizationService
    from app.services.recovery_priority import RecoveryPriorityService
    from app.services.recovery_recommendation import RecoveryRecommendationService
    from app.services.damage_assessment import DamageAssessmentService
    from app.services.gis_repository import GISRepository

    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    damage_dict = session.get("damage_assessment")
    if not damage_dict:
        flood_geojson = session.get("flood_geojson")
        if not flood_geojson:
            raise HTTPException(
                status_code=422,
                detail="Flood polygon GeoJSON not found in session. Run /pipeline first.",
            )
        gis_repo = GISRepository(settings.DATA_DIR)
        damage_svc = DamageAssessmentService()
        exposure = session.get("impact")
        detection = session.get("detection_result")
        damage_dict = damage_svc.assess_damage(
            flood_geojson=flood_geojson,
            session_id=session_id,
            gis_repo=gis_repo,
            detection_result=detection,
            exposure_result=exposure,
        )
        session["damage_assessment"] = damage_dict

    rec_dict = session.get("recovery_recommendations")
    if not rec_dict:
        rec_svc = RecoveryRecommendationService()
        rec_dict = rec_svc.generate_recommendations(
            damage_assessment=damage_dict,
            session_id=session_id,
            region=damage_dict.get("region"),
        )
        session["recovery_recommendations"] = rec_dict

    prio_dict = session.get("recovery_priorities")
    if not prio_dict:
        prio_svc = RecoveryPriorityService()
        exposure = session.get("impact")
        prio_dict = prio_svc.compute_recovery_priorities(
            damage_assessment=damage_dict,
            recovery_recommendations=rec_dict,
            exposure_data=exposure,
            session_id=session_id,
            region=damage_dict.get("region"),
        )
        session["recovery_priorities"] = prio_dict

    opt_dict = session.get("resource_optimization")

    mon_dict = session.get("recovery_monitoring")
    if not mon_dict:
        mon_svc = RecoveryMonitoringService()
        mon_dict = mon_svc.generate_recovery_timelines(
            damage_assessment=damage_dict,
            recovery_recommendations=rec_dict,
            recovery_priorities=prio_dict,
            resource_optimization=opt_dict,
            session_id=session_id,
            region=damage_dict.get("region"),
        )
        session["recovery_monitoring"] = mon_dict

    diag_dict = session.get("recovery_diagnosis")
    if not diag_dict:
        diag_svc = RecoveryStallDiagnosisService()
        diag_dict = diag_svc.diagnose_stalls(
            recovery_monitoring=mon_dict,
            damage_assessment=damage_dict,
            recovery_recommendations=rec_dict,
            recovery_priorities=prio_dict,
            session_id=session_id,
            region=damage_dict.get("region"),
        )
        session["recovery_diagnosis"] = diag_dict

    ver_svc = RecoveryVerificationService()
    ver_raw = ver_svc.verify_recovery(
        damage_assessment=damage_dict,
        recovery_recommendations=rec_dict,
        recovery_priorities=prio_dict,
        resource_optimization=opt_dict,
        recovery_monitoring=mon_dict,
        recovery_diagnosis=diag_dict,
        session_id=session_id,
        region=damage_dict.get("region"),
    )

    ver_items = [SectorRecoveryVerificationItem(**v) for v in ver_raw.get("verifications", [])]
    result = RecoveryVerificationResult(
        session_id=session_id,
        region=ver_raw.get("region"),
        summary=RecoveryVerificationSummary(**ver_raw.get("summary", {})),
        verifications=ver_items,
        methodology_notes=ver_raw.get("methodology_notes", []),
        disclaimer=ver_raw.get("disclaimer", ""),
    )
    _session_cache[session_id]["recovery_verification"] = result.model_dump()
    return result


# ---------------------------------------------------------------------------
# 7. Spatial Layers Access
# ---------------------------------------------------------------------------

@router.get(
    "/buildings",
    summary="Retrieve building footprints GeoJSON",
)
async def get_buildings():
    """Return building footprints GeoJSON from data/buildings/."""
    from app.services.gis_repository import GISRepository
    import json
    gis_repo = GISRepository(settings.DATA_DIR)
    bld_gdf = gis_repo.load_layer("buildings")
    if bld_gdf is not None:
        if bld_gdf.crs != "EPSG:4326":
            bld_gdf = bld_gdf.to_crs("EPSG:4326")
        return json.loads(bld_gdf.to_json())
    return {"type": "FeatureCollection", "features": []}


# ---------------------------------------------------------------------------
# 8. Session Management
# ---------------------------------------------------------------------------

@router.get(
    "/session/{session_id}",
    summary="Retrieve cached session results",
)
async def get_session_results(session_id: str):
    """Return cached pipeline results for a given session ID."""
    session = _session_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    # Return only serializable data (exclude numpy arrays)
    return {k: v for k, v in session.items() if k not in ("mask_array", "transform")}


@router.delete(
    "/session/{session_id}",
    summary="Delete a cached session",
)
async def delete_session(session_id: str):
    """Remove a session from the in-memory cache."""
    if session_id in _session_cache:
        del _session_cache[session_id]
        return {"deleted": True, "session_id": session_id}
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")


# ---------------------------------------------------------------------------
# 9. Sample Test Images & Demo Datasets
# ---------------------------------------------------------------------------

@router.get(
    "/demos",
    summary="List available demo events",
)
async def get_demos():
    """List available demo options: Kerala Flood and Nepal 2026 Flood."""
    return [
        {
            "id": "kerala",
            "name": "Kerala Flood",
            "region": "Kerala, India",
            "pre_file": "kerala_before_flood.tif",
            "post_file": "kerala_after_flood.tif",
            "description": "Real Sentinel satellite imagery for the August 2018 Kerala flood event.",
        },
        {
            "id": "nepal",
            "name": "Nepal 2026 Flood",
            "region": "Rasuwa, Nepal",
            "pre_file": "nepal_before_flood.tif",
            "post_file": "nepal_after_flood.tif",
            "description": "Real Sentinel-2 Harmonized optical imagery for the August 2026 Nepal flood event.",
        },
    ]


@router.get(
    "/demo-file/{filename}",
    summary="Download real demo GeoTIFF raster file",
)
async def get_demo_file(filename: str):
    """Serve pre-existing real demo GeoTIFF raster file for Kerala or Nepal demo."""
    allowed = [
        "kerala_before_flood.tif",
        "kerala_after_flood.tif",
        "nepal_before_flood.tif",
        "nepal_after_flood.tif",
    ]
    if filename not in allowed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo file '{filename}' not found. Available: {allowed}",
        )
    file_path = os.path.join(settings.DATA_DIR, "test_images", filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo file '{filename}' not found on server disk.",
        )
    return FileResponse(file_path, media_type="image/tiff", filename=filename)


@router.get(
    "/sample/{sample_name}",
    summary="Download sample satellite GeoTIFF files",
)
async def get_sample_image(sample_name: str):
    """Serve real Kerala and Nepal pre/post flood sample images."""
    allowed = {
        "pre": "kerala_before_flood.tif",
        "post": "kerala_after_flood.tif",
        "kerala_before_flood.tif": "kerala_before_flood.tif",
        "kerala_after_flood.tif": "kerala_after_flood.tif",
        "nepal_before_flood.tif": "nepal_before_flood.tif",
        "nepal_after_flood.tif": "nepal_after_flood.tif",
    }
    if sample_name not in allowed:
        raise HTTPException(status_code=404, detail="Sample image not found")
    filename = allowed[sample_name]
    path = os.path.join(settings.DATA_DIR, "test_images", filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"Sample file '{filename}' missing on disk")
    return FileResponse(path, media_type="image/tiff", filename=filename)

