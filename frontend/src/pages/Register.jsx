import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import {
  IconUser, IconMail, IconPhone, IconLock, IconEye, IconEyeOff,
  IconCompass, IconSparkles, IconMap2, IconShieldCheck,
  IconAlertCircle, IconCheck, IconChevronRight, IconChevronLeft
} from "@tabler/icons-react";
import "./auth.css";
import { parseCurrencyCode } from "../utils/currencyFormatter";

const TRAVEL_STYLES = [
  "Solo", "Family", "Luxury", "Backpacking", "Adventure",
  "Food & Dining", "Shopping", "Photography", "Nature",
  "History & Culture", "Nightlife", "Spiritual & Religion"
];
const CLIMATES     = ["Mountains 🏔️", "Beach 🏖️", "City 🏙️", "Forest 🌿"];

// Minimal fallback — replaced by live /api/currency/registry data on mount
const CURRENCIES_FALLBACK = [
  { code: "USD", symbol: "$", name: "US Dollar" },
  { code: "INR", symbol: "₹", name: "Indian Rupee" },
  { code: "EUR", symbol: "€", name: "Euro" },
  { code: "GBP", symbol: "£", name: "British Pound" },
  { code: "JPY", symbol: "¥", name: "Japanese Yen" },
  { code: "AUD", symbol: "A$", name: "Australian Dollar" },
  { code: "CAD", symbol: "C$", name: "Canadian Dollar" },
  { code: "AED", symbol: "د.إ", name: "UAE Dirham" },
  { code: "SGD", symbol: "S$", name: "Singapore Dollar" },
  { code: "SAR", symbol: "﷼", name: "Saudi Riyal" },
];

const BUDGETS = ["Budget (<$50/day)", "Mid-range ($50–150/day)", "Comfort ($150–350/day)", "Luxury ($350+/day)"];
const DIETS   = ["No Preference", "Vegetarian", "Vegan", "Halal", "Kosher", "Gluten-Free"];

function calcStrength(pwd) {
  let score = 0;
  if (pwd.length >= 8)          score++;
  if (/[A-Z]/.test(pwd))        score++;
  if (/[0-9]/.test(pwd))        score++;
  if (/[^A-Za-z0-9]/.test(pwd)) score++;
  return score;
}

const STRENGTH_LABELS = ["", "Weak", "Fair", "Good", "Strong"];
const PANEL_FEATURES  = [
  { icon: IconSparkles,    text: "AI-generated day-by-day itineraries" },
  { icon: IconMap2,        text: "Smart destination recommendations" },
  { icon: IconShieldCheck, text: "Real-time safety and travel alerts" },
];

