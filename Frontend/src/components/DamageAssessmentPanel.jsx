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
} from 'lucide-react';
import { optimizeResources } from '../services/api';

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

export default function DamageAssessmentPanel({
  damageAssessment,
  recoveryRecommendations,
  recoveryPriorities,
  resourceOptimization,
  sessionId,
  onSelectFeature,
  onNavigateToTab,
}) {
  const [activeView, setActiveView] = useState('optimization'); // 'optimization' | 'priorities' | 'sectors'
  const [filterType, setFilterType] = useState('all');
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);

  // Simulation Parameters for Part 4
  const [budgetLakhs, setBudgetLakhs] = useState(10.0);
  const [maxCapacity, setMaxCapacity] = useState(5);
  const [allowNaturalRecovery, setAllowNaturalRecovery] = useState(false);
  const [domainFilter, setDomainFilter] = useState('all');
  const [customOptimization, setCustomOptimization] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);

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

  if (!damageAssessment || !damageAssessment.categories) {
    return (
      <div className="empty-state-card card">
        <ClipboardCheck size={32} color="#38bdf8" className="empty-icon" />
        <h3>No Damage & Priority Assessment Data</h3>
        <p>Run full flood analysis to generate damage metrics, sustainable recovery actions, priority rankings, and budget optimization.</p>
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

  const { summary, categories, disclaimers } = damageAssessment;

  // Build lookup maps
  const recommendationsMap = {};
  if (recoveryRecommendations?.recommendations) {
    recoveryRecommendations.recommendations.forEach((rec) => {
      recommendationsMap[rec.category] = rec;
    });
  }

  const prioritiesMap = {};
  if (recoveryPriorities?.priorities) {
    recoveryPriorities.priorities.forEach((p) => {
      prioritiesMap[p.category] = p;
    });
  }

  const highPrioCount = recoveryPriorities?.high_priority_count ?? 0;
  const medPrioCount = recoveryPriorities?.medium_priority_count ?? 0;
  const lowPrioCount = recoveryPriorities?.low_priority_count ?? 0;

  // Filtered lists for Priority View & Sector View
  const sortedPriorities = recoveryPriorities?.priorities || [];
  const filteredPriorities = sortedPriorities.filter((p) => {
    if (filterType === 'high') return p.priority_level === 'HIGH';
    if (filterType === 'medium') return p.priority_level === 'MEDIUM';
    if (filterType === 'low') return p.priority_level === 'LOW';
    if (filterType === 'environmental') return p.category_type === 'environmental';
    if (filterType === 'infrastructure') return p.category_type === 'infrastructure';
    return true;
  });

  const filteredCategories = categories.filter((cat) => {
    const p = prioritiesMap[cat.category_id];
    if (filterType === 'high') return p?.priority_level === 'HIGH';
    if (filterType === 'medium') return p?.priority_level === 'MEDIUM';
    if (filterType === 'low') return p?.priority_level === 'LOW';
    if (filterType === 'environmental') return cat.category_type === 'environmental';
    if (filterType === 'infrastructure') return cat.category_type === 'infrastructure';
    return true;
  });

  // Pure deterministic client-side fallback simulation
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

  return (
    <div className="damage-assessment-panel">
      {/* Header Banner */}
      <div className="card damage-header-card">
        <div className="damage-header-top">
          <div className="damage-title-group">
            <div className="damage-badge-pill">
              <Shield size={13} color="#38bdf8" />
              <span>Sustainability Extension • Parts 1, 2, 3 & 4</span>
            </div>
            <h2 className="damage-main-title">
              Post-Flood Recovery Priority & Resource Optimization Engine
            </h2>
            <p className="damage-subtitle">
              Multi-criteria prioritization ranking affected locations (HIGH / MEDIUM / LOW) and simulating optimal hypothetical recovery budget allocation under workforce capacity constraints.
            </p>
          </div>
        </div>

        {/* Top KPI Metrics Grid */}
        <div className="damage-kpi-grid">
          <div className="damage-kpi-card">
            <span className="kpi-label">HIGH Priority Sectors</span>
            <div className="kpi-value-row">
              <span className="kpi-val highlight-rose">{highPrioCount}</span>
              <span className="kpi-denom">/ {categories.length} sectors</span>
            </div>
            <span className="kpi-sub">Immediate intervention required</span>
          </div>

          <div className="damage-kpi-card">
            <span className="kpi-label">MEDIUM Priority Sectors</span>
            <div className="kpi-value-row">
              <span className="kpi-val highlight-amber">{medPrioCount}</span>
              <span className="kpi-denom">/ {categories.length} sectors</span>
            </div>
            <span className="kpi-sub">Targeted / verification surveys</span>
          </div>

          <div className="damage-kpi-card">
            <span className="kpi-label">LOW Priority (Natural)</span>
            <div className="kpi-value-row">
              <span className="kpi-val highlight-green">{lowPrioCount}</span>
              <span className="kpi-denom">/ {categories.length} sectors</span>
            </div>
            <span className="kpi-sub">High natural recovery capacity</span>
          </div>

          <div className="damage-kpi-card">
            <span className="kpi-label">Submerged Assets</span>
            <div className="kpi-value-row">
              <span className="kpi-val highlight-blue">
                {summary?.total_submerged_buildings != null ? `${summary.total_submerged_buildings} bldgs` : '0'}
              </span>
            </div>
            <span className="kpi-sub">
              {summary?.total_inundated_roads_km != null ? `${summary.total_inundated_roads_km} km roads` : '0 km'}
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
          <div className="flow-step active-flow-step">
            <span className="flow-badge">5. OPTIMIZATION</span>
            <span className="flow-desc">Resource & Budget Allocation</span>
          </div>
        </div>
      </div>

      {/* Primary Sub-Navigation Tabs */}
      <div className="damage-subnav-bar">
        <div className="subnav-toggle-group">
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

      {/* VIEW 0: RESOURCE / BUDGET OPTIMIZATION (PART 4) */}
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

      {/* VIEW 1: RECOVERY PRIORITY RANKING ENGINE */}
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
                          {item.category_type.toUpperCase()}
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
                          {item.priority_score.toFixed(1)}
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

      {/* VIEW 2: DETAILED SECTORS */}
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
                          {cat.category_type.toUpperCase()}
                        </span>
                        <span className="cat-confidence-tag">
                          Confidence: <b>{cat.confidence_level}</b>
                        </span>
                        {prio && (
                          <span className={`prio-inline-badge ${prioConfig?.badge}`}>
                            #{prio.priority_rank} {prio.priority_level} ({prio.priority_score.toFixed(1)}/10)
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
          <li>Budget amounts (₹ Lakhs) and site capacity units are hypothetical decision-support simulation values designed to demonstrate multi-criteria trade-off modeling.</li>
          <li>They do not represent official government contract tenders, commercial price quotes, or engineering guarantees.</li>
          <li>Sectors with high natural recovery potential are deferred by default to avoid wasteful capital expenditure where natural processes suffice.</li>
          <li>Priority rankings and resource allocation outcomes can directly feed into long-term monitoring and verification (Parts 5–7).</li>
        </ul>
      </div>
    </div>
  );
}
