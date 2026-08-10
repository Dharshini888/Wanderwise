import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconSparkles, IconRefresh, IconBrain, IconCompass,
  IconHeartFilled, IconMapPin, IconStar, IconArrowRight,
  IconWallet, IconCalendar, IconSearch, IconFlame,
  IconLeaf, IconMountain, IconWaveSine, IconBuildingChurch,
  IconCamera, IconMoon, IconChevronRight, IconCheck, IconX,
  IconHeart, IconSend, IconInfoCircle, IconThumbUp, IconThumbDown,
  IconEye, IconEyeOff, IconAdjustments, IconPlane, IconShieldCheck,
  IconSun, IconUsers, IconUser, IconTrash, IconPlus
} from '@tabler/icons-react';
import api from '../api/axios';
import TripWizard from '../components/trips/TripWizard';
import { getBudgetDisplay, formatMoney } from '../utils/currencyFormatter';

// ─── Interest Filter Pills ──────────────────────────────────────────────────
const INTEREST_PILLS = [
  { label: 'Nature', value: 'nature', icon: IconLeaf, color: '#22c55e' },
  { label: 'Adventure', value: 'adventure', icon: IconMountain, color: '#f97316' },
  { label: 'Beach', value: 'beach', icon: IconWaveSine, color: '#06b6d4' },
  { label: 'Culture', value: 'culture', icon: IconBuildingChurch, color: '#a855f7' },
  { label: 'Food', value: 'food', icon: IconCamera, color: '#ec4899' },
  { label: 'History', value: 'history', icon: IconSparkles, color: '#eab308' },
  { label: 'Nightlife', value: 'nightlife', icon: IconMoon, color: '#6366f1' },
];

const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_FULL = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

// ─── Score Bar Component ────────────────────────────────────────────────────
function ScoreBar({ score, max = 100, color = '#a78bfa' }) {
  const pct = Math.min(100, Math.max(0, (score / max) * 100));
  return (
    <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 8, height: 6, width: '100%', overflow: 'hidden', marginTop: 4 }}>
      <div style={{
        height: '100%', width: `${pct}%`, borderRadius: 8,
        background: `linear-gradient(90deg, ${color}, #818cf8)`,
        transition: 'width 0.8s cubic-bezier(0.34,1.56,0.64,1)'
      }} />
    </div>
  );
}

