import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { formatCurrency } from '../utils/formatters';

const API = 'http://localhost:8000/api';
const CURRENCIES = ['USD', 'INR', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD'];
const TRAVEL_TYPES = ['leisure', 'adventure', 'business', 'family'];

// --- Sub-Components for Widgets ---

const WMO_ICONS = {
  0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
  45: '🌫️', 48: '🌫️',
  51: '🌦️', 53: '🌧️', 55: '🌧️',
  61: '🌧️', 63: '🌧️', 65: '🌊',
  71: '❄️', 73: '❄️', 75: '🌨️',
  80: '🌦️', 81: '⛈️', 82: '⛈️',
  95: '⛈️', 96: '⛈️', 99: '⛈️',
};

function WeatherWidget({ trip }) {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!trip) { setLoading(false); return; }
    const dest = trip.destination.split(',')[0];
    const cacheKey = `weather_dash_${dest}`;

    // Show cached instantly
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        // only use cache if less than 30 minutes old
        if (Date.now() - parsed._ts < 30 * 60 * 1000) {
          setWeather(parsed); setLoading(false);
        }
      } catch (_) {}
    }

    fetch(`${API}/weather/${encodeURIComponent(dest)}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data && data.current) {
          data._ts = Date.now();
          setWeather(data);
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [trip]);

  if (!trip) return null;

  if (loading) return (
    <div className="glass-card" style={{ padding: '20px' }}>
      <div style={{ fontSize: '13px', color: '#5a7a9a', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⏳</span> Loading weather...
      </div>
    </div>
  );

  if (!weather || !weather.current) return (
    <div className="glass-card" style={{ padding: '20px' }}>
      <div style={{ fontSize: '13px', color: '#5a7a9a' }}>☁️ Weather unavailable for {trip.destination.split(',')[0]}</div>
    </div>
  );

  const cur = weather.current;
  const icon = WMO_ICONS[cur.weather_code] || '🌡️';
  const today = weather.forecast?.[0];

  return (
    <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3 className="text-primary-dark" style={{ margin: '0 0 2px', fontSize: '15px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
            ☁️ Live Weather
          </h3>
          <div style={{ fontSize: '11px', color: '#5a7a9a', fontWeight: 600 }}>{weather.city}, {weather.country}</div>
        </div>
        <span style={{ fontSize: '2.4rem', lineHeight: 1 }}>{icon}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px' }}>
        <div style={{ fontSize: '3rem', fontWeight: 900, color: '#185FA5', lineHeight: 1 }}>{cur.temperature?.toFixed(0)}°C</div>
        <div style={{ paddingBottom: '4px' }}>
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#1a2a3a' }}>{cur.description}</div>
          <div style={{ fontSize: '11px', color: '#5a7a9a' }}>Feels {cur.feels_like?.toFixed(0)}°C</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
        {[
          { icon: '💧', label: 'Humidity', val: `${cur.humidity}%` },
          { icon: '💨', label: 'Wind', val: `${cur.wind_speed?.toFixed(0)} km/h` },
          { icon: '🌧️', label: 'Precip', val: `${cur.precipitation ?? 0} mm` },
        ].map(({ icon, label, val }) => (
          <div key={label} style={{ background: 'rgba(24,95,165,0.05)', borderRadius: '8px', padding: '8px', textAlign: 'center' }}>
            <div style={{ fontSize: '14px' }}>{icon}</div>
            <div style={{ fontSize: '10px', color: '#5a7a9a', fontWeight: 600, textTransform: 'uppercase', margin: '2px 0' }}>{label}</div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#1a2a3a' }}>{val}</div>
          </div>
        ))}
      </div>

      {/* Mini 3-day forecast */}
      {weather.forecast && (
        <div style={{ display: 'flex', gap: '6px' }}>
          {weather.forecast.slice(0, 3).map((day, i) => (
            <div key={i} style={{ flex: 1, textAlign: 'center', padding: '8px 4px', background: 'rgba(255,255,255,0.6)', border: '1px solid rgba(200,225,245,0.6)', borderRadius: '8px' }}>
              <div style={{ fontSize: '10px', color: '#5a7a9a', fontWeight: 600, marginBottom: '4px' }}>
                {i === 0 ? 'Today' : new Date(day.date + 'T12:00:00').toLocaleDateString('en', { weekday: 'short' })}
              </div>
              <div style={{ fontSize: '16px' }}>{WMO_ICONS[day.weather_code] || '🌡️'}</div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#1a2a3a', marginTop: '4px' }}>{day.max_temp?.toFixed(0)}°</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


function RiskAnalyzerWidget({ trip, token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!trip) return;
    const fetchRisk = async () => {
      try {
        const dest = trip.destination.split(',')[0];
        const res = await fetch(`${API}/safety/risk-score`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ destination: dest, travel_dates: `${trip.start_date} to ${trip.end_date}`, budget: trip.budget || 1000 })
        });
        setData(await res.json());
      } catch (e) {}
      setLoading(false);
    };
    fetchRisk();
  }, [trip, token]);

  if (!trip) return null;
  if (loading) return <div className="glass-card" style={{ padding: '16px' }}><p className="text-secondary" style={{ fontSize: '13px', margin: 0 }}>Analyzing risks...</p></div>;
  if (!data || data.overall_score === undefined) return null;

  return (
    <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 className="text-primary-dark" style={{ margin: 0, fontSize: '16px' }}>🛡️ Risk Analyzer</h3>
        <span style={{ fontSize: '12px', fontWeight: 700, padding: '4px 8px', borderRadius: '12px', background: data.overall_score > 70 ? 'rgba(220, 38, 38, 0.1)' : 'rgba(22, 163, 74, 0.1)', color: data.overall_score > 70 ? '#dc2626' : '#16a34a' }}>
          {data.overall_label || `${data.overall_score}% Risk`}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
        {[
          { label: 'Weather', val: data.weather_risk },
          { label: 'Crowd', val: data.crowd_risk },
          { label: 'Safety', val: data.safety_risk },
        ].map((r, i) => (
          <div key={i} style={{ border: '1px solid rgba(200, 225, 245, 0.5)', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#5a7a9a', textTransform: 'uppercase', fontWeight: 600 }}>{r.label}</div>
            <div style={{ fontSize: '16px', fontWeight: 800, color: '#1a2a3a', marginTop: '4px' }}>{r.val || 0}%</div>
          </div>
        ))}
      </div>

      <div>
        <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: '#dc2626' }}>🚨 Emergency Contacts</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          {Object.entries(data.emergency_numbers || {}).slice(0, 4).map(([k, v]) => (
            <div key={k} style={{ fontSize: '12px', background: 'rgba(220, 38, 38, 0.05)', padding: '6px', borderRadius: '4px', display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#4a6080', textTransform: 'capitalize' }}>{k.replace('_', ' ')}:</span>
              <strong style={{ color: '#dc2626' }}>{v}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function LanguageWidget({ trip, token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [spokenText, setSpokenText] = useState("");
  const [translation, setTranslation] = useState("");

  useEffect(() => {
    if (!trip) return;
    const dest = trip.destination.split(',')[0];
    const cacheKey = `lang_guide_${dest}`;

    // Load from cache instantly
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try { setData(JSON.parse(cached)); setLoading(false); } catch (_) {}
    }

    const fetchLang = async () => {
      try {
        const res = await fetch(`${API}/recommendations/language-guide`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ destination: dest })
        });
        if (res.ok) {
          const json = await res.json();
          if (json && json.hello) {
            setData(json);
            localStorage.setItem(cacheKey, JSON.stringify(json));
          }
        }
      } catch (e) {}
      setLoading(false);
    };
    fetchLang();
  }, [trip, token]);

  const speak = (text) => {
    if ('speechSynthesis' in window) {
      const msg = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.speak(msg);
    } else {
      alert("Text-to-speech not supported in this browser.");
    }
  };

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech Recognition is not supported in this browser.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setSpokenText("Listening...");
      setTranslation("");
    };

    recognition.onresult = async (event) => {
      const text = event.results[0][0].transcript;
      setSpokenText(text);
      
      // Call translation API
      try {
        const dest = trip.destination.split(',')[0];
        setTranslation("Translating...");
        const res = await fetch(`${API}/recommendations/translate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ text, destination: dest })
        });
        const transData = await res.json();
        setTranslation(transData.translated);
        speak(transData.translated);
      } catch (e) {
        setTranslation("Translation failed.");
      }
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      setSpokenText("Error processing voice.");
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  if (!trip) return null;
  if (loading) return <div className="glass-card" style={{ padding: '16px' }}><p className="text-secondary" style={{ fontSize: '13px', margin: 0 }}>Loading language guide...</p></div>;
  if (!data || !data.hello) return null;

  const phrases = [
    { label: 'Hello', val: data.hello },
    { label: 'Thank You', val: data.thank_you },
    { label: 'Help', val: data.help },
    { label: 'How much?', val: data.how_much }
  ];

  return (
    <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 className="text-primary-dark" style={{ margin: 0, fontSize: '16px' }}>🗣️ Language Guide</h3>
        <div style={{ fontSize: '10px', color: '#185FA5', fontWeight: 700, background: 'rgba(24, 95, 165, 0.1)', padding: '4px 8px', borderRadius: '12px' }}>
          {data.primary_language}
        </div>
      </div>
      
      {/* Real-Time Translation Section */}
      <div style={{ background: isListening ? 'rgba(220, 38, 38, 0.05)' : 'rgba(24, 95, 165, 0.05)', border: `1px solid ${isListening ? '#dc2626' : '#c8dff0'}`, padding: '12px', borderRadius: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#1a2a3a' }}>Real-Time Translate</span>
          <button 
            onClick={startListening} 
            disabled={isListening}
            style={{ background: isListening ? '#dc2626' : '#185FA5', color: 'white', border: 'none', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: isListening ? 'not-allowed' : 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
            title="Speak to translate"
          >
            🎙️
          </button>
        </div>
        {(spokenText || translation) && (
          <div style={{ fontSize: '12px' }}>
            <div style={{ color: '#5a7a9a', fontStyle: 'italic', marginBottom: '4px' }}>"{spokenText}"</div>
            {translation && <div style={{ color: '#185FA5', fontWeight: 700 }}>{translation}</div>}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {phrases.map((p, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(200, 225, 245, 0.5)', paddingBottom: '6px' }}>
            <div>
              <div style={{ fontSize: '11px', color: '#5a7a9a' }}>{p.label}</div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#1a2a3a' }}>{p.val}</div>
            </div>
            <button onClick={() => speak(p.val)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '18px', opacity: 0.8 }} title="Listen">🔊</button>
          </div>
        ))}
      </div>
      <div style={{ fontSize: '11px', color: '#4a6080', fontStyle: 'italic' }}>"{data.cultural_tip}"</div>
    </div>
  );
}

function PersonalizedWidget({ trips, token }) {
  const [recs, setRecs] = useState([]);
  const [photos, setPhotos] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!trips || trips.length === 0) { setLoading(false); return; }
    const dests = trips.map(t => (t.destination || '').split(',')[0]).filter(Boolean);
    const cacheKey = `personalized_${dests.join('_')}`;

    // Load from cache instantly
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try { setRecs(JSON.parse(cached)); setLoading(false); } catch (_) {}
    }

    const fetchRecs = async () => {
      try {
        const res = await fetch(`${API}/recommendations/personalized`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ past_destinations: dests })
        });
        if (res.ok) {
          const data = await res.json();
          const list = data.recommendations || [];
          if (list.length > 0) {
            setRecs(list);
            localStorage.setItem(cacheKey, JSON.stringify(list));
          }
        }
      } catch (e) {}
      setLoading(false);
    };
    fetchRecs();
  }, [trips, token]);

  // Fetch Wikipedia images for each recommendation
  useEffect(() => {
    if (!recs.length) return;
    recs.forEach(async (r) => {
      if (!r.destination || photos[r.destination]) return;
      try {
        const res = await fetch(
          `https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=thumbnail&pithumbsize=400&titles=${encodeURIComponent(r.destination)}&origin=*`
        );
        const data = await res.json();
        const pages = data.query?.pages || {};
        const page = Object.values(pages)[0];
        if (page?.thumbnail?.source) {
          setPhotos(prev => ({ ...prev, [r.destination]: page.thumbnail.source }));
        }
      } catch (_) {}
    });
  }, [recs]);

  if (loading) return <div className="glass-card" style={{ padding: '16px' }}><p className="text-secondary" style={{ fontSize: '13px', margin: 0 }}>Finding your next adventure...</p></div>;
  if (!recs || recs.length === 0) return null;

  return (
    <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <h3 className="text-primary-dark" style={{ margin: 0, fontSize: '16px' }}>✨ Recommended For You</h3>
      <p className="text-secondary" style={{ fontSize: '11px', margin: '0 0 4px' }}>Based on your travel history</p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {recs.slice(0, 3).map((r, i) => (
          <div key={i} style={{ background: 'rgba(255,255,255,0.7)', border: '1px solid #c8dff0', borderRadius: '10px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {/* Destination Image */}
            <div style={{ height: '80px', background: 'linear-gradient(135deg, #185FA5 0%, #2a8fda 100%)', position: 'relative', overflow: 'hidden' }}>
              {photos[r.destination] && (
                <img
                  src={photos[r.destination]}
                  alt={r.destination}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  onError={e => { e.target.style.display = 'none'; }}
                />
              )}
              <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(0,0,0,0.5) 0%, transparent 60%)' }} />
              <div style={{ position: 'absolute', bottom: '6px', left: '10px', right: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div style={{ fontSize: '13px', fontWeight: 800, color: 'white', textShadow: '0 1px 3px rgba(0,0,0,0.5)' }}>{r.destination}</div>
                <span style={{ fontSize: '9px', background: 'rgba(255,255,255,0.2)', color: 'white', backdropFilter: 'blur(4px)', padding: '2px 6px', borderRadius: '8px', fontWeight: 600 }}>{r.vibe}</span>
              </div>
            </div>
            {/* Description */}
            <div style={{ padding: '8px 10px', fontSize: '11px', color: '#4a6080', lineHeight: 1.4 }}>{r.reason}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function QuickCurrencyWidget({ token }) {
  const [from, setFrom] = useState('USD');
  const [to, setTo] = useState('EUR');
  const [amount, setAmount] = useState('100');
  const [result, setResult] = useState(null);

  const convert = async () => {
    if (!amount) return;
    try {
      const res = await fetch(`${API}/currency/convert?from_curr=${from}&to_curr=${to}&amount=${amount}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if(res.ok) setResult(await res.json());
    } catch(e) {}
  }

  useEffect(() => { convert(); }, [from, to, amount]);

  return (
    <div className="glass-card" style={{ padding: '20px' }}>
      <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '16px' }}>💱 Quick Currency</h3>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        <input style={{ width: '40%', padding: '8px', borderRadius: '6px', border: '1px solid #c8dff0', outline: 'none' }} value={amount} onChange={e => setAmount(e.target.value)} type="number" />
        <select style={{ flex: 1, padding: '8px', borderRadius: '6px', border: '1px solid #c8dff0', outline: 'none' }} value={from} onChange={e => setFrom(e.target.value)}>
          {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <span style={{ display: 'flex', alignItems: 'center', color: '#185FA5' }}>→</span>
        <select style={{ flex: 1, padding: '8px', borderRadius: '6px', border: '1px solid #c8dff0', outline: 'none' }} value={to} onChange={e => setTo(e.target.value)}>
          {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <div style={{ textAlign: 'center', fontSize: '20px', fontWeight: 800, color: '#185FA5' }}>
        {result ? result.converted_amount?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '...'} {to}
      </div>
    </div>
  );
}

function TripCard({ trip, token, getDays }) {
  const [photo, setPhoto] = useState('https://placehold.co/400x200/185FA5/FFFFFF?text=WanderWise');

  useEffect(() => {
    const fetchPhoto = async () => {
      try {
        const dest = trip.destination.split(',')[0];
        const res = await fetch(`https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=thumbnail&pithumbsize=400&titles=${encodeURIComponent(dest)}&origin=*`);
        const data = await res.json();
        const pages = data.query.pages;
        const pageId = Object.keys(pages)[0];
        if (pages[pageId].thumbnail) {
          setPhoto(pages[pageId].thumbnail.source);
        }
      } catch (e) {}
    };
    fetchPhoto();
  }, [trip]);

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ height: '140px', width: '100%', background: '#e4f1fb', position: 'relative' }}>
        <img src={photo} alt={trip.destination} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        <div style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(255,255,255,0.9)', color: '#185FA5', fontSize: '10px', padding: '4px 8px', borderRadius: '12px', fontWeight: 600, textTransform: 'uppercase', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          {trip.travel_type}
        </div>
      </div>
      <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', flex: 1 }}>
        <div className="text-primary-dark" style={{ fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>{trip.destination}</div>
        <div className="text-muted" style={{ fontSize: '11px', marginBottom: '16px' }}>
          {trip.start_date} — {trip.end_date} ({getDays(trip)} days)
        </div>
        <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ color: '#185FA5', fontWeight: 700, fontSize: '15px' }}>{formatCurrency(trip.budget || 0, trip.currency)}</div>
          <Link to={`/companion`} style={{ fontSize: '12px', color: '#4a6080', textDecoration: 'none', fontWeight: 600, background: 'rgba(24, 95, 165, 0.05)', padding: '6px 12px', borderRadius: '8px' }}>View Details →</Link>
        </div>
      </div>
    </div>
  );
}


// --- Main Dashboard Component ---

export default function Dashboard() {
  const navigate = useNavigate();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;
  let userId = null;
  try {
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = payload.sub || payload.user_id || payload.id;
    }
  } catch (_) {}

  const [form, setForm] = useState({
    destination: '', start_date: '', end_date: '', budget: '',
    travel_type: 'leisure', travel_style: 'solo', interests: 'sightseeing',
    group_size: '1', currency: 'USD',
  });

  const fetchTrips = async () => {
    if (!userId) { setLoading(false); return; }
    try {
      const res = await fetch(`${API}/trips/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok && Array.isArray(data)) setTrips(data);
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => { fetchTrips(); }, []);

  const handleChange = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/trips/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, user_id: Number(userId), budget: parseFloat(form.budget), group_size: parseInt(form.group_size) }),
      });
      if (res.ok) {
        setShowForm(false);
        fetchTrips();
      }
    } catch (_) {}
    setSubmitting(false);
  };

  const getDays = (t) => {
    if (!t.start_date || !t.end_date) return 0;
    return Math.round((new Date(t.end_date) - new Date(t.start_date)) / 86400000) + 1;
  };

  const inputStyle = { width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #c8dff0', background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '13px', boxSizing: 'border-box', outline: 'none' };
  const labelStyle = { display: 'block', marginBottom: '4px', fontSize: '11px', fontWeight: 600, color: '#5a7a9a', textTransform: 'uppercase' };

  const nextTrip = trips.length > 0 ? trips[0] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>
            Good morning, {user?.name?.split(' ')[0] || 'Traveler'}
          </h1>
          <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>
            WanderWise AI Command Center
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{ background: '#185FA5', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '10px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', boxShadow: '0 2px 8px rgba(24, 95, 165, 0.2)' }}
        >
          {showForm ? 'Cancel' : '+ Plan New Trip'}
        </button>
      </div>

      {/* Create Trip Form */}
      {showForm && (
        <form className="glass-card" onSubmit={handleSubmit} style={{ padding: '24px' }}>
          <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '16px' }}>New Trip Details</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ gridColumn: 'span 2' }}>
              <label style={labelStyle}>Destination</label>
              <input style={inputStyle} name="destination" value={form.destination} onChange={handleChange} placeholder="Paris, France" required />
            </div>
            <div><label style={labelStyle}>Start Date</label><input style={inputStyle} type="date" name="start_date" value={form.start_date} onChange={handleChange} required /></div>
            <div><label style={labelStyle}>End Date</label><input style={inputStyle} type="date" name="end_date" value={form.end_date} onChange={handleChange} required /></div>
            <div><label style={labelStyle}>Budget Amount</label><input style={inputStyle} type="number" name="budget" value={form.budget} onChange={handleChange} placeholder="2000" required /></div>
            <div>
              <label style={labelStyle}>Currency</label>
              <select style={inputStyle} name="currency" value={form.currency} onChange={handleChange}>
                {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div><label style={labelStyle}>Activity Pace</label><select style={inputStyle} name="travel_type" value={form.travel_type} onChange={handleChange}>{TRAVEL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}</select></div>
            <div>
              <label style={labelStyle}>Travel Style</label>
              <select style={inputStyle} name="travel_style" value={form.travel_style} onChange={handleChange}>
                <option value="solo">Solo</option>
                <option value="couple">Couple</option>
                <option value="family">Family</option>
                <option value="friends">Friends / Group</option>
              </select>
            </div>
            <div><label style={labelStyle}>Group Size</label><input style={inputStyle} type="number" min="1" name="group_size" value={form.group_size} onChange={handleChange} required /></div>
          </div>
          <button type="submit" disabled={submitting} style={{ marginTop: '16px', width: '100%', background: '#185FA5', color: 'white', border: 'none', padding: '12px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}>
            {submitting ? 'Generating AI Itinerary...' : 'Generate Itinerary'}
          </button>
        </form>
      )}

      {/* 1. Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
        {[
          { label: 'Total Trips', value: trips.length, sub: 'Active & past' },
          { label: 'Destinations', value: new Set(trips.map(t => (t.destination || '').split(',')[0])).size, sub: 'Globally' },
          { label: 'Total Budget', value: formatCurrency(trips.reduce((s, t) => s + (t.budget || 0), 0)), sub: 'Planned' },
          { label: 'Travel Days', value: trips.reduce((s, t) => s + getDays(t), 0), sub: 'Upcoming' },
        ].map((stat, i) => (
          <div key={i} className="glass-card" style={{ padding: '20px' }}>
            <div className="label-text" style={{ marginBottom: '8px' }}>{stat.label}</div>
            <div className="text-primary-dark" style={{ fontSize: '32px', fontWeight: 800, lineHeight: 1 }}>{stat.value}</div>
            <div style={{ fontSize: '12px', color: '#185FA5', marginTop: '8px', fontWeight: 500 }}>{stat.sub}</div>
          </div>
        ))}
      </div>

      {/* Smart Widget Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* Column 1 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <WeatherWidget trip={nextTrip} />
          <RiskAnalyzerWidget trip={nextTrip} token={token} />
        </div>

        {/* Column 2 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <LanguageWidget trip={nextTrip} token={token} />
          
          {/* Quick Chat Preview */}
          <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="text-primary-dark" style={{ fontSize: '14px', fontWeight: 700 }}>AI Travel Assistant</div>
            <div style={{ background: 'rgba(24, 95, 165, 0.1)', padding: '10px', borderRadius: '12px 12px 12px 0', fontSize: '12px', color: '#1a2a3a' }}>
              I have analyzed your upcoming trip to {(nextTrip?.destination || '').split(',')[0]}. Need packing or transit advice?
            </div>
            <Link to="/chat" style={{ textDecoration: 'none' }}>
              <div style={{ background: 'rgba(255,255,255,0.9)', border: '1px solid #c8dff0', borderRadius: '20px', padding: '8px 16px', fontSize: '12px', color: '#5a7a9a', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Ask anything...</span><span style={{ color: '#185FA5', fontWeight: 600 }}>↗</span>
              </div>
            </Link>
          </div>
        </div>

        {/* Column 3 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <PersonalizedWidget trips={trips} token={token} />
          <QuickCurrencyWidget token={token} />
        </div>

      </div>

      {/* Upcoming Trips List */}
      <div>
        <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '18px' }}>Upcoming Trips</h3>
        {loading ? (
          <div className="text-secondary">Loading trips...</div>
        ) : trips.length === 0 ? (
          <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}><p className="text-secondary" style={{ margin: 0 }}>No trips planned yet.</p></div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
            {trips.map(trip => (
              <TripCard key={trip.id} trip={trip} token={token} getDays={getDays} />
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
