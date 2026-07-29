import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconSparkles, IconRefresh, IconBrain, IconCompass,
  IconHeartFilled, IconMapPin, IconStar, IconArrowRight,
  IconWallet, IconCalendar, IconSearch, IconFlame,
  IconLeaf, IconMountain, IconWaveSine, IconBuildingChurch,
  IconCamera, IconMoon, IconChevronRight,
  IconCheck, IconX, IconHeart, IconSend
} from '@tabler/icons-react';
import api from '../api/axios';
import TripWizard from '../components/trips/TripWizard';
import { getBudgetDisplay } from '../utils/currencyFormatter';

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

// ─── Score Bar ──────────────────────────────────────────────────────────────
function ScoreBar({ score, color = '#a78bfa' }) {
  return (
    <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 8, height: 6, width: '100%', overflow: 'hidden', marginTop: 4 }}>
      <div style={{
        height: '100%', width: `${score}%`, borderRadius: 8,
        background: `linear-gradient(90deg, ${color}, #818cf8)`,
        transition: 'width 0.8s cubic-bezier(0.34,1.56,0.64,1)'
      }} />
    </div>
  );
}

// ─── Destination Card ────────────────────────────────────────────────────────
function DestCard({ dest, onPlan, onInteract, userCurrency = 'USD' }) {
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.stopPropagation();
    setSaved(true);
    onInteract && onInteract(dest.destination, 'save');
  };

  const handlePlan = () => {
    onInteract && onInteract(dest.destination, 'click');
    onPlan && onPlan(dest.destination);
  };

  const scoreColor =
    dest.match_score >= 85 ? '#22c55e' :
    dest.match_score >= 70 ? '#f59e0b' : '#60a5fa';

  return (
    <div className="glass-card" style={{
      padding: '20px',
      borderRadius: 16,
      cursor: 'pointer',
      transition: 'transform 0.25s, box-shadow 0.25s',
      position: 'relative',
      overflow: 'hidden',
      border: '1px solid rgba(255,255,255,0.08)',
    }}
    onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-4px)'}
    onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      {/* Score Badge */}
      <div style={{
        position: 'absolute', top: 14, right: 14,
        background: `${scoreColor}22`, border: `1px solid ${scoreColor}55`,
        borderRadius: 20, padding: '4px 10px',
        fontSize: 12, fontWeight: 700, color: scoreColor, display: 'flex', alignItems: 'center', gap: 4
      }}>
        <IconStar size={10} fill={scoreColor} /> {dest.match_score}%
      </div>

      {/* Save button */}
      <button onClick={handleSave} style={{
        position: 'absolute', top: 12, right: 70,
        background: 'transparent', border: 'none', cursor: 'pointer',
        color: saved ? '#f43f5e' : 'rgba(255,255,255,0.4)',
        transition: 'color 0.2s', padding: 4
      }}>
        {saved ? <IconHeartFilled size={16} /> : <IconHeart size={16} />}
      </button>

      <div style={{ marginBottom: 10 }}>
        <div style={{ fontSize: 17, fontWeight: 700, color: '#f1f5f9', marginBottom: 2 }}>
          {dest.destination}
        </div>
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', display: 'flex', alignItems: 'center', gap: 4 }}>
          <IconMapPin size={11} /> {dest.country} &nbsp;·&nbsp; {dest.travel_style}
        </div>
      </div>

      {/* Categories */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 12 }}>
        {(dest.categories || []).slice(0, 3).map(c => (
          <span key={c} style={{
            background: 'rgba(167,139,250,0.12)', border: '1px solid rgba(167,139,250,0.2)',
            borderRadius: 20, padding: '2px 8px', fontSize: 11, color: '#c4b5fd'
          }}>{c}</span>
        ))}
        {dest.best_months && dest.best_months[0] && (
          <span style={{
            background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)',
            borderRadius: 20, padding: '2px 8px', fontSize: 11, color: '#86efac'
          }}>
            <IconCalendar size={9} style={{ marginRight: 3 }} />
            {dest.best_months[0]}
          </span>
        )}
      </div>

      {/* Match Score bar */}
      <ScoreBar score={dest.match_score} color={scoreColor} />
      <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 4, marginBottom: 12 }}>
        AI Match Score
      </div>

      {/* Reasons */}
      {dest.reasons && dest.reasons.length > 0 && (
        <div style={{
          background: 'rgba(167,139,250,0.07)', borderRadius: 10,
          padding: '10px 12px', marginBottom: 14
        }}>
          <div style={{ fontSize: 11, color: '#a78bfa', fontWeight: 600, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 5 }}>
            <IconBrain size={11} /> Why this destination?
          </div>
          {dest.reasons.slice(0, 2).map((r, i) => (
            <div key={i} style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)', display: 'flex', gap: 6, marginBottom: 3 }}>
              <IconCheck size={10} style={{ color: '#22c55e', flexShrink: 0, marginTop: 2 }} /> {r}
            </div>
          ))}
        </div>
      )}

      {/* Budget + Plan button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 13, color: '#a78bfa', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 5 }}>
          <IconWallet size={13} />
          {getBudgetDisplay(dest.budget, userCurrency)}
        </div>
        <button onClick={handlePlan} style={{
          background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
          border: 'none', borderRadius: 20, padding: '7px 16px',
          fontSize: 12, fontWeight: 600, color: '#fff', cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 5,
          transition: 'opacity 0.2s'
        }}>
          Plan Trip <IconArrowRight size={12} />
        </button>
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
          {subtitle && <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>{subtitle}</div>}
        </div>
      </div>
    </div>
  );
}

// ─── Profile Radar ───────────────────────────────────────────────────────────
function ProfileRadar({ profile }) {
  const interests = [
    { key: 'nature', label: 'Nature', color: '#22c55e' },
    { key: 'adventure', label: 'Adventure', color: '#f97316' },
    { key: 'culture', label: 'Culture', color: '#a855f7' },
    { key: 'food', label: 'Food', color: '#ec4899' },
    { key: 'beach', label: 'Beach', color: '#06b6d4' },
    { key: 'history', label: 'History', color: '#eab308' },
    { key: 'nightlife', label: 'Nightlife', color: '#6366f1' },
  ];

  return (
    <div className="glass-card" style={{ padding: '20px', borderRadius: 16, border: '1px solid rgba(255,255,255,0.08)' }}>
      <div style={{ fontSize: 13, color: '#a78bfa', fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 6 }}>
        <IconBrain size={14} /> Your Travel Personality
      </div>
      {interests.map(({ key, label, color }) => (
        <div key={key} style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)' }}>{label}</span>
            <span style={{ fontSize: 12, fontWeight: 700, color }}>{profile[key] ?? 65}%</span>
          </div>
          <ScoreBar score={profile[key] ?? 65} color={color} />
        </div>
      ))}
      {profile.average_budget && (
        <div style={{ marginTop: 16, padding: '12px', background: 'rgba(167,139,250,0.08)', borderRadius: 10 }}>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginBottom: 2 }}>Avg. Trip Budget</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#a78bfa' }}>
            {getBudgetDisplay({ amount: profile.average_budget, base_currency: 'USD', user_currency: 'USD', converted_amount: profile.average_budget, formatted: '' })}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────
export default function AISuggestions() {
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [activeInterest, setActiveInterest] = useState(null);
  const [nlQuery, setNlQuery] = useState('');
  const [showNlInput, setShowNlInput] = useState(false);
  const [nlLoading, setNlLoading] = useState(false);

  const [showWizard, setShowWizard] = useState(false);
  const [wizardDest, setWizardDest] = useState('');

  // ─── Load recommendations ────────────────────────────────────────────────
  const loadRecs = useCallback(async (interest = null, query = null) => {
    try {
      const params = {};
      if (interest) params.interest = interest;
      if (query) params.query = query;

      const res = await api.get('/api/ai/recommendations', { params });
      setData(res.data);
    } catch (err) {
      console.error('Recommendations failed:', err);
      setData(null);
    }
    setLoading(false);
    setRefreshing(false);
    setNlLoading(false);
  }, []);

  useEffect(() => {
    loadRecs();
  }, [loadRecs]);

  const handleInterestPill = (interest) => {
    const newVal = activeInterest === interest ? null : interest;
    setActiveInterest(newVal);
    setRefreshing(true);
    loadRecs(newVal);
  };

  const handleNlQuery = () => {
    if (!nlQuery.trim()) return;
    setNlLoading(true);
    loadRecs(null, nlQuery.trim());
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadRecs(activeInterest);
  };

  // ─── Interaction tracking ────────────────────────────────────────────────
  const handleInteract = async (destination, action) => {
    try {
      await api.post('/api/ai/recommendations/interact', { destination, action, match_score: 85 });
    } catch (_) {}
  };

  const handlePlan = (destination) => {
    setWizardDest(destination);
    setShowWizard(true);
  };

  // ─── Helpers ─────────────────────────────────────────────────────────────
  const profile = data?.user_profile || {};
  const userCurrency = data?.user_currency || 'USD';
  const recommendedForYou = data?.recommended_for_you || [];
  const becauseYouLoved = data?.because_you_loved || [];
  const budgetFriendly = data?.budget_friendly || [];
  const seasonalPicks = data?.seasonal_picks || [];
  const discoverByInterest = data?.discover_by_interest || [];
  const nlResults = data?.nl_query_results || [];
  const visited = profile.visited_destinations || [];

  // ─── Loading ─────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 20 }}>
        <div style={{ fontSize: 40 }}>✨</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9' }}>Building Your Travel Intelligence...</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)' }}>Analyzing your interests, past trips, budget & season</div>
        <div className="loading-spinner" style={{
          width: 40, height: 40, borderRadius: '50%',
          border: '3px solid rgba(167,139,250,0.2)',
          borderTopColor: '#a78bfa', animation: 'spin 0.8s linear infinite'
        }} />
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', padding: '24px 24px 60px' }}>

      {/* ── Page Header ─────────────────────────────────────────────────────── */}
      <div style={{ maxWidth: 1300, margin: '0 auto' }}>
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
          marginBottom: 28, flexWrap: 'wrap', gap: 16
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
              <div style={{
                background: 'linear-gradient(135deg, #7c3aed20, #6366f120)',
                border: '1px solid rgba(167,139,250,0.25)', borderRadius: 12, padding: '10px'
              }}>
                <IconSparkles size={22} style={{ color: '#a78bfa' }} />
              </div>
              <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: '#f1f5f9' }}>
                AI Travel Intelligence
              </h1>
              <span style={{
                background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
                borderRadius: 20, padding: '3px 12px', fontSize: 12, fontWeight: 700, color: '#fff'
              }}>v2.7</span>
            </div>
            <p style={{ margin: 0, fontSize: 14, color: 'rgba(255,255,255,0.4)' }}>
              Personalized recommendations powered by your travel personality, past trips, budget & season
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={() => setShowNlInput(v => !v)} style={{
              background: showNlInput ? 'rgba(167,139,250,0.2)' : 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(167,139,250,0.3)', borderRadius: 10, padding: '9px 16px',
              fontSize: 13, fontWeight: 600, color: '#a78bfa', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6
            }}>
              <IconSearch size={14} /> AI Query
            </button>
            <button onClick={handleRefresh} disabled={refreshing} style={{
              background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 10, padding: '9px 16px', fontSize: 13, fontWeight: 600,
              color: 'rgba(255,255,255,0.6)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6
            }}>
              <IconRefresh size={14} style={{ animation: refreshing ? 'spin 0.8s linear infinite' : 'none' }} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* ── Natural Language Query Bar ───────────────────────────────────── */}
        {showNlInput && (
          <div className="glass-card" style={{
            padding: '18px 20px', borderRadius: 14, marginBottom: 24,
            border: '1px solid rgba(167,139,250,0.25)',
            background: 'rgba(124,58,237,0.08)'
          }}>
            <div style={{ fontSize: 13, color: '#a78bfa', fontWeight: 600, marginBottom: 10, display: 'flex', gap: 6, alignItems: 'center' }}>
              <IconBrain size={14} /> Ask AI about destinations
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <input
                value={nlQuery}
                onChange={e => setNlQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleNlQuery()}
                placeholder="e.g. I loved Meghalaya, suggest similar places... or Beach places under $500..."
                style={{
                  flex: 1, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 10, padding: '10px 16px', color: '#f1f5f9', fontSize: 13,
                  outline: 'none'
                }}
              />
              <button onClick={handleNlQuery} disabled={nlLoading || !nlQuery.trim()} style={{
                background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
                border: 'none', borderRadius: 10, padding: '10px 18px',
                color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
                fontSize: 13, fontWeight: 600, opacity: nlLoading ? 0.6 : 1
              }}>
                <IconSend size={13} /> {nlLoading ? 'Thinking...' : 'Ask AI'}
              </button>
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 8 }}>
              Try: "Hidden gems in North India" · "Budget beach destinations" · "Like Japan but cheaper"
            </div>
          </div>
        )}

        {/* ── NL Query Results ─────────────────────────────────────────────── */}
        {nlResults.length > 0 && (
          <div style={{ marginBottom: 40 }}>
            <SectionHeader
              icon={IconBrain}
              iconColor="#a78bfa"
              title={`Results for "${nlQuery}"`}
              subtitle="AI-analyzed destinations matching your natural language query"
              badge="AI Query"
            />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
              {nlResults.map(dest => (
                <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onInteract={handleInteract} userCurrency={userCurrency} />
              ))}
            </div>
          </div>
        )}

        {/* ── Main Layout: Content + Profile Sidebar ───────────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 28, alignItems: 'start' }}>

          {/* ── Left Column: All Recommendation Sections ─────────────────── */}
          <div>

            {/* Interest Filter Pills */}
            <div className="glass-card" style={{
              padding: '16px 20px', borderRadius: 14, marginBottom: 32,
              border: '1px solid rgba(255,255,255,0.07)'
            }}>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginBottom: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Discover By Interest
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {INTEREST_PILLS.map(({ label, value, icon: Icon, color }) => {
                  const active = activeInterest === value;
                  return (
                    <button key={value} onClick={() => handleInterestPill(value)} style={{
                      background: active ? `${color}20` : 'rgba(255,255,255,0.04)',
                      border: `1px solid ${active ? color + '60' : 'rgba(255,255,255,0.1)'}`,
                      borderRadius: 20, padding: '7px 14px', cursor: 'pointer',
                      color: active ? color : 'rgba(255,255,255,0.5)',
                      fontSize: 12, fontWeight: active ? 700 : 500,
                      display: 'flex', alignItems: 'center', gap: 5,
                      transition: 'all 0.2s'
                    }}>
                      <Icon size={12} />
                      {label}
                    </button>
                  );
                })}
                {activeInterest && (
                  <button onClick={() => handleInterestPill(null)} style={{
                    background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 20, padding: '7px 12px', cursor: 'pointer',
                    color: 'rgba(255,255,255,0.3)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4
                  }}>
                    <IconX size={11} /> Clear
                  </button>
                )}
              </div>

              {/* Discover by interest results */}
              {activeInterest && discoverByInterest.length > 0 && (
                <div style={{ marginTop: 20 }}>
                  <div style={{ fontSize: 13, color: '#a78bfa', fontWeight: 600, marginBottom: 14, textTransform: 'capitalize' }}>
                    Top {activeInterest} destinations for you
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 14 }}>
                    {discoverByInterest.map(dest => (
                      <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onInteract={handleInteract} userCurrency={userCurrency} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* ── Section 1: Recommended For You ───────────────────────────── */}
            {recommendedForYou.length > 0 && (
              <div style={{ marginBottom: 40 }}>
                <SectionHeader
                  icon={IconSparkles}
                  iconColor="#a78bfa"
                  title="Recommended For You"
                  subtitle="6-factor AI personality match — Interest · Past Trips · Budget · Season · Style · Popularity"
                  badge="Top Picks"
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
                  {recommendedForYou.map(dest => (
                    <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onInteract={handleInteract} userCurrency={userCurrency} />
                  ))}
                </div>
              </div>
            )}

            {/* ── Section 2: Because You Loved ─────────────────────────────── */}
            {becauseYouLoved.length > 0 && (
              <div style={{ marginBottom: 40 }}>
                <SectionHeader
                  icon={IconHeartFilled}
                  iconColor="#f43f5e"
                  title="Because You Loved..."
                  subtitle="Netflix-style similarity matching based on your completed trips"
                  badge="Past Trips"
                />
                <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
                  {becauseYouLoved.map(group => (
                    <div key={group.based_on}>
                      <div style={{ marginBottom: 14 }}>
                        <div style={{ fontSize: 15, fontWeight: 700, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: 8 }}>
                          <IconHeartFilled size={14} style={{ color: '#f43f5e' }} />
                          Because You Loved {group.based_on}
                        </div>
                        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', marginTop: 3 }}>
                          Destinations with similar landscape, style & activities
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 14 }}>
                        {group.destinations.map(dest => (
                          <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onInteract={handleInteract} userCurrency={userCurrency} />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── Section 3: Budget Friendly ────────────────────────────────── */}
            {budgetFriendly.length > 0 && (
              <div style={{ marginBottom: 40 }}>
                <SectionHeader
                  icon={IconWallet}
                  iconColor="#22c55e"
                  title="Budget Friendly For You"
                  subtitle="Well within your average trip budget — high value, low cost"
                  badge="Best Value"
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
                  {budgetFriendly.map(dest => (
                    <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onInteract={handleInteract} userCurrency={userCurrency} />
                  ))}
                </div>
              </div>
            )}

            {/* ── Section 4: Seasonal Picks ─────────────────────────────────── */}
            {seasonalPicks.length > 0 && (
              <div style={{ marginBottom: 40 }}>
                <SectionHeader
                  icon={IconCalendar}
                  iconColor="#f59e0b"
                  title="Best This Season"
                  subtitle={`Top destinations at their peak right now — ${new Date().toLocaleString('default', { month: 'long' })} picks`}
                  badge="In Season"
                />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
                  {seasonalPicks.map(dest => (
                    <DestCard key={dest.destination} dest={dest} onPlan={handlePlan} onInteract={handleInteract} userCurrency={userCurrency} />
                  ))}
                </div>
              </div>
            )}

            {/* ── Section 5: Future AI Modules ─────────────────────────────── */}
            <div style={{ marginBottom: 20 }}>
              <SectionHeader
                icon={IconFlame}
                iconColor="#f97316"
                title="Future AI Modules"
                subtitle="Upcoming features powered by machine learning — coming in WanderWise v3.0"
                badge="Coming Soon"
              />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 14 }}>
                {[
                  { icon: '🎯', title: 'Crowd Prediction Engine', desc: 'AI-predicted crowd levels for your travel dates using historical data' },
                  { icon: '✈️', title: 'Flight Price Prediction', desc: 'Best time to book your flight for maximum savings' },
                  { icon: '🧬', title: 'Travel Personality Evolution', desc: 'How your travel style changes season to season' },
                  { icon: '💎', title: 'Hidden Gem Discovery', desc: 'AI-curated off-the-beaten-path destinations personalized to you' },
                  { icon: '🧠', title: 'AI Travel Memory', desc: 'Learns from every trip to make increasingly accurate predictions' },
                  { icon: '🤝', title: 'Collaborative Recommendations', desc: '"Travelers like you also loved..." powered by collaborative filtering' },
                ].map(m => (
                  <div key={m.title} className="glass-card" style={{
                    padding: '16px', borderRadius: 14, border: '1px solid rgba(255,255,255,0.06)',
                    opacity: 0.75
                  }}>
                    <div style={{ fontSize: 22, marginBottom: 8 }}>{m.icon}</div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#f1f5f9', marginBottom: 4 }}>{m.title}</div>
                    <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', lineHeight: 1.5 }}>{m.desc}</div>
                    <div style={{
                      marginTop: 12, fontSize: 10, fontWeight: 700, color: '#f97316',
                      background: 'rgba(249,115,22,0.1)', border: '1px solid rgba(249,115,22,0.2)',
                      borderRadius: 20, padding: '3px 10px', display: 'inline-block'
                    }}>v3.0 ML</div>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* ── Right Sidebar: Travel Personality Profile ─────────────────── */}
          <div style={{ position: 'sticky', top: 24 }}>
            <ProfileRadar profile={profile} />

            {/* Visited destinations */}
            {visited.length > 0 && (
              <div className="glass-card" style={{
                padding: '18px', borderRadius: 14, marginTop: 16,
                border: '1px solid rgba(255,255,255,0.07)'
              }}>
                <div style={{ fontSize: 12, color: '#a78bfa', fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <IconMapPin size={12} /> Your Journey So Far
                </div>
                {visited.map(v => (
                  <div key={v} style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '7px 0',
                    borderBottom: '1px solid rgba(255,255,255,0.05)'
                  }}>
                    <IconCheck size={12} style={{ color: '#22c55e' }} />
                    <span style={{ fontSize: 13, color: '#f1f5f9' }}>{v}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Quick Actions */}
            <div className="glass-card" style={{
              padding: '18px', borderRadius: 14, marginTop: 16,
              border: '1px solid rgba(255,255,255,0.07)'
            }}>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', fontWeight: 700, marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Quick Actions
              </div>
              {[
                { label: 'My Trips', icon: IconCompass, path: '/trips' },
                { label: 'AI Chat Assistant', icon: IconBrain, path: '/chat' },
                { label: 'Expense Tracker', icon: IconWallet, path: '/expenses' },
              ].map(({ label, icon: Icon, path }) => (
                <button key={path} onClick={() => navigate(path)} style={{
                  width: '100%', background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10,
                  padding: '10px 14px', cursor: 'pointer', color: '#f1f5f9',
                  fontSize: 13, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  marginBottom: 8, transition: 'background 0.2s'
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(167,139,250,0.08)'}
                onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Icon size={14} style={{ color: '#a78bfa' }} /> {label}
                  </span>
                  <IconChevronRight size={12} style={{ color: 'rgba(255,255,255,0.3)' }} />
                </button>
              ))}
            </div>
          </div>

        </div>
      </div>

      {/* ── Trip Wizard Modal ─────────────────────────────────────────────── */}
      {showWizard && (
        <TripWizard
          initialDestination={wizardDest}
          onClose={() => setShowWizard(false)}
          onSuccess={() => { setShowWizard(false); navigate('/trips'); }}
        />
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
