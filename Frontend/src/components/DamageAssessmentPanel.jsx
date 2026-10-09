import React, { useState, useEffect, useMemo } from 'react';
import {
  ClipboardCheck,
  Sprout,
  Wheat,
  Droplets,
  Layers,
  Trees,
  Building2,
  Navigation,
  GitFork,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Clock,
  Shield,
  Info,
  ChevronRight,
  Sparkles,
  Leaf,
  FileSearch,
  Flame,
  Award,
  SlidersHorizontal,
  Coins,
  Scale,
  RefreshCw,
  TrendingUp,
  Ban,
  Check,
  Focus,
  Activity,
  Calendar,
  Eye,
  Radio,
  Stethoscope,
  AlertOctagon,
  XCircle,
  Search,
  FileText,
  BadgeCheck,
  FileCheck2,
  CheckSquare,
} from 'lucide-react';
import { optimizeResources, fetchRecoveryMonitoring, fetchRecoveryDiagnosis, fetchRecoveryVerification } from '../services/api';

const CATEGORY_ICONS = {
  vegetation: Sprout,
  agriculture: Wheat,
  water_wetlands: Droplets,
  soil_land: Layers,
  habitats: Trees,
  buildings: Building2,
  roads: Navigation,
  drainage: GitFork,
};

const SEVERITY_BADGES = {
  Low: 'badge-low',
  Moderate: 'badge-moderate',
  Severe: 'badge-severe',
  Critical: 'badge-critical',
};

const RECOVERY_COLORS = {
  'Likely Natural Recovery': {
    badge: 'recovery-natural',
    icon: CheckCircle2,
    color: '#10b981',
    label: 'Likely Natural Recovery',
  },
  'Likely to recover naturally': {
    badge: 'recovery-natural',
    icon: CheckCircle2,
    color: '#10b981',
    label: 'Likely Natural Recovery',
  },
  'Recovery Assistance Needed': {
    badge: 'recovery-assistance',
    icon: Clock,
    color: '#f59e0b',
    label: 'Recovery Assistance Needed',
  },
  'Requires recovery assistance': {
    badge: 'recovery-assistance',
    icon: Clock,
    color: '#f59e0b',
    label: 'Recovery Assistance Needed',
  },
  'Severely/Persistently Damaged': {
    badge: 'recovery-severe',
    icon: AlertTriangle,
    color: '#ef4444',
    label: 'Severely/Persistently Damaged',
  },
  'Severely / persistently damaged': {
    badge: 'recovery-severe',
    icon: AlertTriangle,
    color: '#ef4444',
    label: 'Severely/Persistently Damaged',
  },
  'Field Verification Required': {
    badge: 'recovery-verification',
    icon: HelpCircle,
    color: '#8b5cf6',
    label: 'Field Verification Required',
  },
  'Requires field verification': {
    badge: 'recovery-verification',
    icon: HelpCircle,
    color: '#8b5cf6',
    label: 'Field Verification Required',
  },
};

const PRIORITY_BADGES = {
  HIGH: {
    badge: 'prio-high',
    color: '#ef4444',
    icon: Flame,
    bg: 'rgba(239, 68, 68, 0.16)',
    border: 'rgba(239, 68, 68, 0.35)',
  },
  MEDIUM: {
    badge: 'prio-medium',
    color: '#f59e0b',
    icon: AlertTriangle,
    bg: 'rgba(245, 158, 11, 0.16)',
    border: 'rgba(245, 158, 11, 0.35)',
  },
  LOW: {
    badge: 'prio-low',
    color: '#10b981',
    icon: CheckCircle2,
    bg: 'rgba(16, 185, 129, 0.16)',
    border: 'rgba(16, 185, 129, 0.35)',
  },
};

const MONITORING_STATUS_CONFIG = {
  'Recovery On Track': {
    badge: 'mon-on-track',
    color: '#10b981',
    icon: CheckCircle2,
    bg: 'rgba(16, 185, 129, 0.14)',
    border: 'rgba(16, 185, 129, 0.4)',
    label: 'Recovery On Track',
  },
  'Recovery Lagging': {
    badge: 'mon-lagging',
    color: '#f59e0b',
    icon: Clock,
    bg: 'rgba(245, 158, 11, 0.14)',
    border: 'rgba(245, 158, 11, 0.4)',
    label: 'Recovery Lagging',
  },
  'Recovery Stalled': {
    badge: 'mon-stalled',
    color: '#ef4444',
    icon: Ban,
    bg: 'rgba(239, 68, 68, 0.14)',
    border: 'rgba(239, 68, 68, 0.4)',
    label: 'Recovery Stalled',
  },
  'Insufficient Data': {
    badge: 'mon-insufficient',
    color: '#8b5cf6',
    icon: HelpCircle,
    bg: 'rgba(139, 92, 246, 0.14)',
    border: 'rgba(139, 92, 246, 0.4)',
    label: 'Insufficient Data',
  },
};

const VERIFICATION_STATUS_CONFIG = {
  'VERIFIED RECOVERY': {
    badge: 'ver-verified',
    color: '#10b981',
    icon: BadgeCheck,
    bg: 'rgba(16, 185, 129, 0.14)',
    border: 'rgba(16, 185, 129, 0.4)',
    label: 'VERIFIED RECOVERY',
  },
  'PARTIAL / IMPROVING': {
    badge: 'ver-partial',
    color: '#f59e0b',
    icon: Clock,
    bg: 'rgba(245, 158, 11, 0.14)',
    border: 'rgba(245, 158, 11, 0.4)',
    label: 'PARTIAL / IMPROVING',
  },
  'NOT VERIFIED': {
    badge: 'ver-not-verified',
    color: '#ef4444',
    icon: Ban,
    bg: 'rgba(239, 68, 68, 0.14)',
    border: 'rgba(239, 68, 68, 0.4)',
    label: 'NOT VERIFIED',
  },
  'INSUFFICIENT DATA': {
    badge: 'ver-insufficient',
    color: '#8b5cf6',
    icon: HelpCircle,
    bg: 'rgba(139, 92, 246, 0.14)',
    border: 'rgba(139, 92, 246, 0.4)',
    label: 'INSUFFICIENT DATA',
  },
};

const BASE_UNIT_COSTS = {
  buildings: 3.5,
  roads: 3.0,
  drainage: 1.8,
  agriculture: 1.5,
  soil_land: 1.2,
  habitats: 0.6,
  water_wetlands: 0.3,
  vegetation: 0.2,
};

const SEVERITY_MULTIPLIERS = {
  Critical: 1.25,
  Severe: 1.1,
  Moderate: 1.0,
  Low: 0.75,
};

function formatLocation(loc) {
  if (!loc) return null;
  if (typeof loc === 'object') {
    if (loc.latitude != null && loc.longitude != null) {
      return `Lat ${Number(loc.latitude).toFixed(4)}°, Lon ${Number(loc.longitude).toFixed(4)}°`;
    }
    if (loc.lat != null && loc.lon != null) {
      return `Lat ${Number(loc.lat).toFixed(4)}°, Lon ${Number(loc.lon).toFixed(4)}°`;
    }
    return null;
  }
  return String(loc);
}

