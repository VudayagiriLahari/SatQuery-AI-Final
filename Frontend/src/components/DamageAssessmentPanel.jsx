import React, { useState } from 'react';
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
} from 'lucide-react';

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

export default function DamageAssessmentPanel({
  damageAssessment,
  recoveryRecommendations,
  recoveryPriorities,
  onSelectFeature,
  onNavigateToTab,
}) {
  const [activeView, setActiveView] = useState('priorities'); // 'priorities' | 'sectors'
  const [filterType, setFilterType] = useState('all');
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);

  if (!damageAssessment || !damageAssessment.categories) {
    return (
      <div className="empty-state-card card">
        <ClipboardCheck size={32} color="#38bdf8" className="empty-icon" />
        <h3>No Damage & Priority Assessment Data</h3>
        <p>Run full flood analysis to generate damage metrics, sustainable recovery actions, and priority rankings.</p>
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

  // Filtered lists
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

  return (
    <div className="damage-assessment-panel">
      {/* Header Banner */}
      <div className="card damage-header-card">
        <div className="damage-header-top">
          <div className="damage-title-group">
            <div className="damage-badge-pill">
              <Shield size={13} color="#38bdf8" />
              <span>Sustainability Extension • Parts 1, 2 & 3</span>
            </div>
            <h2 className="damage-main-title">
              Post-Flood Recovery Priority & Decision-Support Engine
            </h2>
            <p className="damage-subtitle">
              Multi-criteria prioritization ranking affected locations (HIGH / MEDIUM / LOW) based on damage severity, infrastructure criticality, population impact, and natural recovery potential.
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
            <span className="flow-badge">2. RECOVERY CONDITION</span>
            <span className="flow-desc">Natural vs. Assisted</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step">
            <span className="flow-badge">3. RECOMMENDED ACTION</span>
            <span className="flow-desc">Sustainable Practices</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step">
            <span className="flow-badge">4. PRIORITY & SCORE</span>
            <span className="flow-desc">HIGH / MED / LOW</span>
          </div>
          <ChevronRight size={14} className="flow-arrow" />
          <div className="flow-step">
            <span className="flow-badge">5. WHY (REASON)</span>
            <span className="flow-desc">Transparent Evidence</span>
          </div>
        </div>
      </div>

      {/* Primary Sub-Navigation Tabs */}
      <div className="damage-subnav-bar">
        <div className="subnav-toggle-group">
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

      {/* Filter Chips Bar */}
      <div className="damage-filter-bar">
        <div className="filter-tab-buttons">
          <button
            className={`filter-btn ${filterType === 'all' ? 'active' : ''}`}
            onClick={() => setFilterType('all')}
          >
            All ({categories.length})
          </button>
          <button
            className={`filter-btn ${filterType === 'high' ? 'active' : ''}`}
            onClick={() => setFilterType('high')}
          >
            HIGH Priority ({highPrioCount})
          </button>
          <button
            className={`filter-btn ${filterType === 'medium' ? 'active' : ''}`}
            onClick={() => setFilterType('medium')}
          >
            MEDIUM Priority ({medPrioCount})
          </button>
          <button
            className={`filter-btn ${filterType === 'low' ? 'active' : ''}`}
            onClick={() => setFilterType('low')}
          >
            LOW Priority ({lowPrioCount})
          </button>
          <button
            className={`filter-btn ${filterType === 'environmental' ? 'active' : ''}`}
            onClick={() => setFilterType('environmental')}
          >
            Environmental (5)
          </button>
          <button
            className={`filter-btn ${filterType === 'infrastructure' ? 'active' : ''}`}
            onClick={() => setFilterType('infrastructure')}
          >
            Infrastructure (3)
          </button>
        </div>
      </div>

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
                className={`priority-card card ${isSelected ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedCategoryId(item.category);
                  const matchingCat = categories.find((c) => c.category_id === item.category);
                  if (matchingCat?.geojson && onSelectFeature) {
                    onSelectFeature({
                      type: item.category === 'buildings' ? 'building' : (item.category === 'roads' ? 'road' : 'damage'),
                      name: item.category_name,
                      data: matchingCat,
                    });
                  }
                }}
              >
                {/* Header: Rank, Icon, Title, Priority Badge & Score */}
                <div className="prio-card-header">
                  <div className="prio-rank-group">
                    <span className="prio-rank-badge">#{item.priority_rank}</span>
                    <div className="cat-icon-wrapper">
                      <IconComp size={18} color="#38bdf8" />
                    </div>
                    <div>
                      <div className="cat-type-row">
                        <span className={`cat-sector-tag ${item.category_type}`}>
                          {item.category_type.toUpperCase()}
                        </span>
                        <span className="cat-confidence-tag">
                          Domain: <b>{item.target_resource_domain}</b>
                        </span>
                      </div>
                      <h3 className="cat-title">{item.category_name}</h3>
                    </div>
                  </div>

                  <div className="prio-score-group">
                    <div className="prio-score-block">
                      <span className="prio-score-val" style={{ color: prioConfig.color }}>
                        {item.priority_score.toFixed(1)}
                      </span>
                      <span className="prio-score-max">/ 10</span>
                    </div>
                    <span className={`prio-level-badge ${prioConfig.badge}`}>
                      <PrioIcon size={12} style={{ marginRight: 4 }} />
                      {item.priority_level} PRIORITY
                    </span>
                  </div>
                </div>

                {/* Score Factor Visual Bar */}
                <div className="prio-progress-container">
                  <div
                    className="prio-progress-bar"
                    style={{
                      width: `${Math.min(100, Math.max(5, item.priority_score * 10))}%`,
                      backgroundColor: prioConfig.color,
                    }}
                  />
                </div>

                {/* Key Indicators Row */}
                <div className="prio-indicators-row">
                  <div className="prio-indicator-item">
                    <span className="lbl">Damage Severity:</span>
                    <span className="val">{item.damage_severity}</span>
                  </div>
                  <div className="prio-indicator-item">
                    <span className="lbl">Natural Recovery:</span>
                    <span className={`val ${item.natural_recovery_likelihood === 'High' ? 'highlight-green' : ''}`}>
                      {item.natural_recovery_likelihood}
                    </span>
                  </div>
                  <div className="prio-indicator-item">
                    <span className="lbl">Urgency:</span>
                    <span className="val">{item.urgency}</span>
                  </div>
                  <div className="prio-indicator-item">
                    <span className="lbl">Est. Effort:</span>
                    <span className="val">{item.estimated_effort_level}</span>
                  </div>
                </div>

                {/* Recommended Action Box */}
                <div className="prio-action-box">
                  <div className="prio-action-header">
                    <Sparkles size={13} color="#38bdf8" />
                    <span className="prio-action-lbl">RECOMMENDED ACTION:</span>
                    <span className="prio-action-name">{item.recommended_action}</span>
                  </div>
                </div>

                {/* Plain-Language Justification (WHY) */}
                <div className="prio-reason-box">
                  <span className="reason-lbl">PRIORITY JUSTIFICATION (WHY):</span>
                  <p className="reason-text">{item.reason}</p>
                </div>

                {/* Factor Contribution Breakdown */}
                {item.contributing_factors && (
                  <div className="prio-factors-grid">
                    <div className="factor-chip">
                      <span>Damage Severity:</span>
                      <b>{(item.contributing_factors.damage_severity_score * 10).toFixed(1)}/10</b>
                    </div>
                    <div className="factor-chip">
                      <span>Infrastructure:</span>
                      <b>{(item.contributing_factors.infrastructure_importance_score * 10).toFixed(1)}/10</b>
                    </div>
                    <div className="factor-chip">
                      <span>Population Impact:</span>
                      <b>{(item.contributing_factors.population_impact_score * 10).toFixed(1)}/10</b>
                    </div>
                    <div className="factor-chip">
                      <span>Urgency:</span>
                      <b>{(item.contributing_factors.urgency_score * 10).toFixed(1)}/10</b>
                    </div>
                    <div className="factor-chip">
                      <span>Recovery Modifier:</span>
                      <b>{item.contributing_factors.natural_recovery_factor.toFixed(2)}x</b>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* VIEW 2: DETAILED SECTORS & RECOMMENDATIONS */}
      {activeView === 'sectors' && (
        <div className="damage-categories-list">
          {filteredCategories.map((cat) => {
            const IconComp = CATEGORY_ICONS[cat.category_id] || ClipboardCheck;
            const rec = recommendationsMap[cat.category_id];
            const prio = prioritiesMap[cat.category_id];
            const recCondition = rec?.recovery_classification || cat.recovery_classification;
            const recConfig = RECOVERY_COLORS[recCondition] || {
              badge: 'recovery-natural',
              icon: CheckCircle2,
              color: '#10b981',
              label: recCondition,
            };
            const RecIcon = recConfig.icon;
            const isSelected = selectedCategoryId === cat.category_id;
            const prioConfig = prio ? (PRIORITY_BADGES[prio.priority_level] || PRIORITY_BADGES.MEDIUM) : null;

            const recommendedAction = rec?.recommended_action || cat.recovery_notes;
            const reasonText = rec?.reason || cat.detected_change;
            const practices = rec?.sustainable_practices || [];
            const urgency = rec?.urgency || 'Medium-Term';
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
          <li>Priority rankings are multi-criteria decision-support scores $[0.0 - 10.0]$ designed to guide recovery resource allocation.</li>
          <li>Sectors with high natural recovery potential receive lower priority scores to avoid unnecessary resource expenditure where natural processes suffice.</li>
          <li>No exact financial costs or unverified biological mortality are asserted without in-situ ground engineering assessments.</li>
          <li>Part 4 (Budget & Resource Optimization) can directly consume these ranked sector priorities.</li>
        </ul>
      </div>
    </div>
  );
}