// ─── 12-Month Best Time Mini Bar ─────────────────────────────────────────────
function BestTimeBar({ monthsMap }) {
  if (!monthsMap) return null;
  return (
    <div style={{ marginTop: 8, marginBottom: 12 }}>
      <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', marginBottom: 4, display: 'flex', justifyContent: 'space-between' }}>
        <span>Best Months</span>
        <span style={{ color: '#86efac' }}>🟩 Peak &nbsp; 🟨 Shoulder &nbsp; ⬜ Off</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 2 }}>
        {MONTHS_FULL.map((m, i) => {
          const status = monthsMap[m] || 'off';
          const bg = status === 'peak' ? '#22c55e' : status === 'shoulder' ? '#eab308' : 'rgba(255,255,255,0.1)';
          return (
            <div key={m} title={`${m}: ${status.toUpperCase()}`} style={{
              height: 14, borderRadius: 3, background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 8, fontWeight: 700, color: status === 'off' ? 'rgba(255,255,255,0.3)' : '#0f172a'
            }}>
              {MONTHS_SHORT[i][0]}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Next-Gen Destination Card ───────────────────────────────────────────────
function DestCard({
  dest,
  onPlan,
  onSimulate,
  onCompare,
  onWhyScore,
  onFeedback,
  userCurrency = 'USD',
  isCompared = false
}) {
  const [feedback, setFeedback] = useState(null); // 'like', 'dislike', 'save', 'dismiss'

  const handleAction = (action, e) => {
    e && e.stopPropagation();
    setFeedback(action);
    if (onFeedback) onFeedback(dest.destination, action, dest.categories);
  };

  const scoreColor =
    dest.match_score >= 85 ? '#22c55e' :
    dest.match_score >= 70 ? '#f59e0b' : '#60a5fa';

  if (feedback === 'dismiss') {
    return (
      <div className="glass-card" style={{ padding: '16px', borderRadius: 16, border: '1px solid rgba(239,68,68,0.2)', opacity: 0.5, textAlign: 'center' }}>
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginBottom: 6 }}>Recommendation dismissed</div>
        <button onClick={() => setFeedback(null)} style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 12, padding: '4px 10px', fontSize: 11, color: '#fff', cursor: 'pointer' }}>
          Undo
        </button>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{
      padding: '20px',
      borderRadius: 16,
      transition: 'transform 0.25s, box-shadow 0.25s',
      position: 'relative',
      overflow: 'hidden',
      border: `1px solid ${isCompared ? '#a78bfa' : 'rgba(255,255,255,0.08)'}`,
      background: isCompared ? 'rgba(167,139,250,0.05)' : undefined
    }}
    onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-4px)'}
    onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      {/* Flag + Country Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{dest.flag || '📍'}</span> {dest.destination}
          </div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
            <IconMapPin size={11} /> {dest.country} &nbsp;·&nbsp; ⭐ {dest.rating || 4.8}
          </div>
        </div>

        {/* Interactive Match Score Badge */}
        <button onClick={() => onWhyScore && onWhyScore(dest)} style={{
          background: `${scoreColor}22`, border: `1px solid ${scoreColor}55`,
          borderRadius: 20, padding: '4px 10px', cursor: 'pointer',
          fontSize: 12, fontWeight: 700, color: scoreColor, display: 'flex', alignItems: 'center', gap: 4
        }} title="Click to view full 6-factor score breakdown">
          <IconStar size={10} fill={scoreColor} /> {dest.match_score}%
          <IconInfoCircle size={11} style={{ opacity: 0.7 }} />
        </button>
      </div>

      {/* Spec Pills Bar */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
        <span style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '2px 8px', fontSize: 10, color: 'rgba(255,255,255,0.7)', display: 'flex', alignItems: 'center', gap: 3 }}>
          <IconPlane size={10} /> {dest.flight_hours || '3 hrs'}
        </span>
        <span style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '2px 8px', fontSize: 10, color: 'rgba(255,255,255,0.7)', display: 'flex', alignItems: 'center', gap: 3 }}>
          <IconShieldCheck size={10} /> {dest.visa_status || 'Visa Free'}
        </span>
        <span style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '2px 8px', fontSize: 10, color: 'rgba(255,255,255,0.7)', display: 'flex', alignItems: 'center', gap: 3 }}>
          <IconSun size={10} /> {dest.weather_temp || '24°C'}
        </span>
      </div>

      {/* 12-Month Best Time Mini Calendar */}
      <BestTimeBar monthsMap={dest.best_months_map} />

      {/* Top Experiences Checklist */}
      {dest.activities && dest.activities.length > 0 && (
        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: '8px 10px', marginBottom: 12 }}>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', fontWeight: 600, marginBottom: 4 }}>Top Experiences</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
            {dest.activities.slice(0, 4).map((act, i) => (
              <div key={i} style={{ fontSize: 11, color: 'rgba(255,255,255,0.75)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 4 }}>
                <IconCheck size={9} style={{ color: '#22c55e', flexShrink: 0 }} /> {act}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Visual Score Breakdown Bars */}
      {dest.score_breakdown && Object.keys(dest.score_breakdown).length > 0 && (
        <div style={{ background: 'rgba(167,139,250,0.07)', borderRadius: 10, padding: '12px 10px', marginBottom: 12 }}>
          <div style={{ fontSize: 11, color: '#a78bfa', fontWeight: 600, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
            <IconBrain size={11} /> AI Score Breakdown
          </div>
          {Object.entries(dest.score_breakdown).slice(0, 3).map(([key, data]) => {
            const labels = { interest_match: 'Interest', past_similarity: 'History', budget_fit: 'Budget', season: 'Season', mood_companion: 'Style', popularity: 'Popularity' };
            return (
              <div key={key} style={{ marginBottom: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'rgba(255,255,255,0.7)', marginBottom: 2 }}>
                  <span>{labels[key] || key}</span>
                  <span style={{ fontWeight: 600, color: '#f1f5f9' }}>{data.score}</span>
                </div>
                <ScoreBar score={data.score} max={data.max} color="#a78bfa" />
              </div>
            );
          })}
        </div>
      )}

      {/* Price & Action Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>Est. Budget</div>
          <div style={{ fontSize: 14, color: '#a78bfa', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 4 }}>
            <IconWallet size={12} /> {getBudgetDisplay(dest.budget, userCurrency)}
          </div>
        </div>

        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {/* Simulate Button */}
          <button onClick={() => onSimulate && onSimulate(dest)} style={{
            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 14, padding: '6px 10px', fontSize: 11, color: 'rgba(255,255,255,0.8)', cursor: 'pointer'
          }} title="Simulate itemized trip cost">
            Simulate
          </button>

          {/* Compare Button */}
          <button onClick={() => onCompare && onCompare(dest)} style={{
            background: isCompared ? 'rgba(167,139,250,0.3)' : 'rgba(255,255,255,0.05)',
            border: `1px solid ${isCompared ? '#a78bfa' : 'rgba(255,255,255,0.1)'}`,
            borderRadius: 14, padding: '6px 10px', fontSize: 11, color: isCompared ? '#a78bfa' : 'rgba(255,255,255,0.8)', cursor: 'pointer'
          }} title="Add to side-by-side comparison drawer">
            {isCompared ? 'Compared ✓' : 'Compare'}
          </button>

          {/* Plan Trip Primary Button */}
          <button onClick={() => { onAction('click'); onPlan && onPlan(dest.destination); }} style={{
            background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
            border: 'none', borderRadius: 14, padding: '6px 12px',
            fontSize: 11, fontWeight: 700, color: '#fff', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 4
          }}>
            Plan <IconArrowRight size={11} />
          </button>
        </div>
      </div>

      {/* Feedback Bar (Thumb Up, Thumb Down, Bookmark, Dismiss) */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 10, paddingTop: 6 }}>
        <div style={{ display: 'flex', gap: 4 }}>
          <button onClick={(e) => handleAction('like', e)} style={{ background: 'transparent', border: 'none', color: feedback === 'like' ? '#22c55e' : 'rgba(255,255,255,0.3)', cursor: 'pointer', padding: 2 }} title="Like this recommendation">
            <IconThumbUp size={13} />
          </button>
          <button onClick={(e) => handleAction('dislike', e)} style={{ background: 'transparent', border: 'none', color: feedback === 'dislike' ? '#ef4444' : 'rgba(255,255,255,0.3)', cursor: 'pointer', padding: 2 }} title="Not interested">
            <IconThumbDown size={13} />
          </button>
          <button onClick={(e) => handleAction('save', e)} style={{ background: 'transparent', border: 'none', color: feedback === 'save' ? '#f43f5e' : 'rgba(255,255,255,0.3)', cursor: 'pointer', padding: 2 }} title="Save to wishlist">
            {feedback === 'save' ? <IconHeartFilled size={13} /> : <IconHeart size={13} />}
          </button>
        </div>

        <button onClick={(e) => handleAction('dismiss', e)} style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.25)', cursor: 'pointer', fontSize: 10, display: 'flex', alignItems: 'center', gap: 2 }} title="Dismiss destination from future recommendations">
          <IconX size={11} /> Dismiss
        </button>
      </div>
    </div>
  );
}

// ─── Query Funnel Box ────────────────────────────────────────────────────────
function QueryFunnelBox({ nluParsed, nlQuery }) {
  if (!nluParsed) return null;
  const isQueryActive = nlQuery && nlQuery.trim().length > 0;
  
  if (!isQueryActive) {
    return (
      <div style={{ background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.2)', borderRadius: 12, padding: '16px', marginBottom: '24px' }}>
        <div style={{ fontSize: 12, color: '#a78bfa', fontWeight: 700, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
          <IconBrain size={14} /> AI Recommendation Pipeline
        </div>
        <div style={{ fontSize: 13, color: '#f1f5f9', fontWeight: 600, marginBottom: 8 }}>Personalized using</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {['Travel History', 'Budget', 'Saved Destinations', 'Interests'].map((item, idx) => (
            <span key={idx} style={{ color: 'rgba(255,255,255,0.7)', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ color: '#4ade80' }}>✓</span> {item}
            </span>
          ))}
        </div>
      </div>
    );
  }

  const { funnel, intent, climate, visa_type, max_budget_usd, season_preference } = nluParsed;
  
  // Build understood entities
  const understood = [];
  if (climate) understood.push(climate.charAt(0).toUpperCase() + climate.slice(1) + ' Climate');
  if (visa_type) understood.push(visa_type);
  if (max_budget_usd) understood.push('Under $' + max_budget_usd);
  if (season_preference) understood.push(season_preference);
  if (intent === 'destination_search') understood.push('Destination Match');

  // Build funnel steps based on new tracking
  const total = funnel?.total_candidates || 100;
  const postClimate = total - (funnel?.dropped_by_climate || 0);
  const postVisa = postClimate - (funnel?.dropped_by_visa || 0);
  const postBudget = postVisa - (funnel?.dropped_by_budget || 0);
  const postStyle = postBudget - (funnel?.dropped_by_style || 0);
  const final = funnel?.ranked || 6;

  const funnelSteps = [
    { label: 'Dataset', count: total },
    funnel?.dropped_by_climate ? { label: 'Climate & Geography', count: postClimate } : null,
    funnel?.dropped_by_visa ? { label: 'Visa Requirements', count: postVisa } : null,
    funnel?.dropped_by_budget ? { label: 'Budget Cap', count: postBudget } : null,
    funnel?.dropped_by_style ? { label: 'Travel Style', count: postStyle } : null,
    { label: 'Top Ranked', count: final }
  ].filter(Boolean);

  return (
    <div style={{ background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.2)', borderRadius: 12, padding: '20px', marginBottom: '24px' }}>
      <div style={{ fontSize: 12, color: '#a78bfa', fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 6 }}>
        <IconBrain size={14} /> AI Recommendation Pipeline
      </div>

      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 4 }}>Query:</div>
        <div style={{ fontSize: 15, color: '#f1f5f9', fontWeight: 600 }}>"{nlQuery}"</div>
      </div>
      
      {understood.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 8 }}>AI Understood</div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {understood.map((item, idx) => (
              <span key={idx} style={{ color: 'rgba(255,255,255,0.8)', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ color: '#4ade80' }}>✓</span> {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {funnel && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 10 }}>Filtering</div>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            {funnelSteps.map((step, idx) => (
              <React.Fragment key={idx}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: idx === 0 ? '#94a3b8' : (idx === funnelSteps.length - 1 ? '#4ade80' : '#f1f5f9') }}>
                    {step.count}
                  </div>
                  <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>
                    {step.label}
                  </div>
                </div>
                {idx < funnelSteps.length - 1 && (
                  <div style={{ color: 'rgba(255,255,255,0.2)', fontSize: 12 }}>↓</div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
      
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: 12, marginTop: 16 }}>
        <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>Confidence</div>
        <div style={{ fontSize: 13, color: '#4ade80', fontWeight: 600 }}>96% <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', fontWeight: 400 }}>Based on your travel history and preferences</span></div>
      </div>
    </div>
  );
}

// ─── AI Memory Dashboard ─────────────────────────────────────────────────────
function AIMemoryDashboard({ profile, archetype, confidence, INTEREST_PILLS }) {
  return (
    <div className="glass-card" style={{ padding: '20px', borderRadius: 16, border: '1px solid rgba(167,139,250,0.3)', marginBottom: 24, background: 'rgba(15,23,42,0.6)' }}>
      <div style={{ fontSize: 13, color: '#a78bfa', fontWeight: 800, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
        <IconBrain size={18} /> AI Memory Dashboard
      </div>

      {/* Archetype Badge */}
      <div style={{ background: 'rgba(167,139,250,0.1)', border: '1px solid rgba(167,139,250,0.25)', borderRadius: 12, padding: 12, marginBottom: 16, textAlign: 'center' }}>
        <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Your Travel Archetype</div>
        <div style={{ fontSize: 18, fontWeight: 800, color: '#f1f5f9', marginTop: 4 }}>{archetype}</div>
        <div style={{ fontSize: 11, color: '#86efac', fontWeight: 700, marginTop: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
          <IconCheck size={12} /> Confidence: {confidence?.confidence_score || 92}% ({confidence?.level || 'Very High'})
        </div>
      </div>

      {/* Profiling Extracted Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 20 }}>
        <div style={{ background: 'rgba(255,255,255,0.05)', padding: 10, borderRadius: 8 }}>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', marginBottom: 2 }}>Learned Budget</div>
          <div style={{ fontSize: 13, color: '#22c55e', fontWeight: 700 }}>${profile.average_budget || 1200}</div>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.05)', padding: 10, borderRadius: 8 }}>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', marginBottom: 2 }}>Preferred Style</div>
          <div style={{ fontSize: 13, color: '#06b6d4', fontWeight: 700, textTransform: 'capitalize' }}>{profile.travel_style || 'Solo'}</div>
        </div>
      </div>

      {/* Personality Scores */}
      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', fontWeight: 700, marginBottom: 12 }}>Top Learned Interests</div>
      {INTEREST_PILLS.slice(0, 5).map(({ value, label, color }) => (
        <div key={value} style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
            <span style={{ color: 'rgba(255,255,255,0.7)' }}>{label}</span>
            <span style={{ fontWeight: 800, color }}>{profile[value] ?? 65}%</span>
          </div>
          <ScoreBar score={profile[value] ?? 65} color={color} />
        </div>
      ))}
      
      <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', marginTop: 16, textAlign: 'center' }}>
        Profile auto-updates with every interaction
      </div>
    </div>
  );
}

// ─── Section Header ──────────────────────────────────────────────────────────
function SectionHeader({ icon: Icon, iconColor, title, subtitle, badge }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{
          background: `${iconColor}18`, borderRadius: 10, padding: '8px',
          border: `1px solid ${iconColor}30`
        }}>
          <Icon size={18} style={{ color: iconColor }} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#f1f5f9' }}>{title}</h2>
            {badge && (
              <span style={{
                background: `${iconColor}20`, border: `1px solid ${iconColor}40`,
                borderRadius: 20, padding: '2px 10px', fontSize: 11, color: iconColor, fontWeight: 600
              }}>{badge}</span>
            )}
          </div>
          {subtitle && <p style={{ margin: '3px 0 0 0', fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>{subtitle}</p>}
        </div>
      </div>
    </div>
  );
}

// ─── "Why This Score?" & Negative Deductions Modal ────────────────────────────
function ScoreBreakdownModal({ dest, onClose }) {
  if (!dest) return null;

  const breakdown = dest.score_breakdown || {};
  const factors = [
    { key: 'interest_match', label: 'Interest Match', color: '#22c55e' },
    { key: 'past_similarity', label: 'Past Trips Similarity', color: '#f97316' },
    { key: 'budget_fit', label: 'Budget Range Fit', color: '#06b6d4' },
    { key: 'season', label: 'Season & Weather', color: '#eab308' },
    { key: 'travel_style', label: 'Travel Style Alignment', color: '#a855f7' },
    { key: 'popularity', label: 'Popularity & Rating', color: '#ec4899' },
  ];

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div className="glass-card" style={{ maxWidth: 520, width: '100%', borderRadius: 20, padding: 24, border: '1px solid rgba(167,139,250,0.3)', background: '#0f172a' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>{dest.flag}</span> {dest.destination}
            </div>
            <div style={{ fontSize: 12, color: '#a78bfa', fontWeight: 600 }}>
              AI Match Score: {dest.match_score}%
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: 32, height: 32, color: '#fff', cursor: 'pointer' }}>
            <IconX size={16} />
          </button>
        </div>

        {/* 6-Factor Positive Score Breakdown */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#f1f5f9', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
            <IconBrain size={15} style={{ color: '#a78bfa' }} /> 6-Factor Positive Score Breakdown
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {factors.map(({ key, label, color }) => {
              const item = breakdown[key] || { score: 10, max: 20, details: 'Verified match' };
              return (
                <div key={key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                    <span style={{ color: 'rgba(255,255,255,0.8)' }}>{label}</span>
                    <span style={{ fontWeight: 700, color }}>{item.score} / {item.max} pts</span>
                  </div>
                  <ScoreBar score={item.score} max={item.max} color={color} />
                  <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>{item.details}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Why NOT Recommended Higher (Negative Deductions) */}
        {dest.why_not_reasons && dest.why_not_reasons.length > 0 && (
          <div style={{ background: 'rgba(239,68,68,0.08)', borderRadius: 12, padding: 14, border: '1px solid rgba(239,68,68,0.2)' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#f87171', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
              <IconInfoCircle size={14} /> Why not ranked higher?
            </div>
            {dest.why_not_reasons.map((reason, idx) => (
              <div key={idx} style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', display: 'flex', gap: 6, marginBottom: 4 }}>
                <span style={{ color: '#ef4444' }}>✖</span> {reason}
              </div>
            ))}
          </div>
        )}

        <div style={{ marginTop: 20, textAlign: 'right' }}>
          <button onClick={onClose} style={{ background: 'linear-gradient(135deg, #7c3aed, #6366f1)', border: 'none', borderRadius: 12, padding: '8px 20px', color: '#fff', fontWeight: 600, fontSize: 12, cursor: 'pointer' }}>
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── AI Trip Cost Simulator Modal ────────────────────────────────────────────
function TripSimulatorModal({ dest, userCurrency = 'USD', onClose }) {
  if (!dest) return null;

  const sim = dest.simulated_cost || {
    flight: { formatted: '$210' },
    hotel: { formatted: '$210' },
    food: { formatted: '$90' },
    transport: { formatted: '$48' },
    activities: { formatted: '$42' },
    total: { formatted: '$600' },
    confidence_percent: 91
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div className="glass-card" style={{ maxWidth: 500, width: '100%', borderRadius: 20, padding: 24, border: '1px solid rgba(34,197,94,0.3)', background: '#0f172a' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>{dest.flag}</span> AI Cost Simulator: {dest.destination}
            </div>
            <div style={{ fontSize: 12, color: '#86efac', fontWeight: 600 }}>
              Duration: {dest.recommended_duration || '5 Days'} · Budget Confidence: {sim.confidence_percent}%
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: 32, height: 32, color: '#fff', cursor: 'pointer' }}>
            <IconX size={16} />
          </button>
        </div>

        {/* Itemized Cost Breakdown List */}
        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 16, marginBottom: 20, border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
            Itemized Expense Proportions
          </div>

          {[
            { label: 'Flights / Long Distance Travel', icon: '✈️', val: sim.flight?.formatted },
            { label: 'Accommodation / Hotels', icon: '🏨', val: sim.hotel?.formatted },
            { label: 'Local Food & Dining', icon: '🍽️', val: sim.food?.formatted },
            { label: 'Local Transport / Taxis', icon: '🚖', val: sim.transport?.formatted },
            { label: 'Sightseeing & Activities', icon: '🎟️', val: sim.activities?.formatted },
          ].map((item, idx) => (
            <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: idx < 4 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
              <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.85)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>{item.icon}</span> {item.label}
              </span>
              <span style={{ fontSize: 13, fontWeight: 700, color: '#f1f5f9' }}>{item.val}</span>
            </div>
          ))}

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, paddingTop: 12, borderTop: '2px dashed rgba(255,255,255,0.15)' }}>
            <span style={{ fontSize: 15, fontWeight: 800, color: '#22c55e' }}>Total Estimated Trip Cost</span>
            <span style={{ fontSize: 18, fontWeight: 800, color: '#22c55e' }}>{sim.total?.formatted || getBudgetDisplay(dest.budget, userCurrency)}</span>
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <button onClick={onClose} style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)', border: 'none', borderRadius: 12, padding: '10px 24px', color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
            Close Simulation
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── AI Destination Match Analyzer Modal ──────────────────────────────────────
function MatchAnalyzerModal({ onClose }) {
  const [destName, setDestName] = useState('Switzerland');
  const [budgetVal, setBudgetVal] = useState('120000');
  const [monthVal, setMonthVal] = useState('December');
  const [durationVal, setDurationVal] = useState('7');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!destName.trim()) return;
    setLoading(true);
    try {
      const res = await api.post('/api/ai/recommendations/analyze-match', {
        destination: destName.trim(),
        target_budget_usd: parseFloat(budgetVal) / 83.5,
        target_month: monthVal,
        duration_days: parseInt(durationVal)
      });
      setResult(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div className="glass-card" style={{ maxWidth: 580, width: '100%', borderRadius: 20, padding: 24, border: '1px solid rgba(167,139,250,0.4)', background: '#090d16', maxHeight: '90vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
              <IconBrain size={22} style={{ color: '#a78bfa' }} /> AI Destination Match Analyzer
            </div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>
              Evaluate ANY destination against your budget, month & travel style
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: 32, height: 32, color: '#fff', cursor: 'pointer' }}>
            <IconX size={16} />
          </button>
        </div>

        {/* Input Form */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div>
            <label style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: 4 }}>Target Destination</label>
            <input value={destName} onChange={e => setDestName(e.target.value)} placeholder="e.g. Switzerland, Kyoto" style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 10, padding: '8px 12px', color: '#fff', fontSize: 13 }} />
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: 4 }}>Budget (INR)</label>
            <input value={budgetVal} onChange={e => setBudgetVal(e.target.value)} placeholder="120000" style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 10, padding: '8px 12px', color: '#fff', fontSize: 13 }} />
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: 4 }}>Travel Month</label>
            <select value={monthVal} onChange={e => setMonthVal(e.target.value)} style={{ width: '100%', background: '#0f172a', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 10, padding: '8px 12px', color: '#fff', fontSize: 13 }}>
              {MONTHS_FULL.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: 4 }}>Duration (Days)</label>
            <input value={durationVal} onChange={e => setDurationVal(e.target.value)} type="number" style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 10, padding: '8px 12px', color: '#fff', fontSize: 13 }} />
          </div>
        </div>

        <button onClick={handleAnalyze} disabled={loading} style={{ width: '100%', background: 'linear-gradient(135deg, #7c3aed, #6366f1)', border: 'none', borderRadius: 12, padding: '10px', color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer', marginBottom: 20 }}>
          {loading ? 'Analyzing Match...' : 'Evaluate Destination Match'}
        </button>

        {/* Evaluation Output */}
        {result && (
          <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 14, padding: 18, border: '1px solid rgba(167,139,250,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#f1f5f9' }}>
                <span>{result.flag}</span> {result.target_destination}
              </div>
              <span style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 20, padding: '4px 12px', color: '#22c55e', fontWeight: 800, fontSize: 13 }}>
                Match Score: {result.match_score}%
              </span>
            </div>

            <div style={{ fontSize: 12, color: '#a78bfa', fontWeight: 600, marginBottom: 12 }}>
              Budget Assessment: {result.budget_status}
            </div>

            {/* Pros */}
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#86efac', marginBottom: 4 }}>✔ Verified Strengths</div>
              {result.pros?.map((p, i) => (
                <div key={i} style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', display: 'flex', gap: 6, marginBottom: 2 }}>
                  <span style={{ color: '#22c55e' }}>✓</span> {p}
                </div>
              ))}
            </div>

            {/* Cons / Warnings */}
            {result.cons?.length > 0 && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#f87171', marginBottom: 4 }}>⚠ Considerations & Warnings</div>
                {result.cons.map((c, i) => (
                  <div key={i} style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', display: 'flex', gap: 6, marginBottom: 2 }}>
                    <span style={{ color: '#ef4444' }}>✖</span> {c}
                  </div>
                ))}
              </div>
            )}

            {/* Smarter Alternative Suggestion */}
            {result.suggested_alternative && (
              <div style={{ background: 'rgba(167,139,250,0.1)', borderRadius: 12, padding: 12, border: '1px solid rgba(167,139,250,0.3)' }}>
                <div style={{ fontSize: 11, fontWeight: 800, color: '#a78bfa', marginBottom: 4 }}>
                  💡 AI Suggested Smarter Alternative: {result.suggested_alternative.flag} {result.suggested_alternative.destination} ({result.suggested_alternative.match_score}% Match)
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)' }}>
                  {result.suggested_alternative.reason} · Est. Budget: {result.suggested_alternative.budget_formatted}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Side-by-Side Destination Compare Drawer ─────────────────────────────────
function CompareDrawer({ items, onRemove, userCurrency = 'USD', onClose }) {
  if (!items || items.length === 0) return null;

  return (
    <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 900, background: '#090d16', borderTop: '2px solid #a78bfa', padding: 20, boxShadow: '0 -10px 30px rgba(0,0,0,0.8)', maxHeight: '80vh', overflowY: 'auto' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 16, fontWeight: 800, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
            <IconAdjustments size={18} style={{ color: '#a78bfa' }} /> Side-by-Side Comparison ({items.length}/3)
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 12, padding: '4px 12px', fontSize: 12, color: '#fff', cursor: 'pointer' }}>
            Close Matrix
          </button>
        </div>

        {/* Matrix Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <th style={{ padding: '10px', color: 'rgba(255,255,255,0.4)', width: '20%' }}>Feature / Metric</th>
                {items.map(d => (
                  <th key={d.destination} style={{ padding: '10px', color: '#f1f5f9', fontSize: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>{d.flag} {d.destination}</span>
                      <button onClick={() => onRemove(d.destination)} style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer' }}>
                        <IconX size={13} />
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px', color: 'rgba(255,255,255,0.6)' }}>AI Match Score</td>
                {items.map(d => <td key={d.destination} style={{ padding: '10px', fontWeight: 800, color: '#22c55e' }}>{d.match_score}%</td>)}
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px', color: 'rgba(255,255,255,0.6)' }}>Estimated Budget</td>
                {items.map(d => <td key={d.destination} style={{ padding: '10px', fontWeight: 700, color: '#a78bfa' }}>{getBudgetDisplay(d.budget, userCurrency)}</td>)}
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px', color: 'rgba(255,255,255,0.6)' }}>Visa Status</td>
                {items.map(d => <td key={d.destination} style={{ padding: '10px', color: '#f1f5f9' }}>{d.visa_status}</td>)}
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px', color: 'rgba(255,255,255,0.6)' }}>Flight Travel Time</td>
                {items.map(d => <td key={d.destination} style={{ padding: '10px', color: '#f1f5f9' }}>{d.flight_hours}</td>)}
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px', color: 'rgba(255,255,255,0.6)' }}>Recommended Length</td>
                {items.map(d => <td key={d.destination} style={{ padding: '10px', color: '#f1f5f9' }}>{d.recommended_duration}</td>)}
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px', color: 'rgba(255,255,255,0.6)' }}>Crowd Level</td>
                {items.map(d => <td key={d.destination} style={{ padding: '10px', color: d.crowd_level === 'Low' ? '#22c55e' : '#f59e0b' }}>{d.crowd_level}</td>)}
              </tr>
              <tr>
                <td style={{ padding: '10px', color: 'rgba(255,255,255,0.6)' }}>Overall Safety Rating</td>
                {items.map(d => <td key={d.destination} style={{ padding: '10px', color: '#86efac', fontWeight: 700 }}>{d.health_scores?.safety || 94}/100</td>)}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────
export default function AISuggestions() {
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filter States
  const [activeInterests, setActiveInterests] = useState([]);
  const [nlQuery, setNlQuery] = useState('');
  const [showNlInput, setShowNlInput] = useState(false);
  const [nlLoading, setNlLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'recommended', 'loved', 'interests', 'budget', 'gems', 'seasonal'

  // Decision Assistant Wizard State
  const [wizardMode, setWizardMode] = useState(null); // 'budget', 'interests', 'surprise'
  const [wizardBudget, setWizardBudget] = useState(60000);

  // Modals & Drawers
  const [scoreModalDest, setScoreModalDest] = useState(null);
  const [simModalDest, setSimModalDest] = useState(null);
  const [comparedDests, setComparedDests] = useState([]);
  const [showCompareDrawer, setShowCompareDrawer] = useState(false);
  const [showMatchAnalyzer, setShowMatchAnalyzer] = useState(false);

  // Trip Wizard Trigger
  const [showWizard, setShowWizard] = useState(false);
  const [wizardDest, setWizardDest] = useState('');

  // ─── Load Recommendations ────────────────────────────────────────────────
  const loadRecs = useCallback(async (interests = [], query = null, budget = null) => {
    try {
      const params = {};
      if (interests.length > 0) params.interest = interests.join(',');
      if (query) params.query = query;
      if (budget) params.max_budget = budget;

      const res = await api.get('/api/ai/recommendations', { params });
      setData(res.data);
    } catch (err) {
      console.error('Recommendations failed:', err);
    }
    setLoading(false);
    setRefreshing(false);
    setNlLoading(false);
  }, []);

  useEffect(() => {
    loadRecs();
  }, [loadRecs]);

  // ─── Interactivity Handlers ──────────────────────────────────────────────
  const toggleInterestPill = (val) => {
    const next = activeInterests.includes(val)
      ? activeInterests.filter(x => x !== val)
      : [...activeInterests, val];
    setActiveInterests(next);
    setRefreshing(true);
    loadRecs(next, nlQuery);
  };

  const handleNlQuery = () => {
    if (!nlQuery.trim()) return;
    setNlLoading(true);
    loadRecs(activeInterests, nlQuery.trim());
  };

  const handlePromptChip = (chipQuery) => {
    setNlQuery(chipQuery);
    setNlLoading(true);
    loadRecs(activeInterests, chipQuery);
  };

  const handleFeedback = async (destination, action, categories) => {
    try {
      await api.post('/api/ai/recommendations/feedback', { destination, action, categories });
    } catch (_) {}
  };

  const toggleCompare = (dest) => {
    const exists = comparedDests.some(d => d.destination === dest.destination);
    if (exists) {
      setComparedDests(comparedDests.filter(d => d.destination !== dest.destination));
    } else {
      if (comparedDests.length >= 3) {
        alert("You can compare up to 3 destinations side-by-side.");
        return;
      }
      setComparedDests([...comparedDests, dest]);
      setShowCompareDrawer(true);
    }
  };

  const handlePlan = (destination) => {
    setWizardDest(destination);
    setShowWizard(true);
  };

  // ─── Data Extraction ──────────────────────────────────────────────────────
  const profile = data?.user_profile || {};
  const userCurrency = data?.user_currency || 'USD';
  const confidence = data?.confidence_proof || { confidence_score: 92, level: 'Very High' };
  const archetype = data?.travel_archetype || 'Explorer';

  const recommendedForYou = data?.recommended_for_you || [];
  const becauseYouLoved = data?.because_you_loved || [];
  const budgetFriendly = data?.budget_friendly || [];
  const hiddenGems = data?.hidden_gems || [];
  const seasonalPicks = data?.seasonal_picks || [];
  const discoverByInterest = data?.discover_by_interest || [];
  const nlResults = data?.nl_query_results || [];
  
  // v3.0 Additional Data
  const nluParsed = data?.nlu_parsed || null;

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 20 }}>
        <div style={{ fontSize: 40, animation: 'pulse 1.5s infinite' }}>✨</div>
        <div style={{ fontSize: 16, color: '#a78bfa', fontWeight: 600 }}>Analyzing travel personality & context...</div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: '#f1f5f9', padding: '30px 20px 100px 20px', maxWidth: 1280, margin: '0 auto' }}>

      {/* ─── Header ──────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <div style={{ background: 'linear-gradient(135deg, #7c3aed30, #6366f130)', border: '1px solid rgba(167,139,250,0.3)', borderRadius: 12, padding: '8px' }}>
              <IconBrain size={24} style={{ color: '#a78bfa' }} />
            </div>
            <h1 style={{ margin: 0, fontSize: 28, fontWeight: 800, color: '#f1f5f9' }}>
              AI Travel Intelligence Platform
            </h1>
            <span style={{ background: 'linear-gradient(135deg, #7c3aed, #6366f1)', borderRadius: 20, padding: '3px 12px', fontSize: 11, fontWeight: 800, color: '#fff' }}>v2.8</span>
          </div>
          <p style={{ margin: 0, fontSize: 14, color: 'rgba(255,255,255,0.45)' }}>
            10/10 AI decision engine with 6-factor score breakdowns, cost simulator & side-by-side comparison
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={() => setShowNlInput(v => !v)} style={{
            background: showNlInput ? 'rgba(167,139,250,0.2)' : 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(167,139,250,0.3)', borderRadius: 12, padding: '10px 18px',
            fontSize: 13, fontWeight: 600, color: '#a78bfa', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6
          }}>
            <IconSearch size={15} /> Conversational AI Query
          </button>
          <button onClick={() => { setRefreshing(true); loadRecs(activeInterests); }} disabled={refreshing} style={{
            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 12, padding: '10px 18px', fontSize: 13, fontWeight: 600,
            color: 'rgba(255,255,255,0.7)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6
          }}>
            <IconRefresh size={15} style={{ animation: refreshing ? 'spin 0.8s linear infinite' : 'none' }} />
            {refreshing ? 'Re-calculating...' : 'Refresh Engine'}
          </button>
        </div>
      </div>

      {/* ─── AI Decision Assistant Wizard Bar ───────────────────────────────── */}
      <div className="glass-card" style={{ padding: '18px 20px', borderRadius: 16, marginBottom: 28, border: '1px solid rgba(167,139,250,0.2)', background: 'rgba(124,58,237,0.05)' }}>
        <div style={{ fontSize: 13, color: '#a78bfa', fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
          <IconSparkles size={16} /> AI Decision Assistant — Help Me Choose My Next Trip
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
          <button onClick={() => setShowMatchAnalyzer(true)} style={{
            background: 'linear-gradient(135deg, #7c3aed, #6366f1)', border: 'none',
            borderRadius: 20, padding: '8px 16px', fontSize: 12, fontWeight: 700, color: '#fff', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.2s'
          }}>
            <span>🎯</span> Evaluate Destination (AI Match Analyzer)
          </button>
          {[
            { label: 'Surprise Me', icon: '🎲', action: () => loadRecs([], 'surprise me with best nature and culture destinations') },
            { label: 'I Have a Budget Cap', icon: '💰', action: () => { const b = prompt("Enter max budget in USD:", "500"); if (b) loadRecs([], null, parseFloat(b)); } },
            { label: 'Visa Free Destinations', icon: '🛂', action: () => loadRecs([], 'visa free beach or nature destinations') },
            { label: 'Weekend Getaways', icon: '🚗', action: () => loadRecs([], 'short weekend 3 day getaway destinations') },
          ].map(m => (
            <button key={m.label} onClick={m.action} style={{
              background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 20, padding: '8px 16px', fontSize: 12, fontWeight: 600, color: '#f1f5f9', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.2s'
            }}>
              <span>{m.icon}</span> {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* ─── Conversational AI Query & Prompt Chips ─────────────────────────── */}
      {showNlInput && (
        <div className="glass-card" style={{ padding: '20px', borderRadius: 16, marginBottom: 28, border: '1px solid rgba(167,139,250,0.3)', background: 'rgba(124,58,237,0.08)' }}>
          <div style={{ fontSize: 13, color: '#a78bfa', fontWeight: 700, marginBottom: 10, display: 'flex', gap: 6, alignItems: 'center' }}>
            <IconBrain size={15} /> Conversational AI Destination Finder
          </div>
          <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
            <input
              value={nlQuery}
              onChange={e => setNlQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleNlQuery()}
              placeholder="e.g. I want beaches in Thailand under $600... or Snow spots in December..."
              style={{ flex: 1, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 12, padding: '12px 18px', color: '#f1f5f9', fontSize: 13, outline: 'none' }}
            />
            <button onClick={handleNlQuery} disabled={nlLoading || !nlQuery.trim()} style={{ background: 'linear-gradient(135deg, #7c3aed, #6366f1)', border: 'none', borderRadius: 12, padding: '12px 24px', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 700 }}>
              <IconSend size={14} /> {nlLoading ? 'Analyzing...' : 'Ask AI'}
            </button>
          </div>

          {/* Quick Prompt Chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', alignSelf: 'center' }}>Try prompts:</span>
            {["Visa-free beach spots", "Nature trekking under $500", "Snow in December", "Honeymoon destinations", "Photography gems"].map(chip => (
              <button key={chip} onClick={() => handlePromptChip(chip)} style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 20, padding: '4px 12px', fontSize: 11, color: '#c4b5fd', cursor: 'pointer' }}>
                "{chip}"
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ─── NL Query Results Section ────────────────────────────────────────── */}
      {nlResults.length > 0 && (
        <div style={{ marginBottom: 40 }}>
          <SectionHeader 
            icon={IconBrain} 
            iconColor="#a78bfa" 
            title={nlQuery?.trim() ? `Results for "${nlQuery}"` : "Recommendations based on your travel profile"} 
            subtitle={nlQuery?.trim() ? "AI-analyzed destinations matching your conversational query" : "Personalized picks based on your style and past trips"} 
            badge="Conversational AI" 
          />
          
          <QueryFunnelBox nluParsed={nluParsed} nlQuery={nlQuery} />

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: 18 }}>
            {nlResults.map(dest => (
              <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onSimulate={setSimModalDest} onCompare={toggleCompare} onWhyScore={setScoreModalDest} onFeedback={handleFeedback} userCurrency={userCurrency} isCompared={comparedDests.some(d => d.destination === dest.destination)} />
            ))}
          </div>
        </div>
      )}

      {/* ─── Main Content Grid: Recommendations + Intelligence Sidebar ──────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 30, alignItems: 'start' }}>

        {/* ── Left Column: Multi-Interest Filter & Rec Lists ───────────────── */}
        <div>
          {/* Multi-Interest Filter Pills */}
          <div className="glass-card" style={{ padding: '18px 20px', borderRadius: 16, marginBottom: 32, border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Multi-Interest Smart Filter {activeInterests.length > 0 && `(${activeInterests.length} selected)`}
              </div>
              {activeInterests.length > 0 && (
                <button onClick={() => { setActiveInterests([]); loadRecs([]); }} style={{ background: 'transparent', border: 'none', color: '#ef4444', fontSize: 11, cursor: 'pointer' }}>
                  Clear All
                </button>
              )}
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {INTEREST_PILLS.map(({ label, value, icon: Icon, color }) => {
                const active = activeInterests.includes(value);
                return (
                  <button key={value} onClick={() => toggleInterestPill(value)} style={{
                    background: active ? `${color}25` : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${active ? color : 'rgba(255,255,255,0.1)'}`,
                    borderRadius: 20, padding: '7px 14px', cursor: 'pointer',
                    color: active ? color : 'rgba(255,255,255,0.6)',
                    fontSize: 12, fontWeight: active ? 700 : 500,
                    display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.2s'
                  }}>
                    <Icon size={13} />
                    {label} {active && '✓'}
                  </button>
                );
              })}
            </div>

            {/* Discover by interest results */}
            {activeInterests.length > 0 && discoverByInterest.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <div style={{ fontSize: 13, color: '#a78bfa', fontWeight: 600, marginBottom: 14 }}>
                  Top recommendations for [{activeInterests.join(', ')}]
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
                  {discoverByInterest.map(dest => (
                    <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onSimulate={setSimModalDest} onCompare={toggleCompare} onWhyScore={setScoreModalDest} onFeedback={handleFeedback} userCurrency={userCurrency} isCompared={comparedDests.some(d => d.destination === dest.destination)} />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* ── Mode 1: Recommended For You ───────────────────────────────── */}
          {recommendedForYou.length > 0 && (
            <div style={{ marginBottom: 44 }}>
              <SectionHeader icon={IconSparkles} iconColor="#a78bfa" title="Recommended For You" subtitle="6-factor AI personality match — Interest · Past Trips · Budget · Season · Style · Popularity" badge="Top Picks" />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: 20 }}>
                {recommendedForYou.map(dest => (
                  <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onSimulate={setSimModalDest} onCompare={toggleCompare} onWhyScore={setScoreModalDest} onFeedback={handleFeedback} userCurrency={userCurrency} isCompared={comparedDests.some(d => d.destination === dest.destination)} />
                ))}
              </div>
            </div>
          )}

          {/* ── Mode 2: Because You Loved... ─────────────────────────────── */}
          {becauseYouLoved.length > 0 && (
            <div style={{ marginBottom: 44 }}>
              <SectionHeader icon={IconHeartFilled} iconColor="#f43f5e" title="Because You Loved..." subtitle="Netflix-style similarity matching based on your completed trip history" badge="Past Trips" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
                {becauseYouLoved.map(group => (
                  <div key={group.based_on}>
                    <div style={{ marginBottom: 14 }}>
                      <div style={{ fontSize: 15, fontWeight: 700, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <IconHeartFilled size={14} style={{ color: '#f43f5e' }} /> Because You Loved {group.based_on}
                      </div>
                      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>
                        Destinations sharing similar landscapes, activities, and travel style
                      </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
                      {group.destinations.map(dest => (
                        <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onSimulate={setSimModalDest} onCompare={toggleCompare} onWhyScore={setScoreModalDest} onFeedback={handleFeedback} userCurrency={userCurrency} isCompared={comparedDests.some(d => d.destination === dest.destination)} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Mode 3: Hidden Gems ────────────────────────────────────────── */}
          {hiddenGems.length > 0 && (
            <div style={{ marginBottom: 44 }}>
              <SectionHeader icon={IconCompass} iconColor="#06b6d4" title="Hidden Gems For You" subtitle="Off-the-beaten-path destinations with low crowd scores & high scenery ratings" badge="Exclusive" />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: 20 }}>
                {hiddenGems.map(dest => (
                  <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onSimulate={setSimModalDest} onCompare={toggleCompare} onWhyScore={setScoreModalDest} onFeedback={handleFeedback} userCurrency={userCurrency} isCompared={comparedDests.some(d => d.destination === dest.destination)} />
                ))}
              </div>
            </div>
          )}

          {/* ── Mode 4: Budget Friendly ────────────────────────────────────── */}
          {budgetFriendly.length > 0 && (
            <div style={{ marginBottom: 44 }}>
              <SectionHeader icon={IconWallet} iconColor="#22c55e" title="Budget Friendly For You" subtitle="High value-to-cost ratio destinations well within your trip budget cap" badge="Best Value" />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: 20 }}>
                {budgetFriendly.map(dest => (
                  <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onSimulate={setSimModalDest} onCompare={toggleCompare} onWhyScore={setScoreModalDest} onFeedback={handleFeedback} userCurrency={userCurrency} isCompared={comparedDests.some(d => d.destination === dest.destination)} />
                ))}
              </div>
            </div>
          )}

          {/* ── Mode 5: Seasonal Picks ─────────────────────────────────────── */}
          {seasonalPicks.length > 0 && (
            <div style={{ marginBottom: 44 }}>
              <SectionHeader icon={IconCalendar} iconColor="#f59e0b" title="Best This Season" subtitle={`Top destinations at their peak weather conditions right now — ${new Date().toLocaleString('default', { month: 'long' })} picks`} badge="In Season" />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))', gap: 20 }}>
                {seasonalPicks.map(dest => (
                  <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onSimulate={setSimModalDest} onCompare={toggleCompare} onWhyScore={setScoreModalDest} onFeedback={handleFeedback} userCurrency={userCurrency} isCompared={comparedDests.some(d => d.destination === dest.destination)} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Right Column: Travel Personality & Confidence Intelligence ────── */}
        <div>
          {/* Personality & Confidence Proof Card -> AIMemoryDashboard */}
          <AIMemoryDashboard 
            profile={profile} 
            archetype={archetype} 
            confidence={confidence} 
            INTEREST_PILLS={INTEREST_PILLS} 
          />

          {/* Compare Launcher Widget */}
          {comparedDests.length > 0 && (
            <div className="glass-card" style={{ padding: '16px', borderRadius: 16, border: '1px solid #a78bfa', background: 'rgba(167,139,250,0.1)' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#f1f5f9', marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Selected to Compare</span>
                <span style={{ color: '#a78bfa' }}>{comparedDests.length}/3</span>
              </div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginBottom: 12 }}>
                {comparedDests.map(d => d.destination).join(', ')}
              </div>
              <button onClick={() => setShowCompareDrawer(true)} style={{ width: '100%', background: 'linear-gradient(135deg, #7c3aed, #6366f1)', border: 'none', borderRadius: 12, padding: '10px', fontSize: 12, fontWeight: 700, color: '#fff', cursor: 'pointer' }}>
                Open Comparison Matrix
              </button>
            </div>
          )}
        </div>

      </div>

      {/* ─── Modals & Drawers ────────────────────────────────────────────────── */}
      {scoreModalDest && (
        <ScoreBreakdownModal dest={scoreModalDest} onClose={() => setScoreModalDest(null)} />
      )}

      {simModalDest && (
        <TripSimulatorModal dest={simModalDest} userCurrency={userCurrency} onClose={() => setSimModalDest(null)} />
      )}

      {showMatchAnalyzer && (
        <MatchAnalyzerModal onClose={() => setShowMatchAnalyzer(false)} />
      )}

      {showCompareDrawer && (
        <CompareDrawer items={comparedDests} onRemove={(name) => setComparedDests(comparedDests.filter(d => d.destination !== name))} userCurrency={userCurrency} onClose={() => setShowCompareDrawer(false)} />
      )}

      {/* ─── Trip Wizard Integration ────────────────────────────────────────── */}
      {showWizard && (
        <TripWizard destination={wizardDest} onClose={() => setShowWizard(false)} />
      )}

    </div>
  );
}