export default function DamageAssessmentPanel({
  damageAssessment,
  recoveryRecommendations,
  recoveryPriorities,
  resourceOptimization,
  recoveryMonitoring,
  recoveryDiagnosis,
  recoveryVerification,
  sessionId,
  onSelectFeature,
  onNavigateToTab,
}) {
  const [activeView, setActiveView] = useState('verification'); // 'verification' | 'diagnosis' | 'monitoring' | 'optimization' | 'priorities' | 'sectors'
  const [filterType, setFilterType] = useState('all');
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);

  // Simulation Parameters for Part 4
  const [budgetLakhs, setBudgetLakhs] = useState(10.0);
  const [maxCapacity, setMaxCapacity] = useState(5);
  const [allowNaturalRecovery, setAllowNaturalRecovery] = useState(false);
  const [domainFilter, setDomainFilter] = useState('all');
  const [customOptimization, setCustomOptimization] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // Monitoring filter for Part 5
  const [monitoringFilter, setMonitoringFilter] = useState('all');

  // Diagnosis filter for Part 6
  const [diagnosisFilter, setDiagnosisFilter] = useState('all');

  // Verification filter for Part 7
  const [verificationFilter, setVerificationFilter] = useState('all');

  // Initialize or update optimization data
  useEffect(() => {
    if (resourceOptimization) {
      setCustomOptimization(resourceOptimization);
      if (resourceOptimization.summary?.total_budget_lakhs != null) {
        setBudgetLakhs(resourceOptimization.summary.total_budget_lakhs);
      }
      if (resourceOptimization.summary?.total_capacity_sites != null) {
        setMaxCapacity(resourceOptimization.summary.total_capacity_sites);
      }
    }
  }, [resourceOptimization]);

  const categories = damageAssessment?.categories || [];
  const summary = damageAssessment?.summary || {};
  const disclaimers = damageAssessment?.disclaimers || [];
  const region = damageAssessment?.region || null;

  // Build lookup maps
  const recommendationsMap = useMemo(() => {
    const map = {};
    if (recoveryRecommendations?.recommendations && Array.isArray(recoveryRecommendations.recommendations)) {
      recoveryRecommendations.recommendations.forEach((rec) => {
        if (rec && rec.category) {
          map[rec.category] = rec;
        }
      });
    }
    return map;
  }, [recoveryRecommendations]);

  const prioritiesMap = useMemo(() => {
    const map = {};
    if (recoveryPriorities?.priorities && Array.isArray(recoveryPriorities.priorities)) {
      recoveryPriorities.priorities.forEach((p) => {
        if (p && p.category) {
          map[p.category] = p;
        }
      });
    }
    return map;
  }, [recoveryPriorities]);

  const highPrioCount = recoveryPriorities?.high_priority_count ?? 0;
  const medPrioCount = recoveryPriorities?.medium_priority_count ?? 0;
  const lowPrioCount = recoveryPriorities?.low_priority_count ?? 0;

  // Filtered lists for Priority View & Sector View
  const sortedPriorities = recoveryPriorities?.priorities || [];
  const filteredPriorities = sortedPriorities.filter((p) => {
    if (filterType === 'high') return p?.priority_level === 'HIGH';
    if (filterType === 'medium') return p?.priority_level === 'MEDIUM';
    if (filterType === 'low') return p?.priority_level === 'LOW';
    if (filterType === 'environmental') return p?.category_type === 'environmental';
    if (filterType === 'infrastructure') return p?.category_type === 'infrastructure';
    return true;
  });

  const filteredCategories = categories.filter((cat) => {
    const p = prioritiesMap[cat?.category_id];
    if (filterType === 'high') return p?.priority_level === 'HIGH';
    if (filterType === 'medium') return p?.priority_level === 'MEDIUM';
    if (filterType === 'low') return p?.priority_level === 'LOW';
    if (filterType === 'environmental') return cat?.category_type === 'environmental';
    if (filterType === 'infrastructure') return cat?.category_type === 'infrastructure';
    return true;
  });

  // Pure deterministic client-side fallback simulation for Part 4
  const computedOptimization = useMemo(() => {
    if (!sortedPriorities || sortedPriorities.length === 0) return null;

    const budget = Math.max(0, parseFloat(budgetLakhs) || 10.0);
    const capacity = Math.max(1, parseInt(maxCapacity, 10) || 5);

    const candidates = sortedPriorities.map((p) => {
      const catId = p.category;
      const severity = p.damage_severity || 'Moderate';
      const baseCost = BASE_UNIT_COSTS[catId] || 1.0;
      const mult = SEVERITY_MULTIPLIERS[severity] || 1.0;
      const estCost = parseFloat((baseCost * mult).toFixed(2));
      const prioScore = parseFloat(p.priority_score) || 0.0;
      const bonus = p.priority_level === 'HIGH' ? 15.0 : p.priority_level === 'MEDIUM' ? 5.0 : 0.0;
      const benefit = parseFloat((prioScore * 10.0 + bonus).toFixed(1));
      return {
        ...p,
        estimated_cost_lakhs: estCost,
        expected_benefit_score: benefit,
        cost_ratio: benefit / Math.max(0.1, estCost),
      };
    });

    candidates.sort((a, b) => a.priority_rank - b.priority_rank);

    const selected = [];
    const unselected = [];
    let remBudget = budget;
    let usedCapacity = 0;

    for (const item of candidates) {
      const catId = item.category;
      const catName = item.category_name;
      const catType = item.category_type;
      const rank = item.priority_rank;
      const score = item.priority_score;
      const level = item.priority_level;
      const cost = item.estimated_cost_lakhs;
      const benefit = item.expected_benefit_score;
      const effort = item.estimated_effort_level || 'Moderate';
      const domain = item.target_resource_domain || 'Public Works';
      const action = item.recommended_action || 'Monitoring';
      const loc = item.location;
      const natLikelihood = item.natural_recovery_likelihood || 'Low';

      // Domain filter
      if (domainFilter && domainFilter !== 'all') {
        if (!domain.toLowerCase().includes(domainFilter.toLowerCase())) {
          unselected.push({
            category: catId,
            category_name: catName,
            category_type: catType,
            priority_rank: rank,
            priority_score: score,
            priority_level: level,
            estimated_cost_lakhs: cost,
            reason_deferred: `Domain Filter: Resource domain '${domain}' does not match active filter '${domainFilter}'.`,
            recommended_action: action,
          });
          continue;
        }
      }

      // Natural recovery deferral
      const isHighNatural = natLikelihood === 'High' || action.toLowerCase().includes('natural') || action.toLowerCase().includes('passive');
      if (isHighNatural && !allowNaturalRecovery) {
        unselected.push({
          category: catId,
          category_name: catName,
          category_type: catType,
          priority_rank: rank,
          priority_score: score,
          priority_level: level,
          estimated_cost_lakhs: cost,
          reason_deferred: `Natural Recovery Deferral: ${catName} exhibits High natural ecological resilience. Active funds (₹${cost.toFixed(2)}L) deferred to preserve recovery budget for critical infrastructure.`,
          recommended_action: action,
        });
        continue;
      }

      // Capacity constraint
      if (usedCapacity >= capacity) {
        unselected.push({
          category: catId,
          category_name: catName,
          category_type: catType,
          priority_rank: rank,
          priority_score: score,
          priority_level: level,
          estimated_cost_lakhs: cost,
          reason_deferred: `Capacity Limit: Maximum simultaneous intervention capacity (${capacity} sites) reached.`,
          recommended_action: action,
        });
        continue;
      }

      // Budget constraint
      if (cost > remBudget) {
        unselected.push({
          category: catId,
          category_name: catName,
          category_type: catType,
          priority_rank: rank,
          priority_score: score,
          priority_level: level,
          estimated_cost_lakhs: cost,
          reason_deferred: `Budget Limit: Estimated cost (₹${cost.toFixed(2)}L) exceeds remaining available allocation (₹${remBudget.toFixed(2)}L).`,
          recommended_action: action,
        });
        continue;
      }

      // Allocate
      remBudget = parseFloat((remBudget - cost).toFixed(2));
      usedCapacity += 1;

      selected.push({
        category: catId,
        category_name: catName,
        category_type: catType,
        location: loc,
        priority_rank: rank,
        priority_score: score,
        priority_level: level,
        estimated_cost_lakhs: cost,
        allocated_budget_lakhs: cost,
        estimated_effort_level: effort,
        expected_benefit_score: benefit,
        recommended_action: action,
        target_resource_domain: domain,
        allocation_reason: `Funded at ₹${cost.toFixed(2)}L (${effort} effort) due to Rank #${rank} ${level} priority (${score}/10) delivering +${benefit} benefit units in ${domain}.`,
      });
    }

    const allocatedTotal = parseFloat(selected.reduce((sum, s) => sum + s.allocated_budget_lakhs, 0).toFixed(2));
    const remFinal = parseFloat((budget - allocatedTotal).toFixed(2));
    const utilPct = budget > 0 ? parseFloat(((allocatedTotal / budget) * 100).toFixed(1)) : 0.0;
    const totalBenefit = parseFloat(selected.reduce((sum, s) => sum + s.expected_benefit_score, 0).toFixed(1));

    return {
      summary: {
        total_budget_lakhs: budget,
        allocated_budget_lakhs: allocatedTotal,
        remaining_budget_lakhs: remFinal,
        budget_utilization_pct: utilPct,
        total_capacity_sites: capacity,
        allocated_capacity_used: selected.length,
        remaining_capacity_sites: Math.max(0, capacity - selected.length),
        expected_total_benefit: totalBenefit,
        allocation_strategy: 'Multi-Criteria Knapsack with Natural Recovery Deferral',
      },
      selected_sites: selected,
      unselected_sites: unselected,
      allocation_notes: [
        `Simulated allocation across ${candidates.length} sectors under budget of ₹${budget.toFixed(2)} Lakhs and capacity of ${capacity} sites.`,
        `Selected ${selected.length} intervention sites utilizing ₹${allocatedTotal.toFixed(2)} Lakhs (${utilPct}% of budget).`,
        `Conserved ₹${remFinal.toFixed(2)} Lakhs in unallocated reserve capital.`,
      ],
      disclaimer: 'Resource allocation simulations, budget figures (₹ Lakhs), and capacity metrics are hypothetical decision-support estimates for multi-criteria optimization. They do not represent official government financial allocations, commercial contract bids, or guaranteed costs.',
    };
  }, [sortedPriorities, budgetLakhs, maxCapacity, allowNaturalRecovery, domainFilter]);

  const activeOptimization = customOptimization || computedOptimization;

  // Client-side fallback for Part 5 Recovery Monitoring
  const computedMonitoring = useMemo(() => {
    if (recoveryMonitoring && recoveryMonitoring.timelines) {
      return recoveryMonitoring;
    }

    // Default multi-temporal observation sequence
    const baseDate = region && region.toLowerCase().includes('nepal') ? '2026-07-28' : '2024-08-15';
    const dates = [baseDate, 'T+30d (1 Mo)', 'T+90d (3 Mo)', 'T+180d (6 Mo)'];

    const monConfigs = {
      vegetation: { indicator: 'Sentinel-2 NDVI', pre: 0.74, post: 0.28, vals: [0.28, 0.50, 0.65, 0.71], inverted: false, conf: 'High', field: false, notes: 'Fast natural vegetative canopy regrowth observed via multispectral near-infrared reflectance.' },
      agriculture: { indicator: 'Sentinel-2 SAVI', pre: 0.68, post: 0.18, vals: [0.18, 0.35, 0.52, 0.62], inverted: false, conf: 'High', field: false, notes: 'Cropland topsoil de-siltation and seasonal crop replanting observable in multi-temporal greenness.' },
      water_wetlands: { indicator: 'Sentinel-2 NDWI', pre: 0.32, post: 0.82, vals: [0.82, 0.52, 0.39, 0.34], inverted: true, conf: 'High', field: false, notes: 'Overland flood surge receding back to permanent riverbank and natural wetland retention boundaries.' },
      soil_land: { indicator: 'Sentinel-2 NDTI', pre: 0.14, post: 0.58, vals: [0.58, 0.42, 0.26, 0.17], inverted: true, conf: 'Moderate', field: false, notes: 'Lowland soil de-waterlogging and moisture stabilization progressing along drainage swales.' },
      habitats: { indicator: 'Riparian Buffer Coherence', pre: 0.82, post: 0.38, vals: [0.38, 0.46, 0.55, 0.64], inverted: false, conf: 'Moderate', field: true, notes: 'Riparian buffer regrowth is naturally slow; ground biodiversity survey required to verify fauna habitat recolonization.' },
      buildings: { indicator: 'Sentinel-1 SAR Backscatter σ°', pre: -5.4, post: -13.2, vals: [-13.2, -10.5, -7.6, -5.9], inverted: false, conf: 'High', field: true, notes: 'Ground-wall corner reflection returning as floodwaters drain and civil structural repairs progress.' },
      roads: { indicator: 'Corridor Clearance Index', pre: 0.92, post: 0.16, vals: [0.16, 0.56, 0.84, 0.90], inverted: false, conf: 'High', field: false, notes: 'Transport network cleared of flood debris and sub-base repaired along major lifeline arteries.' },
      drainage: { indicator: 'Canal Flow Capacity Index', pre: 0.88, post: 0.18, vals: [0.18, 0.48, 0.76, 0.85], inverted: false, conf: 'High', field: false, notes: 'Mechanized desilting of major stormwater canals restored gravity discharge capacity.' },
    };

    const timelines = categories.map((cat) => {
      const catId = cat.category_id;
      const cfg = monConfigs[catId] || { indicator: 'Multispectral Index', pre: 0.80, post: 0.25, vals: [0.25, 0.45, 0.65, 0.75], inverted: false, conf: 'Moderate', field: true, notes: 'Multispectral land surface reflection monitoring.' };
      
      const isFunded = activeOptimization?.selected_sites?.some((s) => s.category === catId) || false;
      const stages = ['Immediate Post-Flood', '1 Month Post-Flood', '3 Months Post-Flood', '6 Months Post-Flood'];
      
      const obs = cfg.vals.map((v, i) => {
        let pct = 0.0;
        if (cfg.inverted) {
          pct = ((cfg.post - v) / Math.max(0.01, Math.abs(cfg.post - cfg.pre))) * 100;
        } else {
          pct = ((v - cfg.post) / Math.max(0.01, Math.abs(cfg.pre - cfg.post))) * 100;
        }
        pct = Math.min(100.0, Math.max(0.0, parseFloat(pct.toFixed(1))));
        return {
          date: dates[i],
          timeline_stage: stages[i],
          indicator_name: cfg.indicator,
          value: v,
          baseline_value: cfg.pre,
          change_from_baseline: parseFloat((v - cfg.post).toFixed(2)),
          recovery_percentage: pct,
          interpretation: `Stage: ${stages[i]} — ${cfg.indicator} at ${v} (${pct}% progress toward pre-flood baseline).`,
        };
      });

      const latestPct = obs[obs.length - 1].recovery_percentage;
      let status = 'Recovery On Track';
      if (latestPct >= 65.0) status = 'Recovery On Track';
      else if (latestPct >= 25.0) status = 'Recovery Lagging';
      else status = 'Recovery Stalled';

      return {
        category: catId,
        category_name: cat.category_name,
        category_type: cat.category_type,
        location: cat.geographic_location,
        baseline_date: dates[0],
        latest_observation_date: dates[dates.length - 1],
        recovery_status: status,
        recovery_score: latestPct,
        latest_condition: `Recovery is ${status.toLowerCase()} with ${latestPct}% observable progress.`,
        primary_indicator_name: cfg.indicator,
        change_detected: true,
        confidence: cfg.conf,
        data_available: true,
        field_verification_required: cfg.field,
        funded_in_part4: isFunded,
        observations: obs,
        notes: cfg.notes,
      };
    });

    const onTrack = timelines.filter((t) => t.recovery_status === 'Recovery On Track').length;
    const lagging = timelines.filter((t) => t.recovery_status === 'Recovery Lagging').length;
    const stalled = timelines.filter((t) => t.recovery_status === 'Recovery Stalled').length;
    const avgScore = parseFloat((timelines.reduce((acc, t) => acc + t.recovery_score, 0) / Math.max(1, timelines.length)).toFixed(1));

    return {
      summary: {
        total_monitored_sectors: timelines.length,
        on_track_count: onTrack,
        lagging_count: lagging,
        stalled_count: stalled,
        insufficient_data_count: 0,
        average_recovery_score: avgScore,
        total_observations_recorded: timelines.length * 4,
        latest_observation_date: dates[dates.length - 1],
      },
      timelines,
      disclaimer: 'Satellite-derived recovery indicators reflect observable spectral indices (NDVI, NDWI, NDTI) and radar backscatter (SAR σ°) over time. They quantify visible land-surface and structural restoration trends but do not constitute comprehensive ground engineering or biological certifications without in-situ physical field verification.',
    };
  }, [recoveryMonitoring, categories, region, activeOptimization]);

  const activeMonitoring = computedMonitoring;

  // Filtered timelines for Part 5
  const filteredTimelines = useMemo(() => {
    if (!activeMonitoring?.timelines) return [];
    return activeMonitoring.timelines.filter((t) => {
      if (monitoringFilter === 'on_track') return t.recovery_status === 'Recovery On Track';
      if (monitoringFilter === 'lagging') return t.recovery_status === 'Recovery Lagging';
      if (monitoringFilter === 'stalled') return t.recovery_status === 'Recovery Stalled';
      if (monitoringFilter === 'environmental') return t.category_type === 'environmental';
      if (monitoringFilter === 'infrastructure') return t.category_type === 'infrastructure';
      return true;
    });
  }, [activeMonitoring, monitoringFilter]);

  // Client-side fallback / integration for Part 6 Recovery Stall Diagnosis
  const computedDiagnosis = useMemo(() => {
    if (recoveryDiagnosis && recoveryDiagnosis.diagnoses && recoveryDiagnosis.diagnoses.length > 0) {
      return recoveryDiagnosis;
    }

    if (!activeMonitoring?.timelines || activeMonitoring.timelines.length === 0) return null;

    const DIAGNOSTIC_MAP = {
      habitats: {
        stalled_causes: [
          { cause: 'Riparian Buffer Fragmentation & Slow Natural Succession', evidence: 'Evidence suggests riparian coherence index is lagging below baseline (0.64 vs. 0.82), indicating fragmented canopy recovery along riverbanks.', confidence: 'Moderate' },
          { cause: 'Possible In-Stream Siltation & Fauna Microhabitat Loss', evidence: 'Evidence suggests post-flood silt sedimentation along bank swales may impede rapid biological recolonization.', confidence: 'Requires Field Verification' },
        ],
        supporting_points: [
          'Multispectral riparian corridor coherence indicates slow natural vegetation succession.',
          'High slope and waterflow shear stress along riverbanks create persistent micro-erosion zones.',
        ],
        field_required: true,
        adaptive_rec: 'Conduct in-situ ground biodiversity survey, delineate protected riparian conservation buffers, and introduce native pioneer riverbank flora.',
      },
      buildings: {
        stalled_causes: [
          { cause: 'Infrastructure Restoration Not Detected / Persistent Structural Dampness', evidence: 'Evidence suggests Sentinel-1 SAR double-bounce backscatter σ° remains suppressed (-5.9 dB vs. -5.4 dB baseline), indicating unresolved masonry damage or moisture retention.', confidence: 'High' },
          { cause: 'Debris Accumulation / Subgrade Instability', evidence: 'Evidence suggests radar corner reflector signatures remain suppressed relative to pre-flood structural benchmarks.', confidence: 'Requires Field Verification' },
        ],
        supporting_points: [
          'Sentinel-1 SAR C-band double-bounce reflections have not returned to pre-event urban baseline.',
          'Persistent attenuation consistent with water-damaged masonry or unaddressed structural collapse.',
        ],
        field_required: true,
        adaptive_rec: 'Deploy civil engineering structural assessment team for building load testing, foundation integrity verification, and moisture mitigation.',
      },
      roads: {
        stalled_causes: [
          { cause: 'Transport Corridor Obstruction / Road Subgrade Degradation', evidence: 'Evidence suggests transport corridor optical clearance is below pre-flood baseline, indicating partial debris blockage or road surface erosion.', confidence: 'High' },
          { cause: 'Road Shoulder Scour / Culvert Washout', evidence: 'Evidence suggests localized washouts along roadside drainage shoulders prevent safe vehicle access.', confidence: 'Moderate' },
        ],
        supporting_points: [
          'Optical transport corridor clearance index indicates disrupted roadway continuity.',
          'Surface reflectance irregularities indicate uncompacted gravel or debris deposits.',
        ],
        field_required: false,
        adaptive_rec: 'Prioritize mechanized debris clearance, sub-base compaction testing, and culvert reinforcement along primary lifeline arteries.',
      },
      drainage: {
        stalled_causes: [
          { cause: 'Persistent Stormwater Canal Siltation & Drainage Bottlenecks', evidence: 'Evidence suggests channel flow capacity is restricted by heavy sediment accumulation in drainage canals.', confidence: 'High' },
          { cause: 'Culvert Debris Clogging & Gravity Outfall Restriction', evidence: 'Evidence suggests downstream drainage culverts and gravity outfalls remain partially obstructed.', confidence: 'Moderate' },
        ],
        supporting_points: [
          'Hydraulic flow capacity index remains significantly below pre-flood stormwater throughput baseline.',
          'Stagnant surface drainage observable along secondary feeder channels.',
        ],
        field_required: false,
        adaptive_rec: 'Execute mechanized desilting of major stormwater canals, clear culvert debris screens, and re-establish gravity discharge slope.',
      },
      vegetation: {
        stalled_causes: [
          { cause: 'Weak Vegetative Canopy Regrowth / Potential Soil Salinity or Nutrient Loss', evidence: 'Evidence suggests Sentinel-2 NDVI is lagging, indicating suppressed photosynthetic vigor in flooded lowlands.', confidence: 'High' },
          { cause: 'Topsoil Scouring & Root Inundation Stress', evidence: 'Evidence suggests prolonged root saturation delayed natural grass and shrub regeneration.', confidence: 'Moderate' },
        ],
        supporting_points: [
          'Near-infrared reflectance indicates slow biomass accumulation across inundation footprint.',
          'Photosynthetic index recovery trajectory remains below historical seasonal regrowth rates.',
        ],
        field_required: false,
        adaptive_rec: 'Deploy assisted native seedling replanting, hydroseeding with indigenous grasses, and conduct topsoil nutrient testing.',
      },
      agriculture: {
        stalled_causes: [
          { cause: 'Agricultural Recovery Below Baseline / Topsoil Silt Compaction', evidence: 'Evidence suggests Soil-Adjusted Vegetation Index (SAVI) indicates delayed crop replanting or dense silt crusting.', confidence: 'High' },
          { cause: 'Standing Furrow Inundation & Micro-Drainage Failure', evidence: 'Evidence suggests micro-topographic water retention in crop furrows preventing field machinery operation.', confidence: 'Moderate' },
        ],
        supporting_points: [
          'SAVI spectral trajectory shows subdued agricultural greenup compared to adjacent unflooded plots.',
          'Soil moisture reflectance indicates prolonged saturation in cultivated flatlands.',
        ],
        field_required: false,
        adaptive_rec: 'Initiate mechanical topsoil de-siltation, deep furrow aeration, and distribute soil bio-amendments before seasonal planting.',
      },
      water_wetlands: {
        stalled_causes: [
          { cause: 'Abnormal Overland Inundation / Delayed Natural Drainage', evidence: 'Evidence suggests Normalized Difference Water Index (NDWI) indicates residual flood extent in lowland depressions.', confidence: 'High' },
          { cause: 'Downstream Silt Berms Restricting Spillway Outflow', evidence: 'Evidence suggests flood-deposited silt ridges along natural spillways impede gravity drainage.', confidence: 'Moderate' },
        ],
        supporting_points: [
          'NDWI surface water index remains elevated above pre-flood wetland retention baseline.',
          'Water extent contraction has decelerated across shallow retention swales.',
        ],
        field_required: false,
        adaptive_rec: 'Survey natural wetland hydrological retention buffers and clear natural spillway discharge channels of obstructive debris.',
      },
      soil_land: {
        stalled_causes: [
          { cause: 'Continuing Subsoil Moisture Saturation & Surface Crusting', evidence: 'Evidence suggests NDTI moisture index indicates slow subsoil percolation.', confidence: 'Moderate' },
          { cause: 'Soil Compaction & Reduced Infiltration Capacity', evidence: 'Evidence suggests fine sediment deposition created impermeable topsoil crusting.', confidence: 'Moderate' },
        ],
        supporting_points: [
          'Normalized Difference Turbidity & Moisture Index (NDTI) indicates prolonged soil moisture retention.',
          'Surface texture roughness indicates unmitigated sediment deposits along drainage paths.',
        ],
        field_required: false,
        adaptive_rec: 'Install perimeter contour drainage trenches and bio-retention swales to accelerate subsoil de-watering.',
      },
    };

    const diagnoses = activeMonitoring.timelines.map((t) => {
      const catId = t.category;
      const cfg = DIAGNOSTIC_MAP[catId] || {
        stalled_causes: [{ cause: 'Unresolved Environmental Bottleneck', evidence: 'Evidence suggests slower than expected recovery trajectory.', confidence: 'Moderate' }],
        supporting_points: ['Multi-temporal indicators show subdued progress.'],
        field_required: true,
        adaptive_rec: 'Deploy field inspection team for ground verification.',
      };

      const stallDetected = (t.recovery_status === 'Recovery Lagging' || t.recovery_status === 'Recovery Stalled' || t.recovery_score < 65.0);
      const isSimulated = t.data_is_simulated ?? true;
      const latestObs = t.observations && t.observations.length > 0 ? t.observations[t.observations.length - 1] : null;

      let possibleCauses = [];
      let supportingEvidence = [];
      let adaptiveRec = '';
      let notes = '';

      if (t.recovery_status === 'Insufficient Data') {
        possibleCauses = [{
          cause: 'Insufficient Satellite Evidence / Cloud Obscuration',
          evidence: 'Evidence suggests cloud cover or lack of recent cloud-free acquisition precludes confirmation.',
          confidence: 'Low',
        }];
        supportingEvidence = ['Lack of cloud-free multispectral or calibrated SAR follow-up acquisitions.'];
        adaptiveRec = 'Acquire high-resolution optical/SAR follow-up imagery or schedule on-ground field inspection.';
        notes = 'Epistemic caveat: Classification indeterminate due to missing multi-temporal sensor observations.';
      } else if (stallDetected) {
        possibleCauses = cfg.stalled_causes;
        supportingEvidence = [
          ...cfg.supporting_points,
          `Observable recovery progress is ${t.recovery_score}% toward pre-flood baseline (${t.recovery_status}).`,
        ];
        adaptiveRec = cfg.adaptive_rec;
        const prefix = isSimulated ? 'Preliminary model indicator / Requires follow-up satellite acquisition or field verification: ' : 'Satellite-observed recovery diagnosis: ';
        notes = `${prefix}${t.category_name} classified as '${t.recovery_status}' at ${t.recovery_score}% recovery progress. Identified ${possibleCauses.length} plausible physical contributing factors backed by ${t.primary_indicator_name} data.`;
      } else {
        possibleCauses = [];
        supportingEvidence = [
          `Evidence suggests consistent positive trajectory: ${t.primary_indicator_name} reached ${t.recovery_score}% of pre-flood baseline.`,
          'No persistent waterlogging, structural collapse, or sediment blockage detected above critical thresholds.',
        ];
        adaptiveRec = 'Maintain routine satellite monitoring schedule and protect established recovery gains.';
        notes = `${t.category_name} is on track (${t.recovery_score}% progress). Observable trajectory aligns with expected recovery benchmarks.`;
      }

      return {
        category: catId,
        category_name: t.category_name,
        category_type: t.category_type,
        location: t.location,
        recovery_status: t.recovery_status,
        recovery_score: t.recovery_score,
        stall_detected: stallDetected,
        primary_indicator_name: t.primary_indicator_name,
        latest_observed_value: latestObs ? latestObs.value : null,
        baseline_value: latestObs ? latestObs.baseline_value : null,
        possible_causes: possibleCauses,
        supporting_evidence: supportingEvidence,
        confidence: stallDetected ? cfg.confidence || t.confidence : t.confidence,
        field_verification_required: stallDetected ? cfg.field_required || t.field_verification_required : t.field_verification_required,
        data_is_simulated: isSimulated,
        updated_recommendation: adaptiveRec,
        notes: notes,
      };
    });

    const stalledCnt = diagnoses.filter((d) => d.recovery_status === 'Recovery Stalled').length;
    const laggingCnt = diagnoses.filter((d) => d.recovery_status === 'Recovery Lagging').length;
    const onTrackCnt = diagnoses.filter((d) => d.recovery_status === 'Recovery On Track').length;
    const fieldReqCnt = diagnoses.filter((d) => d.field_verification_required).length;

    return {
      session_id: sessionId,
      region: region,
      summary: {
        total_diagnosed_sectors: diagnoses.length,
        stalled_count: stalledCnt,
        lagging_count: laggingCnt,
        on_track_count: onTrackCnt,
        insufficient_data_count: 0,
        stalled_or_lagging_count: stalledCnt + laggingCnt,
        requires_field_verification_count: fieldReqCnt,
      },
      diagnoses,
      disclaimer: 'Recovery failure and stall diagnoses are automated decision-support hypotheses inferred from satellite spectral indices (NDVI, NDWI, NDTI), radar backscatter (SAR σ°), and GIS terrain overlays. They highlight potential environmental and infrastructural bottlenecks but do NOT replace in-situ civil engineering inspections, biological surveys, or official field investigations.',
    };
  }, [recoveryDiagnosis, activeMonitoring, sessionId, region]);

  const activeDiagnosis = computedDiagnosis;

  // Filtered diagnoses for Part 6
  const filteredDiagnoses = useMemo(() => {
    if (!activeDiagnosis?.diagnoses) return [];
    return activeDiagnosis.diagnoses.filter((d) => {
      if (diagnosisFilter === 'stalled_only') return d.recovery_status === 'Recovery Stalled';
      if (diagnosisFilter === 'lagging_only') return d.recovery_status === 'Recovery Lagging';
      if (diagnosisFilter === 'issues_only') return d.stall_detected;
      if (diagnosisFilter === 'on_track') return d.recovery_status === 'Recovery On Track';
      if (diagnosisFilter === 'environmental') return d.category_type === 'environmental';
      if (diagnosisFilter === 'infrastructure') return d.category_type === 'infrastructure';
      return true;
    });
  }, [activeDiagnosis, diagnosisFilter]);

  // Client-side fallback / integration for Part 7 Recovery Verification
  const computedVerification = useMemo(() => {
    if (recoveryVerification && recoveryVerification.verifications && recoveryVerification.verifications.length > 0) {
      return recoveryVerification;
    }

    if (!activeMonitoring?.timelines || activeMonitoring.timelines.length === 0) return null;

    const DOMAIN_VERIFICATION_CONFIG = {
      vegetation: { target: 0.74, direction: 'Increasing (Toward Pre-Flood Baseline)' },
      agriculture: { target: 0.68, direction: 'Increasing (Toward Pre-Flood Baseline)' },
      water_wetlands: { target: 0.32, direction: 'Decreasing (Receding Toward Normal)' },
      soil_land: { target: 0.14, direction: 'Decreasing (Receding Toward Normal)' },
      habitats: { target: 0.82, direction: 'Increasing (Toward Pre-Flood Baseline)' },
      buildings: { target: -5.4, direction: 'Increasing (Toward Pre-Flood Baseline)' },
      roads: { target: 0.92, direction: 'Increasing (Toward Pre-Flood Baseline)' },
      drainage: { target: 0.88, direction: 'Increasing (Toward Pre-Flood Baseline)' },
    };

    const verifications = activeMonitoring.timelines.map((t) => {
      const catId = t.category;
      const cfg = DOMAIN_VERIFICATION_CONFIG[catId] || { target: 0.80, direction: 'Increasing (Toward Pre-Flood Baseline)' };
      const isSimulated = t.data_is_simulated ?? true;
      const rec = recommendationsMap[catId];
      const isFunded = activeOptimization?.selected_sites?.some((s) => s.category === catId) || false;
      const diag = activeDiagnosis?.diagnoses?.find((d) => d.category === catId);

      const latestObs = t.observations && t.observations.length > 0 ? t.observations[t.observations.length - 1] : null;
      const firstObs = t.observations && t.observations.length > 0 ? t.observations[0] : null;

      const baselineVal = firstObs ? firstObs.value : (t.baseline_value ?? 0.0);
      const latestVal = latestObs ? latestObs.value : baselineVal;
      const progress = t.recovery_score ?? 0.0;
      const measuredChange = parseFloat((latestVal - baselineVal).toFixed(2));

      // Build resource allocation description
      let resourceStatus = 'Not Allocated';
      let allocatedAmount = null;
      if (isFunded) {
        const fundedSite = activeOptimization?.selected_sites?.find((s) => s.category === catId);
        allocatedAmount = fundedSite?.allocated_budget_lakhs ?? 0.0;
        resourceStatus = `Funded ₹${allocatedAmount.toFixed(2)}L (${fundedSite?.estimated_effort_level || 'Moderate'} effort)`;
      } else {
        const defSite = activeOptimization?.unselected_sites?.find((s) => s.category === catId);
        resourceStatus = defSite?.reason_deferred || 'Deferred in Resource Optimization';
      }

      // Verification classification - Strict Epistemic Integrity
      let status = 'INSUFFICIENT DATA';
      let improved = false;
      let notes = '';
      let fieldRequired = t.field_verification_required;

      if (isSimulated) {
        status = 'INSUFFICIENT DATA';
        improved = progress > 0.0;
        notes = `Modeled projection indicates ${progress}% projected progress under simulated timeline. Epistemic Standard: Simulated/modeled trajectories cannot be certified as verified recovery without empirical post-flood satellite rasters or in-situ ground inspection.`;
      } else {
        if (progress >= 80.0) {
          status = 'VERIFIED RECOVERY';
          improved = true;
          notes = `Empirical multi-temporal satellite observations confirm ${progress}% recovery toward pre-flood baseline. Primary indicator ${t.primary_indicator_name} shows robust physical restoration.`;
        } else if (progress >= 25.0) {
          status = 'PARTIAL / IMPROVING';
          improved = true;
          notes = `Empirical satellite data demonstrates positive recovery trajectory (${progress}% progress), but values remain below the 80% restoration threshold. Ongoing monitoring recommended.`;
        } else {
          status = 'NOT VERIFIED';
          improved = false;
          notes = `Empirical observations indicate recovery is stagnant or deteriorated (${progress}% progress). Bottlenecks detected in recovery pathway.`;
        }
      }

      // Physical Evidence text
      const evidence = `Baseline: ${baselineVal} → Latest Observed: ${latestVal} (Target: ${cfg.target}). Measured change: ${measuredChange > 0 ? '+' : ''}${measuredChange} in ${t.primary_indicator_name} (${cfg.direction}).`;

      return {
        category: catId,
        category_name: t.category_name,
        category_type: t.category_type,
        location: t.location,
        recommended_action: rec?.recommended_action || 'Monitoring & restoration',
        resource_allocation_status: resourceStatus,
        allocated_budget_lakhs: allocatedAmount,
        primary_indicator_name: t.primary_indicator_name,
        baseline_value: baselineVal,
        latest_observed_value: latestVal,
        target_baseline_value: cfg.target,
        measured_change: measuredChange,
        observable_recovery_percentage: progress,
        expected_direction: cfg.direction,
        indicators_improved_as_expected: improved,
        verification_status: status,
        physical_evidence: evidence,
        verification_notes: notes,
        field_verification_required: fieldRequired,
        data_is_simulated: isSimulated,
        recovery_diagnosis_status: diag?.recovery_status || t.recovery_status,
      };
    });

    const verifiedCnt = verifications.filter((v) => v.verification_status === 'VERIFIED RECOVERY').length;
    const partialCnt = verifications.filter((v) => v.verification_status === 'PARTIAL / IMPROVING').length;
    const notVerCnt = verifications.filter((v) => v.verification_status === 'NOT VERIFIED').length;
    const insuffCnt = verifications.filter((v) => v.verification_status === 'INSUFFICIENT DATA').length;
    const fieldReqCnt = verifications.filter((v) => v.field_verification_required).length;

    return {
      session_id: sessionId,
      region: region,
      summary: {
        total_verified_sectors: verifications.length,
        verified_recovery_count: verifiedCnt,
        partial_improving_count: partialCnt,
        not_verified_count: notVerCnt,
        insufficient_data_count: insuffCnt,
        requires_field_verification_count: fieldReqCnt,
        simulated_data_warning: verifications.some((v) => v.data_is_simulated),
      },
      verifications,
      disclaimer: 'Recovery verification rigorously evaluates whether recommended and funded interventions produced measurable improvements. Epistemic Standard: When multi-temporal data relies on simulated/modeled projections, it is classified as INSUFFICIENT DATA and MUST NOT be presented as real-world recovery proof. Empirical multi-spectral/SAR rasters and in-situ field engineering inspections are required for full verification.',
    };
  }, [recoveryVerification, activeMonitoring, activeDiagnosis, activeOptimization, recommendationsMap, sessionId, region]);

  const activeVerification = computedVerification;

  // Filtered verifications for Part 7
  const filteredVerifications = useMemo(() => {
    if (!activeVerification?.verifications) return [];
    return activeVerification.verifications.filter((v) => {
      if (verificationFilter === 'verified_only') return v.verification_status === 'VERIFIED RECOVERY';
      if (verificationFilter === 'partial_only') return v.verification_status === 'PARTIAL / IMPROVING';
      if (verificationFilter === 'not_verified_only') return v.verification_status === 'NOT VERIFIED';
      if (verificationFilter === 'insufficient_only') return v.verification_status === 'INSUFFICIENT DATA';
      if (verificationFilter === 'environmental') return v.category_type === 'environmental';
      if (verificationFilter === 'infrastructure') return v.category_type === 'infrastructure';
      return true;
    });
  }, [activeVerification, verificationFilter]);

  // Handle server-side optimization trigger
  const handleRunBackendOptimization = async () => {
    if (!sessionId) return;
    setIsSimulating(true);
    try {
      const res = await optimizeResources(
        sessionId,
        budgetLakhs,
        maxCapacity,
        allowNaturalRecovery,
        domainFilter === 'all' ? null : domainFilter
      );
      if (res && res.summary) {
        setCustomOptimization(res);
      }
    } catch (err) {
      console.warn('Backend optimization call failed, using client model:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const optSummary = activeOptimization?.summary || {};
  const selectedSites = activeOptimization?.selected_sites || [];
  const unselectedSites = activeOptimization?.unselected_sites || [];
  const monSummary = activeMonitoring?.summary || {};
  const diagSummary = activeDiagnosis?.summary || {};
  const verSummary = activeVerification?.summary || {};

  if (!damageAssessment || !damageAssessment.categories || damageAssessment.categories.length === 0) {
    return (
      <div className="empty-state-card card">
        <ClipboardCheck size={32} color="#38bdf8" className="empty-icon" />
        <h3>No Damage & Priority Assessment Data</h3>
        <p>Run full flood analysis to generate damage metrics, sustainable recovery actions, priority rankings, and multi-temporal recovery monitoring.</p>
        <button
          className="btn-primary"
          style={{ width: 'auto', marginTop: 12 }}
          onClick={() => onNavigateToTab && onNavigateToTab('upload')}
        >
          Go to Data Upload →
        </button>
      </div>
    );
  }

  return (
    <div className="damage-assessment-panel">
      {/* Header Banner */}
      <div className="card damage-header-card">
        <div className="damage-header-top">
          <div className="damage-title-group">
            <div className="damage-badge-pill">
              <Shield size={13} color="#38bdf8" />
              <span>Sustainability Extension • Parts 1 to 7</span>
            </div>
            <h2 className="damage-main-title">
              Post-Flood Damage Assessment, Sustainable Recovery & Empirical Verification Engine
            </h2>
            <p className="damage-subtitle">
              Complete multi-stage pipeline connecting flood impact, nature-based recommendations, multi-criteria resource optimization, multi-temporal satellite monitoring, stall diagnosis, and rigorous empirical recovery verification.
            </p>
          </div>
        </div>

        {/* Top KPI Metrics Grid */}
        <div className="damage-kpi-grid">
          <div className="damage-kpi-card">
            <span className="kpi-label">Verified Recovery</span>
            <div className="kpi-value-row">
              <span className="kpi-val highlight-green">{verSummary.verified_recovery_count ?? 0}</span>
              <span className="kpi-denom">/ {categories.length} sectors</span>
            </div>
            <span className="kpi-sub">≥80% empirical restoration</span>
          </div>

          <div className="damage-kpi-card">
            <span className="kpi-label">Partial / Improving</span>
            <div className="kpi-value-row">
              <span className="kpi-val highlight-amber">{verSummary.partial_improving_count ?? 0}</span>
              <span className="kpi-denom">/ {categories.length} sectors</span>
            </div>
            <span className="kpi-sub">25%–79% measured progress</span>
          </div>

          <div className="damage-kpi-card">
            <span className="kpi-label">Not Verified / Stalled</span>
            <div className="kpi-value-row">
              <span className="kpi-val highlight-rose">{verSummary.not_verified_count ?? 0}</span>
              <span className="kpi-denom">/ {categories.length} sectors</span>
            </div>
            <span className="kpi-sub">&lt;25% progress / stalled</span>
          </div>

          <div className="damage-kpi-card">
            <span className="kpi-label">Insufficient / Modeled</span>
            <div className="kpi-value-row">
              <span className="kpi-val highlight-purple">
                {verSummary.insufficient_data_count ?? 0}
              </span>
              <span className="kpi-denom">/ {categories.length} sectors</span>
            </div>
            <span className="kpi-sub">
              {verSummary.simulated_data_warning ? 'Modeled / Needs Rasters' : 'Awaiting sensor pass'}
            </span>
          </div>
        </div>

        {/* Process Flow Banner */}
        <div className="damage-flow-banner">
          <div className="flow-step">
            <span className="flow-badge">1. DAMAGE</span>
            <span className="flow-desc">Spatial & Asset Impact</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step">
            <span className="flow-badge">2. RECOVERY</span>
            <span className="flow-desc">Natural vs. Assisted</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step">
            <span className="flow-badge">3. ACTION</span>
            <span className="flow-desc">Sustainable Practices</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step">
            <span className="flow-badge">4. PRIORITY</span>
            <span className="flow-desc">HIGH / MED / LOW</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step">
            <span className="flow-badge">5. OPTIMIZATION</span>
            <span className="flow-desc">Resource Allocation</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step">
            <span className="flow-badge">6. MONITORING</span>
            <span className="flow-desc">Satellite Timeline</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step">
            <span className="flow-badge">7. DIAGNOSIS</span>
            <span className="flow-desc">Failure & Stall Causes</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step active-flow-step">
            <span className="flow-badge">8. VERIFICATION</span>
            <span className="flow-desc">Empirical Proof</span>
          </div>
        </div>
      </div>

      {/* Primary Sub-Navigation Tabs */}
      <div className="damage-subnav-bar">
        <div className="subnav-toggle-group">
          <button
            className={`subnav-btn ${activeView === 'verification' ? 'active' : ''}`}
            onClick={() => setActiveView('verification')}
          >
            <BadgeCheck size={14} style={{ marginRight: 6 }} color="#10b981" />
            Recovery Verification (Part 7)
          </button>
          <button
            className={`subnav-btn ${activeView === 'diagnosis' ? 'active' : ''}`}
            onClick={() => setActiveView('diagnosis')}
          >
            <AlertTriangle size={14} style={{ marginRight: 6 }} color="#ef4444" />
            Stall & Failure Diagnosis (Part 6)
          </button>
          <button
            className={`subnav-btn ${activeView === 'monitoring' ? 'active' : ''}`}
            onClick={() => setActiveView('monitoring')}
          >
            <Activity size={14} style={{ marginRight: 6 }} />
            Recovery Timeline & Monitoring (Part 5)
          </button>
          <button
            className={`subnav-btn ${activeView === 'optimization' ? 'active' : ''}`}
            onClick={() => setActiveView('optimization')}
          >
            <Coins size={14} style={{ marginRight: 6 }} />
            Resource / Budget Optimizer (Part 4)
          </button>
          <button
            className={`subnav-btn ${activeView === 'priorities' ? 'active' : ''}`}
            onClick={() => setActiveView('priorities')}
          >
            <Award size={14} style={{ marginRight: 6 }} />
            Priority Ranking Engine ({sortedPriorities.length})
          </button>
          <button
            className={`subnav-btn ${activeView === 'sectors' ? 'active' : ''}`}
            onClick={() => setActiveView('sectors')}
          >
            <SlidersHorizontal size={14} style={{ marginRight: 6 }} />
            Detailed Sector Assessments & Actions ({categories.length})
          </button>
        </div>
      </div>

      {/* VIEW 00: RECOVERY VERIFICATION (PART 7) */}
      {activeView === 'verification' && (
        <div className="recovery-verification-view">
          {/* Filter Chips Bar */}
          <div className="damage-filter-bar" style={{ marginTop: 0 }}>
            <div className="filter-tab-buttons">
              <button
                className={`filter-btn ${verificationFilter === 'all' ? 'active' : ''}`}
                onClick={() => setVerificationFilter('all')}
              >
                All Sectors ({activeVerification?.verifications?.length || 0})
              </button>
              <button
                className={`filter-btn ${verificationFilter === 'verified_only' ? 'active' : ''}`}
                onClick={() => setVerificationFilter('verified_only')}
              >
                Verified Recovery ({verSummary.verified_recovery_count || 0})
              </button>
              <button
                className={`filter-btn ${verificationFilter === 'partial_only' ? 'active' : ''}`}
                onClick={() => setVerificationFilter('partial_only')}
              >
                Partial / Improving ({verSummary.partial_improving_count || 0})
              </button>
              <button
                className={`filter-btn ${verificationFilter === 'not_verified_only' ? 'active' : ''}`}
                onClick={() => setVerificationFilter('not_verified_only')}
              >
                Not Verified ({verSummary.not_verified_count || 0})
              </button>
              <button
                className={`filter-btn ${verificationFilter === 'insufficient_only' ? 'active' : ''}`}
                onClick={() => setVerificationFilter('insufficient_only')}
              >
                Insufficient / Modeled ({verSummary.insufficient_data_count || 0})
              </button>
              <button
                className={`filter-btn ${verificationFilter === 'infrastructure' ? 'active' : ''}`}
                onClick={() => setVerificationFilter('infrastructure')}
              >
                Infrastructure
              </button>
              <button
                className={`filter-btn ${verificationFilter === 'environmental' ? 'active' : ''}`}
                onClick={() => setVerificationFilter('environmental')}
              >
                Environmental
              </button>
            </div>
          </div>

          {/* Verification Cards List */}
          <div className="verification-cards-list">
            {filteredVerifications.map((item) => {
              const IconComponent = CATEGORY_ICONS[item.category] || Shield;
              const statusCfg = VERIFICATION_STATUS_CONFIG[item.verification_status] || VERIFICATION_STATUS_CONFIG['INSUFFICIENT DATA'] || {
                badge: 'ver-insufficient',
                color: '#8b5cf6',
                icon: HelpCircle,
                bg: 'rgba(139, 92, 246, 0.14)',
                border: 'rgba(139, 92, 246, 0.4)',
                label: 'INSUFFICIENT DATA',
              };
              const StatusIcon = statusCfg.icon || HelpCircle;
              const matchedCat = categories.find((c) => c && c.category_id === item.category);

              return (
                <div
                  key={item.category}
                  className={`verification-sector-card card ${item.verification_status === 'VERIFIED RECOVERY' ? 'is-verified' : item.verification_status === 'NOT VERIFIED' ? 'is-not-verified' : item.verification_status === 'PARTIAL / IMPROVING' ? 'is-partial' : 'is-insufficient'}`}
                  onClick={() => {
                    setSelectedCategoryId(item.category);
                    if (onSelectFeature && item.location) {
                      onSelectFeature({
                        type: item.category === 'buildings' ? 'building' : (item.category === 'roads' ? 'road' : 'damage'),
                        name: item.category_name,
                        data: item,
                      });
                    }
                  }}
                >
                  {/* Header: Title + Status Badge */}
                  <div className="ver-card-header">
                    <div className="ver-title-group">
                      <div className="ver-icon-wrapper">
                        <IconComponent size={22} color={statusCfg.color} />
                      </div>
                      <div>
                        <div className="ver-tag-row">
                          <h3 className="ver-card-title">{item.category_name}</h3>
                          <span className="sector-type-badge">
                            {item.category_type ? item.category_type.toUpperCase() : 'SECTOR'}
                          </span>
                          {item.data_is_simulated ? (
                            <span className="ver-sim-pill is-simulated">
                              Modeled Timeline Projection
                            </span>
                          ) : (
                            <span className="ver-sim-pill is-empirical">
                              Empirical Satellite Observation
                            </span>
                          )}
                        </div>
                        {item.location && formatLocation(item.location) && (
                          <span className="card-location">📍 {formatLocation(item.location)}</span>
                        )}
                      </div>
                    </div>

                    <div className="ver-status-pill-group">
                      <span
                        className="ver-status-badge"
                        style={{
                          backgroundColor: statusCfg.bg,
                          color: statusCfg.color,
                          border: `1px solid ${statusCfg.border}`,
                        }}
                      >
                        <StatusIcon size={14} style={{ marginRight: 5 }} />
                        {item.verification_status}
                      </span>
                      {item.field_verification_required && (
                        <span className="field-req-tag">
                          <FileSearch size={10} style={{ marginRight: 3 }} />
                          Field Inspection Required
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Data Provenance Banner */}
                  {item.data_is_simulated ? (
                    <div className="ver-provenance-banner is-simulated-banner">
                      <AlertTriangle size={15} color="#c4b5fd" style={{ flexShrink: 0, marginTop: 2 }} />
                      <div>
                        <b>Epistemic Integrity Standard:</b> This verification evaluation uses modeled multi-temporal projection data. Modeled trajectories cannot be certified as true recovery proof without empirical post-flood satellite rasters or in-situ ground inspection.
                      </div>
                    </div>
                  ) : (
                    <div className="ver-provenance-banner is-empirical-banner">
                      <CheckCircle2 size={15} color="#34d399" style={{ flexShrink: 0, marginTop: 2 }} />
                      <div>
                        <b>Empirical Verification Standard:</b> Evaluated against real satellite multi-temporal observations ({item.primary_indicator_name}).
                      </div>
                    </div>
                  )}

                  {/* 4-Card Context Grid: Damage -> Recommendation -> Resource Funding -> Diagnosis */}
                  <div className="ver-context-grid">
                    <div className="ver-context-card">
                      <div className="ver-context-lbl">1. WHAT WAS DAMAGED</div>
                      <div className="ver-context-val">
                        {matchedCat?.severity || 'Assessed'} Impact
                        <span className="ver-context-sub">
                          {matchedCat?.affected_count != null
                            ? `${matchedCat.affected_count} submerged assets`
                            : matchedCat?.affected_length_km != null
                            ? `${matchedCat.affected_length_km} km affected`
                            : `${matchedCat?.affected_area_km2 ?? 0} km² affected`}
                        </span>
                      </div>
                    </div>

                    <div className="ver-context-card">
                      <div className="ver-context-lbl">2. RECOMMENDED ACTION</div>
                      <div className="ver-context-val">
                        {item.recommended_action}
                      </div>
                    </div>

                    <div className="ver-context-card">
                      <div className="ver-context-lbl">3. RESOURCE ALLOCATION</div>
                      <div className="ver-context-val">
                        {item.resource_allocation_status}
                      </div>
                    </div>

                    <div className="ver-context-card">
                      <div className="ver-context-lbl">4. STALL DIAGNOSIS</div>
                      <div className="ver-context-val">
                        {item.recovery_diagnosis_status}
                      </div>
                    </div>
                  </div>

                  {/* Quantitative Indicator Measurement Strip */}
                  <div className="ver-metric-strip">
                    <div className="ver-metric-box">
                      <span className="lbl">Indicator</span>
                      <span className="val highlight-blue">{item.primary_indicator_name}</span>
                    </div>
                    <div className="ver-metric-box">
                      <span className="lbl">Pre-Flood Baseline</span>
                      <span className="val">{item.target_baseline_value}</span>
                    </div>
                    <div className="ver-metric-box">
                      <span className="lbl">Post-Flood Start</span>
                      <span className="val">{item.baseline_value}</span>
                    </div>
                    <div className="ver-metric-box">
                      <span className="lbl">Latest Observed</span>
                      <span className="val highlight-green">{item.latest_observed_value}</span>
                    </div>
                    <div className="ver-metric-box">
                      <span className="lbl">Progress Score</span>
                      <span className="val highlight-amber">{item.observable_recovery_percentage}%</span>
                    </div>
                    <div className="ver-metric-box">
                      <span className="lbl">Expected Direction</span>
                      <span className="val">{item.expected_direction}</span>
                    </div>
                  </div>

                  {/* Physical Evidence & Scientific Verification Notes */}
                  <div className="ver-evidence-box">
                    <div className="ver-evidence-header">
                      <FileCheck2 size={13} color="#38bdf8" />
                      <span>PHYSICAL EVIDENCE & VERIFICATION FINDING:</span>
                    </div>
                    <p className="ver-evidence-text">{item.physical_evidence}</p>
                    <div className="ver-notes-block">
                      <span className="ver-notes-lbl">EPISTEMIC VERIFICATION NOTES:</span>
                      <p className="ver-notes-text">{item.verification_notes}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW 0: RECOVERY STALL & FAILURE DIAGNOSIS (PART 6) */}
      {activeView === 'diagnosis' && (
        <div className="recovery-diagnosis-view">
          {/* Filter Chips Bar for Diagnosis */}
          <div className="damage-filter-bar" style={{ marginTop: 0 }}>
            <div className="filter-tab-buttons">
              <button
                className={`filter-btn ${diagnosisFilter === 'all' ? 'active' : ''}`}
                onClick={() => setDiagnosisFilter('all')}
              >
                All Sectors ({activeDiagnosis?.diagnoses?.length ?? 8})
              </button>
              <button
                className={`filter-btn ${diagnosisFilter === 'issues_only' ? 'active' : ''}`}
                onClick={() => setDiagnosisFilter('issues_only')}
              >
                <AlertTriangle size={13} color="#f59e0b" style={{ marginRight: 4 }} />
                Bottlenecks / Stalled ({diagSummary.stalled_or_lagging_count ?? 0})
              </button>
              <button
                className={`filter-btn ${diagnosisFilter === 'on_track' ? 'active' : ''}`}
                onClick={() => setDiagnosisFilter('on_track')}
              >
                <CheckCircle2 size={13} color="#10b981" style={{ marginRight: 4 }} />
                On Track ({diagSummary.on_track_count ?? 0})
              </button>
              <button
                className={`filter-btn ${diagnosisFilter === 'infrastructure' ? 'active' : ''}`}
                onClick={() => setDiagnosisFilter('infrastructure')}
              >
                Infrastructure
              </button>
              <button
                className={`filter-btn ${diagnosisFilter === 'environmental' ? 'active' : ''}`}
                onClick={() => setDiagnosisFilter('environmental')}
              >
                Environmental
              </button>
            </div>
          </div>

          {/* Diagnostic Cards List */}
          <div className="diagnosis-cards-list">
            {filteredDiagnoses.map((item) => {
              const IconComp = CATEGORY_ICONS[item.category] || Shield;
              const statusCfg = MONITORING_STATUS_CONFIG[item.recovery_status] || MONITORING_STATUS_CONFIG['Recovery On Track'];
              const StatusIcon = statusCfg.icon;
              const isLaggingOrStalled = item.stall_detected;

              return (
                <div
                  key={item.category}
                  className={`diagnosis-sector-card card ${isLaggingOrStalled ? 'has-bottleneck' : 'is-on-track'}`}
                  onClick={() => {
                    setSelectedCategoryId(item.category);
                    if (onSelectFeature && item.location) {
                      onSelectFeature({
                        type: item.category === 'buildings' ? 'building' : (item.category === 'roads' ? 'road' : 'damage'),
                        name: item.category_name,
                        data: item,
                      });
                    }
                  }}
                >
                  {/* Top Bar: Icon, Title, Sector Type, Status Badge */}
                  <div className="diag-card-header">
                    <div className="diag-title-group">
                      <div className="diag-icon-wrapper" style={{ borderColor: statusCfg.color }}>
                        <IconComp size={20} color={statusCfg.color} />
                      </div>
                      <div>
                        <div className="diag-tag-row">
                          <span className={`cat-sector-tag ${item.category_type}`}>
                            {item.category_type.toUpperCase()}
                          </span>
                          <span className="cat-confidence-tag">
                            Confidence: <b>{item.confidence}</b>
                          </span>
                          {item.field_verification_required && (
                            <span className="cat-verification-pill">
                              <FileSearch size={12} style={{ marginRight: 3 }} />
                              Field Verification Required
                            </span>
                          )}
                          <span className={`diag-sim-pill ${item.data_is_simulated ? 'is-simulated' : 'is-empirical'}`}>
                            {item.data_is_simulated ? 'Modeled Projection' : 'Empirical Satellite Observation'}
                          </span>
                        </div>
                        <h3 className="diag-card-title">{item.category_name}</h3>
                      </div>
                    </div>

                    <div className="diag-status-pill-group">
                      <span className={`diag-status-badge ${statusCfg.badge}`}>
                        <StatusIcon size={14} style={{ marginRight: 5 }} />
                        {statusCfg.label} ({(Number(item.recovery_score) || 0).toFixed(1)}%)
                      </span>
                    </div>
                  </div>

                  {/* Indicator Metric Callout Row */}
                  <div className="diag-metric-row">
                    <div className="diag-metric-col">
                      <span className="lbl">Monitored Sensor / Indicator:</span>
                      <span className="val highlight-blue">{item.primary_indicator_name}</span>
                    </div>
                    {item.latest_observed_value != null && (
                      <div className="diag-metric-col">
                        <span className="lbl">Latest Value vs Baseline:</span>
                        <span className="val">
                          <b>{item.latest_observed_value}</b> / baseline: <b>{item.baseline_value}</b>
                        </span>
                      </div>
                    )}
                    <div className="diag-metric-col">
                      <span className="lbl">Observed Progress:</span>
                      <span className={`val ${item.recovery_score >= 65 ? 'highlight-green' : item.recovery_score >= 25 ? 'highlight-amber' : 'highlight-rose'}`}>
                        {(Number(item.recovery_score) || 0).toFixed(1)}% toward baseline
                      </span>
                    </div>
                  </div>

                  {/* Stall Alert Banner or On-Track Banner */}
                  {isLaggingOrStalled ? (
                    <div className="diag-alert-banner">
                      <AlertOctagon size={16} color="#ef4444" style={{ flexShrink: 0, marginTop: 2 }} />
                      <div>
                        <b>RECOVERY BOTTLENECK / DELAY DETECTED:</b>
                        <span> {item.notes}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="diag-ontrack-banner">
                      <CheckCircle2 size={16} color="#10b981" style={{ flexShrink: 0, marginTop: 2 }} />
                      <div>
                        <b>TRAJECTORY ON TRACK:</b>
                        <span> {item.notes}</span>
                      </div>
                    </div>
                  )}

                  {/* Plausible Contributing Factors / Root Causes */}
                  {item.possible_causes && item.possible_causes.length > 0 && (
                    <div className="diag-causes-block">
                      <div className="diag-causes-header">
                        <Search size={14} color="#f59e0b" />
                        <span>EVIDENCE-BASED POTENTIAL CONTRIBUTING FACTORS:</span>
                      </div>
                      <div className="diag-causes-list">
                        {item.possible_causes.map((causeItem, cIdx) => (
                          <div key={cIdx} className="diag-cause-card">
                            <div className="cause-top-row">
                              <span className="cause-bullet">•</span>
                              <span className="cause-title">{causeItem.cause}</span>
                              <span className="cause-confidence-tag">Confidence: {causeItem.confidence}</span>
                            </div>
                            <p className="cause-evidence-text">{causeItem.evidence}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Supporting Observable Evidence List */}
                  {item.supporting_evidence && item.supporting_evidence.length > 0 && (
                    <div className="diag-evidence-block">
                      <div className="diag-evidence-header">
                        <FileText size={13} color="#38bdf8" />
                        <span>OBSERVABLE SATELLITE & GEOSPATIAL EVIDENCE:</span>
                      </div>
                      <ul className="diag-evidence-list">
                        {item.supporting_evidence.map((ev, eIdx) => (
                          <li key={eIdx}>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Adaptive Decision-Support Recommendation */}
                  <div className="diag-action-block">
                    <div className="diag-action-header">
                      <Sparkles size={14} color="#38bdf8" />
                      <span className="diag-action-lbl">ADAPTIVE DECISION-SUPPORT RECOMMENDATION:</span>
                    </div>
                    <p className="diag-action-text">{item.updated_recommendation}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW 0: RECOVERY TIMELINE & SATELLITE MONITORING (PART 5) */}
      {activeView === 'monitoring' && (
        <div className="recovery-monitoring-view">
          {/* Filter Chips Bar for Monitoring */}
          <div className="damage-filter-bar" style={{ marginTop: 0 }}>
            <div className="filter-tab-buttons">
              <button
                className={`filter-btn ${monitoringFilter === 'all' ? 'active' : ''}`}
                onClick={() => setMonitoringFilter('all')}
              >
                All Sectors ({activeMonitoring?.timelines?.length ?? 8})
              </button>
              <button
                className={`filter-btn ${monitoringFilter === 'on_track' ? 'active' : ''}`}
                onClick={() => setMonitoringFilter('on_track')}
              >
                On Track ({monSummary.on_track_count ?? 0})
              </button>
              <button
                className={`filter-btn ${monitoringFilter === 'lagging' ? 'active' : ''}`}
                onClick={() => setMonitoringFilter('lagging')}
              >
                Lagging ({monSummary.lagging_count ?? 0})
              </button>
              <button
                className={`filter-btn ${monitoringFilter === 'stalled' ? 'active' : ''}`}
                onClick={() => setMonitoringFilter('stalled')}
              >
                Stalled ({monSummary.stalled_count ?? 0})
              </button>
              <button
                className={`filter-btn ${monitoringFilter === 'environmental' ? 'active' : ''}`}
                onClick={() => setMonitoringFilter('environmental')}
              >
                Environmental
              </button>
              <button
                className={`filter-btn ${monitoringFilter === 'infrastructure' ? 'active' : ''}`}
                onClick={() => setMonitoringFilter('infrastructure')}
              >
                Infrastructure
              </button>
            </div>
          </div>

          {/* Sector Timelines List */}
          <div className="timeline-cards-list">
            {filteredTimelines.map((timeline) => {
              const IconComp = CATEGORY_ICONS[timeline.category] || Activity;
              const statusCfg = MONITORING_STATUS_CONFIG[timeline.recovery_status] || MONITORING_STATUS_CONFIG['Recovery On Track'];
              const StatusIcon = statusCfg.icon;
              const isSelected = selectedCategoryId === timeline.category;

              return (
                <div
                  key={timeline.category}
                  className={`timeline-sector-card card ${isSelected ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedCategoryId(timeline.category);
                    const catObj = categories.find((c) => c.category_id === timeline.category);
                    if (catObj?.geojson && onSelectFeature) {
                      onSelectFeature({
                        type: timeline.category === 'buildings' ? 'building' : (timeline.category === 'roads' ? 'road' : 'damage'),
                        name: timeline.category_name,
                        data: catObj,
                      });
                    }
                  }}
                >
                  {/* Top Header Row */}
                  <div className="timeline-card-header">
                    <div className="timeline-title-group">
                      <div className="cat-icon-wrapper" style={{ background: statusCfg.bg, borderColor: statusCfg.border }}>
                        <IconComp size={18} color={statusCfg.color} />
                      </div>
                      <div>
                        <div className="cat-type-row">
                          <span className={`cat-sector-tag ${timeline.category_type}`}>
                            {timeline.category_type ? timeline.category_type.toUpperCase() : 'SECTOR'}
                          </span>
                          <span className="domain-tag">
                            Confidence: <b>{timeline.confidence}</b>
                          </span>
                          {timeline.funded_in_part4 && (
                            <span className="prio-inline-badge prio-low">
                              ✓ Funded in Part 4
                            </span>
                          )}
                          {timeline.field_verification_required && (
                            <span className="prio-inline-badge recovery-verification">
                              Field Inspection Req.
                            </span>
                          )}
                        </div>
                        <h3 className="timeline-sector-title">{timeline.category_name}</h3>
                      </div>
                    </div>

                    <div className="timeline-status-group">
                      <div className="timeline-score-box">
                        <span className="timeline-score-lbl">RECOVERY SCORE</span>
                        <div className="timeline-score-val-row">
                          <span className="timeline-score-val" style={{ color: statusCfg.color }}>
                            {(Number(timeline.recovery_score) || 0).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <span className={`mon-status-badge ${statusCfg.badge}`}>
                        <StatusIcon size={12} style={{ marginRight: 4 }} />
                        {timeline.recovery_status ? timeline.recovery_status.toUpperCase() : 'ON TRACK'}
                      </span>
                    </div>
                  </div>

                  {/* Score Progress Bar */}
                  <div className="prio-progress-container">
                    <div
                      className="prio-progress-bar"
                      style={{
                        width: `${Math.min(100, timeline.recovery_score)}%`,
                        backgroundColor: statusCfg.color,
                      }}
                    />
                  </div>

                  {/* Primary Indicator strip */}
                  <div className="timeline-indicator-strip">
                    <div className="strip-item">
                      <Radio size={13} color="#38bdf8" />
                      <span className="strip-lbl">PRIMARY INDICATOR:</span>
                      <span className="strip-val">{timeline.primary_indicator_name}</span>
                    </div>
                  </div>

                  {/* Multi-Temporal Checkpoint Sequence Track */}
                  <div className="timeline-sequence-container">
                    <span className="sequence-title">
                      <Calendar size={13} color="#38bdf8" style={{ marginRight: 4 }} />
                      MULTI-TEMPORAL SATELLITE OBSERVATION SEQUENCE:
                    </span>

                    <div className="sequence-nodes-grid">
                      {timeline.observations.map((obs, idx) => (
                        <div key={idx} className="sequence-node-item">
                          <div className="node-stage-tag">{obs.timeline_stage}</div>
                          <div className="node-date">{obs.date}</div>
                          <div className="node-metric-row">
                            <span className="node-metric-val">{obs.value}</span>
                            <span className="node-metric-pct" style={{ color: obs.recovery_percentage >= 65 ? '#10b981' : (obs.recovery_percentage >= 25 ? '#f59e0b' : '#ef4444') }}>
                              {obs.recovery_percentage}%
                            </span>
                          </div>
                          <p className="node-interpretation">{obs.interpretation}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Notes & Observable Evidence */}
                  <div className="timeline-notes-box">
                    <span className="notes-lbl">OBSERVABLE SATELLITE EVIDENCE & TRAJECTORY:</span>
                    <p className="notes-text">{timeline.notes}</p>
                  </div>

                  {/* Card Footer */}
                  <div className="timeline-card-footer">
                    <span className="timeline-latest-badge">
                      Latest Status: <b>{timeline.latest_condition}</b>
                    </span>
                    {timeline.location && (
                      <button
                        className="btn-ghost-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedCategoryId(timeline.category);
                          const catObj = categories.find((c) => c.category_id === timeline.category);
                          if (catObj?.geojson && onSelectFeature) {
                            onSelectFeature({
                              type: timeline.category === 'buildings' ? 'building' : (timeline.category === 'roads' ? 'road' : 'damage'),
                              name: timeline.category_name,
                              data: catObj,
                            });
                          }
                          onNavigateToTab && onNavigateToTab('map');
                        }}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                      >
                        <Focus size={13} />
                        <span>Locate on Map</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW 1: RESOURCE / BUDGET OPTIMIZATION (PART 4) */}
      {activeView === 'optimization' && (
        <div className="resource-optimization-view">
          {/* Interactive Simulation Controls Card */}
          <div className="card opt-controls-card">
            <div className="opt-controls-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Scale size={18} color="#38bdf8" />
                <h3 className="opt-controls-title">Hypothetical Resource & Budget Simulation Constraints</h3>
              </div>
              <button
                className="btn-ghost-sm"
                onClick={handleRunBackendOptimization}
                disabled={isSimulating}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                <RefreshCw size={13} className={isSimulating ? 'spin-anim' : ''} />
                <span>{isSimulating ? 'Simulating...' : 'Recalculate Model'}</span>
              </button>
            </div>

            <div className="opt-controls-grid">
              {/* Control 1: Recovery Budget Slider & Input */}
              <div className="opt-control-item">
                <div className="control-label-row">
                  <label className="control-label">Available Recovery Budget</label>
                  <span className="control-value-badge">₹{Number(budgetLakhs).toFixed(1)} Lakhs</span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="40.0"
                  step="0.5"
                  value={budgetLakhs}
                  onChange={(e) => {
                    setBudgetLakhs(parseFloat(e.target.value));
                    setCustomOptimization(null);
                  }}
                  className="opt-slider"
                />
                <div className="slider-ticks">
                  <span>₹1L</span>
                  <span>₹10L</span>
                  <span>₹20L</span>
                  <span>₹30L</span>
                  <span>₹40L</span>
                </div>
              </div>

              {/* Control 2: Maximum Concurrent Site Interventions */}
              <div className="opt-control-item">
                <div className="control-label-row">
                  <label className="control-label">Workforce Capacity (Max Sites)</label>
                  <span className="control-value-badge">{maxCapacity} Sites</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="8"
                  step="1"
                  value={maxCapacity}
                  onChange={(e) => {
                    setMaxCapacity(parseInt(e.target.value, 10));
                    setCustomOptimization(null);
                  }}
                  className="opt-slider"
                />
                <div className="slider-ticks">
                  <span>1 Site</span>
                  <span>3 Sites</span>
                  <span>5 Sites</span>
                  <span>8 Sites</span>
                </div>
              </div>

              {/* Control 3: Target Resource Domain Filter */}
              <div className="opt-control-item">
                <div className="control-label-row">
                  <label className="control-label">Target Resource Domain</label>
                </div>
                <select
                  value={domainFilter}
                  onChange={(e) => {
                    setDomainFilter(e.target.value);
                    setCustomOptimization(null);
                  }}
                  className="opt-select"
                >
                  <option value="all">All Domains (Cross-Sector Multi-Criteria)</option>
                  <option value="Structural">Structural & Civil Engineering</option>
                  <option value="Transportation">Transportation & Highway Maintenance</option>
                  <option value="Drainage">Municipal Drainage & Public Works</option>
                  <option value="Agronomic">Agronomic & Soil Conditioning</option>
                  <option value="Stabilization">Land Stabilization & Bio-Engineering</option>
                  <option value="Ecological">Ecological Survey & Conservation</option>
                </select>
              </div>

              {/* Control 4: Natural Recovery Capital Toggle */}
              <div className="opt-control-item checkbox-item">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={allowNaturalRecovery}
                    onChange={(e) => {
                      setAllowNaturalRecovery(e.target.checked);
                      setCustomOptimization(null);
                    }}
                    className="opt-checkbox"
                  />
                  <span>Fund Natural Recovery Sectors (Override passive deferral)</span>
                </label>
                <span className="control-subtext">
                  Default preserves capital for zero-resilience civil infrastructure.
                </span>
              </div>
            </div>
          </div>

          {/* Allocation Outcome KPI Dashboard */}
          <div className="opt-kpi-summary-grid">
            <div className="damage-kpi-card">
              <span className="kpi-label">Allocated Capital</span>
              <div className="kpi-value-row">
                <span className="kpi-val highlight-green">₹{optSummary.allocated_budget_lakhs?.toFixed(2) ?? '0.00'}L</span>
                <span className="kpi-denom">/ ₹{optSummary.total_budget_lakhs?.toFixed(1) ?? '0.0'}L</span>
              </div>
              <div className="prio-progress-container" style={{ marginTop: 6 }}>
                <div
                  className="prio-progress-bar"
                  style={{
                    width: `${Math.min(100, optSummary.budget_utilization_pct || 0)}%`,
                    backgroundColor: '#10b981',
                  }}
                />
              </div>
              <span className="kpi-sub" style={{ marginTop: 4 }}>
                {optSummary.budget_utilization_pct?.toFixed(1) ?? 0}% Budget Utilized
              </span>
            </div>

            <div className="damage-kpi-card">
              <span className="kpi-label">Funded Interventions</span>
              <div className="kpi-value-row">
                <span className="kpi-val highlight-blue">{optSummary.allocated_capacity_used ?? 0}</span>
                <span className="kpi-denom">/ {optSummary.total_capacity_sites ?? 0} sites</span>
              </div>
              <span className="kpi-sub">
                {optSummary.remaining_capacity_sites ?? 0} site capacity remaining
              </span>
            </div>

            <div className="damage-kpi-card">
              <span className="kpi-label">Cumulative Benefit Score</span>
              <div className="kpi-value-row">
                <span className="kpi-val highlight-amber">+{optSummary.expected_total_benefit?.toFixed(1) ?? '0.0'}</span>
                <span className="kpi-denom">pts</span>
              </div>
              <span className="kpi-sub">Multi-criteria impact addressed</span>
            </div>

            <div className="damage-kpi-card">
              <span className="kpi-label">Conserved Reserve</span>
              <div className="kpi-value-row">
                <span className="kpi-val highlight-purple">₹{optSummary.remaining_budget_lakhs?.toFixed(2) ?? '0.00'}L</span>
              </div>
              <span className="kpi-sub">Emergency contingency balance</span>
            </div>
          </div>

          {/* Section: Funded Interventions */}
          <div className="opt-section-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <CheckCircle2 size={16} color="#10b981" />
              <h3 className="opt-section-title">
                Selected & Funded Interventions ({selectedSites.length})
              </h3>
            </div>
            <span className="opt-section-subtitle">
              Prioritized by multi-criteria benefit-cost efficiency within budget & capacity limits.
            </span>
          </div>

          <div className="opt-cards-list">
            {selectedSites.map((item) => {
              const IconComp = CATEGORY_ICONS[item.category] || Building2;
              const prioConfig = PRIORITY_BADGES[item.priority_level] || PRIORITY_BADGES.MEDIUM;
              const isSelected = selectedCategoryId === item.category;

              return (
                <div
                  key={item.category}
                  className={`opt-funded-card card ${isSelected ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedCategoryId(item.category);
                    const catObj = categories.find((c) => c.category_id === item.category);
                    if (catObj?.geojson && onSelectFeature) {
                      onSelectFeature({
                        type: item.category === 'buildings' ? 'building' : (item.category === 'roads' ? 'road' : 'damage'),
                        name: item.category_name,
                        data: catObj,
                      });
                    }
                  }}
                >
                  <div className="opt-card-top">
                    <div className="opt-card-left">
                      <div className="cat-icon-wrapper funded-icon">
                        <IconComp size={18} color="#10b981" />
                      </div>
                      <div>
                        <div className="cat-type-row">
                          <span className={`cat-sector-tag ${item.category_type}`}>
                            {item.category_type?.toUpperCase()}
                          </span>
                          <span className={`prio-inline-badge ${prioConfig.badge}`}>
                            #{item.priority_rank} {item.priority_level} ({Number(item.priority_score).toFixed(1)}/10)
                          </span>
                          <span className="domain-tag">
                            {item.target_resource_domain}
                          </span>
                        </div>
                        <h4 className="opt-card-title">{item.category_name}</h4>
                      </div>
                    </div>

                    <div className="opt-card-right">
                      <div className="funding-badge-box">
                        <span className="funding-lbl">ALLOCATED BUDGET</span>
                        <span className="funding-val">₹{Number(item.allocated_budget_lakhs).toFixed(2)} Lakhs</span>
                        <span className="effort-badge">{item.estimated_effort_level} Effort</span>
                      </div>
                    </div>
                  </div>

                  {/* Recommendation and Justification */}
                  <div className="opt-card-body">
                    <div className="opt-action-row">
                      <span className="action-lbl">RECOMMENDED ACTION:</span>
                      <span className="action-val">{item.recommended_action}</span>
                    </div>

                    <div className="opt-reason-row">
                      <TrendingUp size={14} color="#10b981" style={{ flexShrink: 0, marginTop: 2 }} />
                      <span className="reason-val">{item.allocation_reason}</span>
                    </div>
                  </div>

                  {/* Footer Actions */}
                  <div className="opt-card-footer">
                    <span className="benefit-pill">
                      Expected Benefit: <b>+{Number(item.expected_benefit_score).toFixed(1)} pts</b>
                    </span>
                    {item.location && (
                      <button
                        className="btn-ghost-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedCategoryId(item.category);
                          const catObj = categories.find((c) => c.category_id === item.category);
                          if (catObj?.geojson && onSelectFeature) {
                            onSelectFeature({
                              type: item.category === 'buildings' ? 'building' : (item.category === 'roads' ? 'road' : 'damage'),
                              name: item.category_name,
                              data: catObj,
                            });
                          }
                          onNavigateToTab && onNavigateToTab('map');
                        }}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                      >
                        <Focus size={13} />
                        <span>Locate on Map</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Section: Deferred / Unallocated Sectors */}
          {unselectedSites.length > 0 && (
            <>
              <div className="opt-section-header" style={{ marginTop: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Ban size={16} color="#94a3b8" />
                  <h3 className="opt-section-title" style={{ color: '#94a3b8' }}>
                    Deferred / Unallocated Sectors ({unselectedSites.length})
                  </h3>
                </div>
                <span className="opt-section-subtitle">
                  Sectors deferred due to budget ceilings, workforce limits, natural recovery resilience, or active filters.
                </span>
              </div>

              <div className="opt-cards-list">
                {unselectedSites.map((item) => {
                  const IconComp = CATEGORY_ICONS[item.category] || ClipboardCheck;
                  const prioConfig = PRIORITY_BADGES[item.priority_level] || PRIORITY_BADGES.LOW;

                  return (
                    <div key={item.category} className="opt-unfunded-card card">
                      <div className="opt-card-top">
                        <div className="opt-card-left">
                          <div className="cat-icon-wrapper unfunded-icon">
                            <IconComp size={18} color="#64748b" />
                          </div>
                          <div>
                            <div className="cat-type-row">
                              <span className={`cat-sector-tag ${item.category_type}`}>
                                {item.category_type?.toUpperCase()}
                              </span>
                              <span className={`prio-inline-badge ${prioConfig.badge}`}>
                                #{item.priority_rank} {item.priority_level} ({Number(item.priority_score).toFixed(1)}/10)
                              </span>
                            </div>
                            <h4 className="opt-card-title" style={{ color: '#cbd5e1' }}>{item.category_name}</h4>
                          </div>
                        </div>

                        <div className="opt-card-right">
                          <span className="unfunded-cost-tag">
                            Est. ₹{Number(item.estimated_cost_lakhs).toFixed(2)}L
                          </span>
                        </div>
                      </div>

                      <div className="opt-deferred-reason-box">
                        <span className="deferred-lbl">REASON DEFERRED:</span>
                        <p className="deferred-text">{item.reason_deferred}</p>
                      </div>

                      <div className="opt-unfunded-action">
                        <span className="action-lbl">BASELINE ACTION:</span>
                        <span className="action-val" style={{ color: '#94a3b8' }}>{item.recommended_action}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      )}

      {/* VIEW 2: RECOVERY PRIORITY RANKING ENGINE */}
      {activeView === 'priorities' && (
        <div className="damage-priorities-list">
          {filteredPriorities.map((item) => {
            const IconComp = CATEGORY_ICONS[item.category] || ClipboardCheck;
            const prioConfig = PRIORITY_BADGES[item.priority_level] || PRIORITY_BADGES.MEDIUM;
            const PrioIcon = prioConfig.icon;
            const isSelected = selectedCategoryId === item.category;

            return (
              <div
                key={item.category}
                className={`priority-sector-card card ${isSelected ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedCategoryId(item.category);
                  const catObj = categories.find((c) => c.category_id === item.category);
                  if (catObj?.geojson && onSelectFeature) {
                    onSelectFeature({
                      type: item.category === 'buildings' ? 'building' : (item.category === 'roads' ? 'road' : 'damage'),
                      name: item.category_name,
                      data: catObj,
                    });
                  }
                }}
              >
                {/* Header Row: Rank Badge, Title, Priority Score Gauge */}
                <div className="prio-card-header">
                  <div className="prio-title-group">
                    <div className="prio-rank-pill">
                      #{item.priority_rank}
                    </div>
                    <div className="cat-icon-wrapper">
                      <IconComp size={18} color="#38bdf8" />
                    </div>
                    <div>
                      <div className="cat-type-row">
                        <span className={`cat-sector-tag ${item.category_type}`}>
                          {item.category_type ? item.category_type.toUpperCase() : 'SECTOR'}
                        </span>
                        <span className="domain-tag">
                          {item.target_resource_domain}
                        </span>
                      </div>
                      <h3 className="cat-title">{item.category_name}</h3>
                    </div>
                  </div>

                  <div className="prio-score-group">
                    <div className="prio-score-box">
                      <span className="prio-score-label">PRIORITY SCORE</span>
                      <div className="prio-score-val-row">
                        <span className="prio-score-val" style={{ color: prioConfig.color }}>
                          {(Number(item.priority_score) || 0).toFixed(1)}
                        </span>
                        <span className="prio-score-max">/10</span>
                      </div>
                    </div>
                    <span className={`prio-level-badge ${prioConfig.badge}`}>
                      <PrioIcon size={12} style={{ marginRight: 4 }} />
                      {item.priority_level} PRIORITY
                    </span>
                  </div>
                </div>

                {/* Score Progress Bar */}
                <div className="prio-progress-container">
                  <div
                    className="prio-progress-bar"
                    style={{
                      width: `${Math.min(100, item.priority_score * 10)}%`,
                      backgroundColor: prioConfig.color,
                    }}
                  />
                </div>

                {/* Multi-Criteria Indicators Strip */}
                <div className="prio-indicators-row">
                  <div className="prio-indicator-item">
                    <span className="lbl">Damage Severity:</span>
                    <span className={`val ${SEVERITY_BADGES[item.damage_severity] || ''}`}>
                      {item.damage_severity}
                    </span>
                  </div>
                  <div className="prio-indicator-item">
                    <span className="lbl">Urgency:</span>
                    <span className="val highlight-amber">{item.urgency}</span>
                  </div>
                  <div className="prio-indicator-item">
                    <span className="lbl">Infrastructure:</span>
                    <span className="val">{item.infrastructure_importance}</span>
                  </div>
                  <div className="prio-indicator-item">
                    <span className="lbl">Natural Recovery:</span>
                    <span className="val highlight-green">{item.natural_recovery_likelihood}</span>
                  </div>
                  <div className="prio-indicator-item">
                    <span className="lbl">Est. Effort:</span>
                    <span className="val">{item.estimated_effort_level}</span>
                  </div>
                </div>

                {/* Plain-Language Justification (Why this priority level was assigned) */}
                <div className="prio-reason-box">
                  <span className="reason-lbl">PRIORITY JUSTIFICATION (WHY):</span>
                  <p className="reason-text">{item.reason}</p>
                </div>

                {/* Recommended Sustainable Action */}
                <div className="prio-action-box">
                  <div className="prio-action-header">
                    <Sparkles size={13} color="#38bdf8" />
                    <span className="prio-action-lbl">RECOMMENDED ACTION:</span>
                    <span className="prio-action-name">{item.recommended_action}</span>
                  </div>
                </div>

                {/* Contributing Factor Normalized Weights Breakdown */}
                {item.contributing_factors && (
                  <div className="prio-factors-grid">
                    <div className="factor-chip">
                      <span>Damage:</span>
                      <b>{item.contributing_factors.damage_severity_score}</b>
                    </div>
                    <div className="factor-chip">
                      <span>Infra:</span>
                      <b>{item.contributing_factors.infrastructure_importance_score}</b>
                    </div>
                    <div className="factor-chip">
                      <span>Pop:</span>
                      <b>{item.contributing_factors.population_impact_score}</b>
                    </div>
                    <div className="factor-chip">
                      <span>Eco:</span>
                      <b>{item.contributing_factors.ecological_importance_score}</b>
                    </div>
                    <div className="factor-chip">
                      <span>Urgency:</span>
                      <b>{item.contributing_factors.urgency_score}</b>
                    </div>
                    <div className="factor-chip">
                      <span>Nat. Mod:</span>
                      <b>{item.contributing_factors.natural_recovery_factor}x</b>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* VIEW 3: DETAILED SECTORS */}
      {activeView === 'sectors' && (
        <div className="damage-categories-list">
          {filteredCategories.map((cat) => {
            const IconComp = CATEGORY_ICONS[cat.category_id] || ClipboardCheck;
            const rec = recommendationsMap[cat.category_id];
            const prio = prioritiesMap[cat.category_id];
            const prioConfig = prio ? PRIORITY_BADGES[prio.priority_level] : null;

            const recClassification = rec?.recovery_classification || cat.recovery_classification || 'Likely Natural Recovery';
            const recConfig = RECOVERY_COLORS[recClassification] || RECOVERY_COLORS['Likely Natural Recovery'];
            const RecIcon = recConfig.icon;

            const isSelected = selectedCategoryId === cat.category_id;
            const recommendedAction = rec?.recommended_action || cat.recovery_notes || 'Routine Monitoring';
            const reasonText = rec?.reason || cat.damage_description || 'Assessed under multispectral baseline parameters.';
            const practices = rec?.sustainable_practices || [];
            const requiresField = rec?.requires_field_verification ?? (cat.confidence_level === 'Requires Field Verification');

            return (
              <div
                key={cat.category_id}
                className={`damage-category-card card ${isSelected ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedCategoryId(cat.category_id);
                  if (cat.geojson && onSelectFeature) {
                    onSelectFeature({
                      type: cat.category_id === 'buildings' ? 'building' : (cat.category_id === 'roads' ? 'road' : 'damage'),
                      name: cat.category_name,
                      data: cat,
                    });
                  }
                }}
              >
                {/* Top Row: Icon, Title, Sector Type, Severity & Recovery Badges */}
                <div className="cat-card-header">
                  <div className="cat-card-title-group">
                    <div className="cat-icon-wrapper">
                      <IconComp size={18} color="#38bdf8" />
                    </div>
                    <div>
                      <div className="cat-type-row">
                        <span className={`cat-sector-tag ${cat.category_type}`}>
                          {cat.category_type ? cat.category_type.toUpperCase() : 'SECTOR'}
                        </span>
                        <span className="cat-confidence-tag">
                          Confidence: <b>{cat.confidence_level}</b>
                        </span>
                        {prio && (
                          <span className={`prio-inline-badge ${prioConfig?.badge}`}>
                            #{prio.priority_rank} {prio.priority_level} ({(Number(prio.priority_score) || 0).toFixed(1)}/10)
                          </span>
                        )}
                      </div>
                      <h3 className="cat-title">{cat.category_name}</h3>
                    </div>
                  </div>

                  <div className="cat-badges-group">
                    <span className={`severity-badge ${SEVERITY_BADGES[cat.severity] || 'badge-moderate'}`}>
                      {cat.severity} Severity
                    </span>
                    <span className={`recovery-badge ${recConfig.badge}`}>
                      <RecIcon size={12} style={{ marginRight: 4 }} />
                      {recConfig.label}
                    </span>
                  </div>
                </div>

                {/* Quantitative Metric Callout */}
                <div className="cat-metric-banner">
                  {cat.affected_count != null && (
                    <div className="cat-metric-item">
                      <span className="metric-lbl">Submerged Assets:</span>
                      <span className="metric-val highlight-rose">{cat.affected_count} structures</span>
                    </div>
                  )}
                  {cat.affected_length_km != null && (
                    <div className="cat-metric-item">
                      <span className="metric-lbl">Inundated Length:</span>
                      <span className="metric-val highlight-amber">{cat.affected_length_km} km</span>
                    </div>
                  )}
                  {cat.affected_area_km2 != null && (
                    <div className="cat-metric-item">
                      <span className="metric-lbl">Affected Land Extent:</span>
                      <span className="metric-val highlight-blue">{cat.affected_area_km2} km²</span>
                    </div>
                  )}
                  {requiresField && (
                    <div className="cat-metric-item highlight-purple">
                      <FileSearch size={13} style={{ marginRight: 4 }} />
                      <span>Ground verification required</span>
                    </div>
                  )}
                </div>

                {/* Recommendation Callout Box */}
                <div className="cat-recommendation-box">
                  <div className="rec-box-header">
                    <Sparkles size={14} color="#38bdf8" />
                    <span className="rec-box-title">RECOMMENDED ACTION:</span>
                    <span className="rec-action-text">{recommendedAction}</span>
                  </div>

                  <div className="rec-reason-block">
                    <span className="reason-lbl">EVIDENCE-BASED REASON:</span>
                    <p className="reason-text">{reasonText}</p>
                  </div>

                  {practices.length > 0 && (
                    <div className="rec-practices-block">
                      <span className="practices-lbl">
                        <Leaf size={12} color="#10b981" style={{ marginRight: 4 }} />
                        SUSTAINABLE / NATURE-BASED PRACTICES:
                      </span>
                      <div className="practices-tags-row">
                        {practices.map((practice, idx) => (
                          <span key={idx} className="practice-tag">
                            {practice}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Epistemic Modesty & Decision-Support Disclaimer Card */}
      <div className="card damage-disclaimer-card">
        <div className="disclaimer-header">
          <Info size={16} color="#38bdf8" />
          <h4>Decision-Support & Epistemic Modesty Standards</h4>
        </div>
        <ul className="disclaimer-list">
          <li>Satellite-derived recovery indicators reflect observable spectral indices (NDVI, NDWI, NDTI) and radar backscatter (SAR $\sigma^\circ$) over time.</li>
          <li>They quantify visible land-surface and structural restoration trends but do not constitute comprehensive ground engineering or biological certifications without in-situ physical field verification.</li>
          <li><b>Part 7 Recovery Verification Integrity Standard:</b> Simulated and modeled timelines are explicitly marked as INSUFFICIENT DATA and cannot certify real-world recovery. Verified Recovery status requires empirical satellite observations (≥80% restoration) or in-situ ground inspection.</li>
          <li>Sectors with high natural recovery potential are monitored passively to avoid wasteful capital expenditure where natural ecological processes suffice.</li>
        </ul>
      </div>
    </div>
  );
}
