import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '2rem' }}>
      
      {/* Header Pill */}
      <div className="glass-card" style={{ padding: '8px 16px', borderRadius: '30px', display: 'inline-flex', alignItems: 'center', gap: '8px', marginBottom: '2rem' }}>
        <span style={{ fontSize: '12px', fontWeight: 700, color: '#185FA5', background: 'rgba(24, 95, 165, 0.1)', padding: '2px 8px', borderRadius: '12px' }}>NEW</span>
        <span className="text-secondary" style={{ fontSize: '13px', fontWeight: 500 }}>Meet your personal AI Travel Companion</span>
      </div>

      {/* Hero Title */}
      <h1 className="text-primary-dark" style={{ fontSize: '4.5rem', fontWeight: 800, lineHeight: 1.1, marginBottom: '1.5rem', letterSpacing: '-1px', maxWidth: '800px' }}>
        Travel smarter with <br />
        <span style={{ color: '#185FA5' }}>WanderWise</span>
      </h1>

      {/* Hero Subtitle */}
      <p className="text-secondary" style={{ fontSize: '1.1rem', lineHeight: 1.6, maxWidth: '600px', marginBottom: '3rem' }}>
        Your intelligent travel companion that helps you plan, navigate, and experience the world with AI-powered insights, personalized itineraries, and real-time assistance.
      </p>

      {/* CTA Buttons */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '3rem' }}>
        <Link to="/register" style={{ textDecoration: 'none' }}>
          <button style={{
            background: '#185FA5',
            color: 'white',
            border: 'none',
            padding: '14px 28px',
            borderRadius: '10px',
            fontSize: '15px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: '0 4px 14px rgba(24, 95, 165, 0.2)'
          }}
          onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(24, 95, 165, 0.3)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 14px rgba(24, 95, 165, 0.2)'; }}
          >
            Start Planning Free
          </button>
        </Link>
        <Link to="/login" style={{ textDecoration: 'none' }}>
          <button style={{
            background: 'rgba(24, 95, 165, 0.05)',
            color: '#185FA5',
            border: '1px solid rgba(24, 95, 165, 0.2)',
            padding: '14px 28px',
            borderRadius: '10px',
            fontSize: '15px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(24, 95, 165, 0.1)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(24, 95, 165, 0.05)'; }}
          >
            Sign In
          </button>
        </Link>
      </div>

      {/* Daily Check-In Widget (v2 Feature) */}
      <div className="glass-card" style={{ padding: '1.5rem 2rem', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '2rem', background: 'linear-gradient(135deg, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0.1) 100%)', border: '1px solid rgba(255,255,255,0.4)', boxShadow: '0 8px 32px rgba(0,0,0,0.05)', backdropFilter: 'blur(10px)' }}>
        <div>
          <h3 className="text-primary-dark" style={{ margin: '0 0 0.5rem 0', fontSize: '1.2rem' }}>How are you feeling today?</h3>
          <p className="text-secondary" style={{ margin: 0, fontSize: '0.9rem' }}>We'll adjust your itinerary to match your energy.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          {['⚡ Energetic', '🥱 Tired', '🤯 Overwhelmed', '🧭 Adventurous'].map(mood => (
            <button key={mood} style={{ padding: '8px 16px', borderRadius: '20px', border: '1px solid #185FA5', background: 'transparent', color: '#185FA5', cursor: 'pointer', transition: 'all 0.2s', fontWeight: 500 }} onMouseEnter={(e) => { e.currentTarget.style.background = '#185FA5'; e.currentTarget.style.color = '#fff'; }} onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#185FA5'; }}>
              {mood}
            </button>
          ))}
        </div>
      </div>

      {/* Feature Grid Mockup (Glass Cards) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginTop: '5rem', maxWidth: '1000px', width: '100%' }}>
        {[
          { icon: '🤖', title: 'AI Itineraries', desc: 'Personalized day-by-day plans crafted by AI.' },
          { icon: '🛡️', title: 'Safety Hub', desc: 'Real-time risk scores and scam alerts.' },
          { icon: '💰', title: 'Smart Budgeting', desc: 'Track expenses and manage your money easily.' }
        ].map((feat, i) => (
          <div key={i} className="glass-card" style={{ padding: '2rem', textAlign: 'left' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>{feat.icon}</div>
            <h3 className="text-primary-dark" style={{ margin: '0 0 0.5rem', fontSize: '1.2rem' }}>{feat.title}</h3>
            <p className="text-secondary" style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.5 }}>{feat.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