import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register: authRegister } = useAuth();
  const [step, setStep]       = useState(1);
  const [currencies, setCurrencies] = useState(CURRENCIES_FALLBACK);
  const [budgetTiers, setBudgetTiers] = useState([
    { key: "budget", label: "Budget (<$50/day)" },
    { key: "mid_range", label: "Mid-range ($50–150/day)" },
    { key: "comfort", label: "Comfort ($150–350/day)" },
    { key: "luxury", label: "Luxury ($350+/day)" },
  ]);
  const [form, setForm]       = useState({
    firstName: "", lastName: "", email: "", phone: "", password: "", confirm: "",
    styles: ["Solo", "Food & Dining"],
    climate: "Beach 🏖️",
    currency: "USD",
    budget: "mid_range",
    diet: "No Preference",
    languages: "English",
    accessibility: "None",
    terms: false, newsletter: false
  });
  const [showPwd, setShowPwd]   = useState(false);
  const [showCon, setShowCon]   = useState(false);
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [success, setSuccess]   = useState(false);
  const navigate                = useNavigate();

  // Load full currency list from backend registry
  useEffect(() => {
    api.get('/api/currency/registry')
      .then(r => {
        if (Array.isArray(r.data) && r.data.length > 5) {
          setCurrencies(r.data.sort((a, b) => a.code.localeCompare(b.code)));
        }
      })
      .catch(() => { /* keep fallback */ });
  }, []);

  // Fetch dynamic currency-converted budget ranges whenever currency changes
  useEffect(() => {
    const code = parseCurrencyCode(form.currency) || "USD";
    api.get(`/api/currency/budget-tiers?currency=${code}`)
      .then(r => {
        if (r.data && Array.isArray(r.data.tiers)) {
          setBudgetTiers(r.data.tiers);
        }
      })
      .catch(() => {});
  }, [form.currency]);

  const handleGoogleLogin = async () => {
    try {
      const res = await api.get('/api/auth/google/url');
      if (res.data && res.data.configured && res.data.auth_url) {
        window.location.href = res.data.auth_url;
      } else {
        setError(res.data?.setup_help || "Google OAuth is not configured on this server. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env.");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Could not connect to Google authentication service.");
    }
  };

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const toggleStyle = s => set("styles", form.styles.includes(s) ? form.styles.filter(x=>x!==s) : [...form.styles, s]);

  const strength = calcStrength(form.password);
  const reqs = [
    { label: "8+ characters", ok: form.password.length >= 8 },
    { label: "Uppercase letter", ok: /[A-Z]/.test(form.password) },
    { label: "Lowercase letter", ok: /[a-z]/.test(form.password) },
    { label: "Number", ok: /[0-9]/.test(form.password) },
    { label: "Special character", ok: /[^A-Za-z0-9]/.test(form.password) },
    { label: "Passwords match", ok: form.password && form.password === form.confirm },
  ];

  const validateStep1 = () => {
    if (!form.firstName.trim()) return "First name is required.";
    if (!form.lastName.trim())  return "Last name is required.";
    if (!form.email.includes("@")) return "Please enter a valid email address.";
    return "";
  };
  const validateStep2 = () => {
    if (form.password.length < 8)            return "Password must be at least 8 characters.";
    if (form.password !== form.confirm)      return "Passwords do not match.";
    if (!form.terms)                         return "Please accept the terms and conditions.";
    return "";
  };

  const nextStep = () => {
    const err = step === 1 ? validateStep1() : step === 2 ? validateStep2() : "";
    if (err) { setError(err); return; }
    setError(""); setStep(s => s + 1);
  };

  const handleSubmit = async e => {
    if (e) e.preventDefault();
    const err = validateStep2();
    if (err) { setError(err); setStep(2); return; }
    setLoading(true); setError("");
    try {
      const payload = {
        name: form.firstName.trim() + " " + form.lastName.trim(),
        email: form.email,
        password: form.password,
        phone_number: form.phone || undefined,
        preferred_budget: form.budget,
        currency: parseCurrencyCode(form.currency),
        travel_styles: form.styles.join(", "),
        preferred_climate: form.climate,
        preferred_activities: form.styles.join(", "),
        languages: form.languages,
        dietary_preferences: form.diet,
        accessibility_needs: form.accessibility,
      };
      await authRegister(payload);
      localStorage.setItem("ww_preferences", JSON.stringify(payload));
      setSuccess(true);
    } catch (err2) {
      setError(err2.response?.data?.detail || "Registration failed. Please try again.");
    }
    setLoading(false);
  };

  if (success) {
    return (
      <div className="au">
        <aside className="au-panel">
          <div className="au-panel__bg" />
          <div className="au-panel__blobs"><div className="au-panel__blob au-panel__blob--a"/><div className="au-panel__blob au-panel__blob--b"/><div className="au-panel__blob au-panel__blob--c"/></div>
          <div className="au-panel__dots">{Array.from({length:80}).map((_,i)=><div key={i} className="au-panel__dot"/>)}</div>
          <div className="au-panel__logo"><div className="au-panel__logo-icon"><IconCompass size={20} stroke={2.5}/></div><span className="au-panel__logo-text">WanderWise</span></div>
          <div className="au-panel__content">
            <div className="au-panel__badge"><span className="au-panel__badge-dot"/> Welcome to WanderWise!</div>
            <h2 className="au-panel__headline">Your Adventure<br/>Starts <span style={{color:"#34d399"}}>Now.</span></h2>
            <p className="au-panel__sub">You are now part of a community of 850,000+ smart travellers exploring the world with AI.</p>
            <div className="au-panel__features">{PANEL_FEATURES.map((f,i)=><div key={i} className="au-panel__feature"><div className="au-panel__feature-icon"><f.icon size={16}/></div><span className="au-panel__feature-text">{f.text}</span></div>)}</div>
          </div>
        </aside>
        <main className="au-main">
          <div className="au-main__blob-a"/><div className="au-main__blob-b"/>
          <div className="au-card">
            <Link to="/" className="au-logo-mob"><div className="au-logo-mob__icon"><IconCompass size={18}/></div><span className="au-logo-mob__text">WanderWise</span></Link>
            <div className="au-success">
              <div className="au-success__ring au-success__ring--green">
                <svg className="au-check-anim" viewBox="0 0 52 52">
                  <circle cx="26" cy="26" r="23"/>
                  <path d="M14 26l8 8 16-16"/>
                </svg>
              </div>
              <h2 className="au-success__title">Welcome aboard! 🎉</h2>
              <p className="au-success__sub">Your WanderWise account has been created. Verify your email to unlock all features.</p>
              <div className="au-success__email">{form.email}</div>
              <div className="au-success__actions">
                <button className="au-btn au-btn--primary" onClick={() => navigate("/dashboard")}><IconSparkles size={18}/> Go to Dashboard</button>
                <button className="au-btn au-btn--outline" onClick={() => navigate("/verify-email")}>Verify Email</button>
              </div>
              <p className="au-success__note">Check your inbox for a verification link. You can also verify later.</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="au">
      <aside className="au-panel">
        <div className="au-panel__bg" />
        <div className="au-panel__blobs"><div className="au-panel__blob au-panel__blob--a"/><div className="au-panel__blob au-panel__blob--b"/><div className="au-panel__blob au-panel__blob--c"/></div>
        <div className="au-panel__dots">{Array.from({length:80}).map((_,i)=><div key={i} className="au-panel__dot"/>)}</div>
        <div className="au-panel__logo"><div className="au-panel__logo-icon"><IconCompass size={20} stroke={2.5}/></div><span className="au-panel__logo-text">WanderWise</span></div>
        <div className="au-panel__content">
          <div className="au-panel__badge"><span className="au-panel__badge-dot"/> Join 850K+ Smart Travellers</div>
          <h2 className="au-panel__headline">Start Your AI<br/>Travel Journey<br/><span style={{color:"#34d399"}}>For Free.</span></h2>
          <p className="au-panel__sub">Create your account in under 2 minutes and let AI plan your perfect trip.</p>
          <div className="au-panel__features">{PANEL_FEATURES.map((f,i)=><div key={i} className="au-panel__feature"><div className="au-panel__feature-icon"><f.icon size={16}/></div><span className="au-panel__feature-text">{f.text}</span></div>)}</div>
          <div className="au-panel__stats"><div><div className="au-panel__stat-val">Free</div><div className="au-panel__stat-lbl">Forever plan</div></div><div><div className="au-panel__stat-val">10s</div><div className="au-panel__stat-lbl">Itinerary time</div></div><div><div className="au-panel__stat-val">4.9★</div><div className="au-panel__stat-lbl">App rating</div></div></div>
        </div>
      </aside>

      <main className="au-main">
        <div className="au-main__blob-a"/><div className="au-main__blob-b"/>
        <div className="au-card au-card--wide">
          <Link to="/" className="au-logo-mob"><div className="au-logo-mob__icon"><IconCompass size={18}/></div><span className="au-logo-mob__text">WanderWise</span></Link>

          <div className="au-steps">
            {["Account","Security","Preferences"].map((lbl,i)=>(
              <div key={lbl} style={{display:"contents"}}>
                <div className="au-step">
                  <div className={"au-step__circle"+(step>i+1?" au-step__circle--done":step===i+1?" au-step__circle--on":"")}>
                    {step>i+1?<IconCheck size={14}/>:i+1}
                  </div>
                  <span className="au-step__lbl">{lbl}</span>
                </div>
                {i<2&&<div className={"au-step__connector"+(step>i+1?" au-step__connector--done":"")}/>}
              </div>
            ))}
          </div>


          {step===1&&<><h1 className="au-card__title">Create your account</h1><p className="au-card__sub">Join thousands of smart travellers using AI to explore the world.</p></>}
          {step===2&&<><h1 className="au-card__title">Secure your account</h1><p className="au-card__sub">Create a strong password to protect your travel plans.</p></>}
          {step===3&&<><h1 className="au-card__title">Personalise your experience</h1><p className="au-card__sub">Help our AI plan trips you&apos;ll love by sharing your travel style.</p></>}

          {error&&<div className="au-alert au-alert--err" style={{marginBottom:18}}><IconAlertCircle size={16} style={{flexShrink:0}}/>{error}</div>}

          {/* STEP 1 */}
          {step===1&&(
            <div className="au-form">
              <div className="au-field__row">
                <div className="au-field">
                  <label htmlFor="reg-fn" className="au-lbl">First Name <sup>*</sup></label>
                  <div className="au-input-wrap"><span className="au-input-icon"><IconUser size={16}/></span>
                    <input id="reg-fn" type="text" className="au-input" placeholder="Alex" value={form.firstName} onChange={e=>set("firstName",e.target.value)} autoComplete="given-name" required/>
                  </div>
                </div>
                <div className="au-field">
                  <label htmlFor="reg-ln" className="au-lbl">Last Name <sup>*</sup></label>
                  <div className="au-input-wrap"><span className="au-input-icon"><IconUser size={16}/></span>
                    <input id="reg-ln" type="text" className="au-input" placeholder="Johnson" value={form.lastName} onChange={e=>set("lastName",e.target.value)} autoComplete="family-name" required/>
                  </div>
                </div>
              </div>
              <div className="au-field">
                <label htmlFor="reg-email" className="au-lbl">Email Address <sup>*</sup></label>
                <div className="au-input-wrap"><span className="au-input-icon"><IconMail size={16}/></span>
                  <input id="reg-email" type="email" className="au-input" placeholder="you@example.com" value={form.email} onChange={e=>set("email",e.target.value)} autoComplete="email" required/>
                </div>
              </div>
              <div className="au-field">
                <label htmlFor="reg-phone" className="au-lbl">Phone Number <span style={{fontWeight:400,textTransform:"none",fontSize:11}}>(optional)</span></label>
                <div className="au-input-wrap"><span className="au-input-icon"><IconPhone size={16}/></span>
                  <input id="reg-phone" type="tel" className="au-input" placeholder="+1 234 567 8900" value={form.phone} onChange={e=>set("phone",e.target.value)} autoComplete="tel"/>
                </div>
              </div>
              <button type="button" className="au-btn au-btn--primary" onClick={nextStep} id="reg-next-1">
                Continue <IconChevronRight size={17}/>
              </button>
              <div className="au-divider"><div className="au-divider__line"/><span className="au-divider__text">or sign up with</span><div className="au-divider__line"/></div>
              <button type="button" className="au-btn au-btn--google" id="reg-google-btn" onClick={handleGoogleLogin}>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
                Continue with Google
              </button>
            </div>
          )}

          {/* STEP 2 */}
          {step===2&&(
            <div className="au-form">
              <div className="au-field">
                <label htmlFor="reg-pwd" className="au-lbl">Password <sup>*</sup></label>
                <div className="au-input-wrap"><span className="au-input-icon"><IconLock size={16}/></span>
                  <input id="reg-pwd" type={showPwd?"text":"password"} className="au-input au-input--pr" placeholder="Min. 8 characters" value={form.password} onChange={e=>set("password",e.target.value)} autoComplete="new-password" required/>
                  <button type="button" className="au-input-icon au-input-icon--r" onClick={()=>setShowPwd(s=>!s)} aria-label={showPwd?"Hide":"Show"}>
                    {showPwd?<IconEyeOff size={16}/>:<IconEye size={16}/>}
                  </button>
                </div>
                {form.password&&(
                  <div className="au-strength">
                    <div className="au-strength__bars">
                      {[1,2,3,4].map(n=><div key={n} className={"au-strength__bar"+(strength>=n?" au-strength__bar--"+strength:"")}/>)}
                    </div>
                    <span className={"au-strength__label au-strength__label--"+strength}>{STRENGTH_LABELS[strength]}</span>
                  </div>
                )}
              </div>
              <div className="au-field">
                <label htmlFor="reg-con" className="au-lbl">Confirm Password <sup>*</sup></label>
                <div className="au-input-wrap"><span className="au-input-icon"><IconLock size={16}/></span>
                  <input id="reg-con" type={showCon?"text":"password"} className={"au-input au-input--pr"+(form.confirm&&form.confirm!==form.password?" au-input--err":form.confirm&&form.confirm===form.password?" au-input--ok":"")} placeholder="Repeat password" value={form.confirm} onChange={e=>set("confirm",e.target.value)} autoComplete="new-password" required/>
                  <button type="button" className="au-input-icon au-input-icon--r" onClick={()=>setShowCon(s=>!s)} aria-label="Toggle">
                    {showCon?<IconEyeOff size={16}/>:<IconEye size={16}/>}
                  </button>
                </div>
              </div>
              <div className="au-req-list">
                {reqs.map((r,i)=><div key={i} className={"au-req"+(r.ok?" au-req--ok":"")}>
                  <div className="au-req__dot"/>
                  {r.ok?<IconCheck size={12}/>:null}{r.label}
                </div>)}
              </div>
              <label className="au-check"><input type="checkbox" checked={form.terms} onChange={e=>set("terms",e.target.checked)} aria-required="true"/><span className="au-check__lbl">I agree to the <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a></span></label>
              <label className="au-check"><input type="checkbox" checked={form.newsletter} onChange={e=>set("newsletter",e.target.checked)}/><span className="au-check__lbl">Send me travel tips and destination guides (optional)</span></label>
              <div style={{display:"flex",gap:10}}>
                <button type="button" className="au-btn au-btn--outline" style={{flex:"0 0 auto",width:"auto",padding:"13px 18px"}} onClick={()=>{setError("");setStep(1);}}><IconChevronLeft size={17}/></button>
                <button type="button" className="au-btn au-btn--primary" style={{flex:1}} onClick={nextStep} id="reg-step2-next-btn">
                  Continue to Preferences <IconChevronRight size={17}/>
                </button>
              </div>
            </div>
          )}

          {/* STEP 3 */}
          {step===3&&(
            <div className="au-form">
              <div className="au-field">
                <label className="au-lbl">Travel Style (Select all that apply)</label>
                <div className="au-chips">{TRAVEL_STYLES.map(s=><button key={s} type="button" className={"au-chip"+(form.styles.includes(s)?" au-chip--on":"")} onClick={()=>toggleStyle(s)}>{s}</button>)}</div>
              </div>

              <div className="au-field">
                <label className="au-lbl">Preferred Climate</label>
                <div className="au-chips">{CLIMATES.map(c=><button key={c} type="button" className={"au-chip"+(form.climate===c?" au-chip--on":"")} onClick={()=>set("climate", c)}>{c}</button>)}</div>
              </div>

              <div className="au-field__row">
                <div className="au-field">
                  <label htmlFor="reg-cur" className="au-lbl">Preferred Currency</label>
                  <select id="reg-cur" className="au-input au-input--no-icon" value={form.currency} onChange={e=>set("currency",e.target.value)}>
                    {currencies.map(c=>(
                      <option key={c.code} value={c.code}>
                        {c.code} ({c.symbol}) — {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="au-field">
                  <label htmlFor="reg-bud" className="au-lbl">Budget Range</label>
                  <select id="reg-bud" className="au-input au-input--no-icon" value={form.budget} onChange={e=>set("budget",e.target.value)}>
                    {budgetTiers.map(b => (
                      <option key={b.key} value={b.key}>{b.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="au-field__row">
                <div className="au-field">
                  <label htmlFor="reg-diet" className="au-lbl">Dietary Preferences</label>
                  <select id="reg-diet" className="au-input au-input--no-icon" value={form.diet} onChange={e=>set("diet",e.target.value)}>{DIETS.map(d=><option key={d}>{d}</option>)}</select>
                </div>
                <div className="au-field">
                  <label htmlFor="reg-lang" className="au-lbl">Primary Language</label>
                  <input id="reg-lang" className="au-input au-input--no-icon" value={form.languages} onChange={e=>set("languages",e.target.value)} placeholder="e.g. English, French"/>
                </div>
              </div>

              <div style={{display:"flex",gap:10}}>
                <button type="button" className="au-btn au-btn--outline" style={{flex:"0 0 auto",width:"auto",padding:"13px 18px"}} onClick={()=>{setError("");setStep(2);}}><IconChevronLeft size={17}/></button>
                <button type="button" className="au-btn au-btn--primary" style={{flex:1}} onClick={handleSubmit} disabled={loading} id="reg-finish-btn">
                  {loading?<><span className="au-spinner"/>Creating account…</>:<><IconSparkles size={17}/> Create Account & Save Preferences</>}
                </button>
              </div>
            </div>
          )}

          <p className="au-signup-row">Already have an account? <Link to="/login">Sign in</Link></p>
          <div className="au-foot"><a href="#" className="au-foot__link">Privacy Policy</a><a href="#" className="au-foot__link">Terms of Service</a><span className="au-foot__link">v2.0.0</span></div>
        </div>
      </main>
    </div>
  );
}
