import { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  IconMail, IconLock, IconEye, IconEyeOff,
  IconCompass, IconSparkles, IconMap2, IconShieldCheck,
  IconAlertCircle
} from "@tabler/icons-react";
import "./auth.css";

const PANEL_FEATURES = [
  { icon: IconSparkles, text: "AI-generated day-by-day itineraries" },
  { icon: IconMap2,     text: "Smart destination recommendations" },
  { icon: IconShieldCheck, text: "Real-time safety and travel alerts" },
];

export default function Login() {
  const [form, setForm]       = useState({ email: "", password: "", remember: false });
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);
  const [shake, setShake]     = useState(false);
  const navigate              = useNavigate();
  const formRef               = useRef(null);
  const { login: authLogin }  = useAuth();

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const triggerShake = () => {
    setShake(true);
    setTimeout(() => setShake(false), 450);
  };

  const handleSubmit = async e => {
    e.preventDefault();
    if (!form.email || !form.password) { setError("Please fill in all fields."); triggerShake(); return; }
    setLoading(true); setError("");
    try {
      await authLogin(form.email, form.password, form.remember);
      navigate("/dashboard");
    } catch (err) {
      const msg = err.response?.data?.detail || "Invalid email or password. Please try again.";
      setError(msg);
      triggerShake();
    }
    setLoading(false);
  };

  return (
    <div className="au">
      {/* ── Left panel ── */}
      <aside className="au-panel">
        <div className="au-panel__bg" />
        <div className="au-panel__blobs">
          <div className="au-panel__blob au-panel__blob--a" />
          <div className="au-panel__blob au-panel__blob--b" />
          <div className="au-panel__blob au-panel__blob--c" />
        </div>
        <div className="au-panel__dots">
          {Array.from({ length: 80 }).map((_, i) => <div key={i} className="au-panel__dot" />)}
        </div>
        <div className="au-panel__logo">
          <div className="au-panel__logo-icon"><IconCompass size={20} stroke={2.5} /></div>
          <span className="au-panel__logo-text">WanderWise</span>
        </div>
        <div className="au-panel__content">
          <div className="au-panel__badge">
            <span className="au-panel__badge-dot" /> AI 2.0 — Now smarter than ever
          </div>
          <h2 className="au-panel__headline">
            Your AI Travel<br />Companion<br /><span style={{ color: "#34d399" }}>Awaits You.</span>
          </h2>
          <p className="au-panel__sub">
            Plan personalised trips in seconds. 850,000+ travellers trust WanderWise to explore the world smarter.
          </p>
          <div className="au-panel__features">
            {PANEL_FEATURES.map((f, i) => (
              <div key={i} className="au-panel__feature">
                <div className="au-panel__feature-icon"><f.icon size={16} /></div>
                <span className="au-panel__feature-text">{f.text}</span>
              </div>
            ))}
          </div>
          <div className="au-panel__stats">
            <div><div className="au-panel__stat-val">850K+</div><div className="au-panel__stat-lbl">Travellers</div></div>
            <div><div className="au-panel__stat-val">195</div><div className="au-panel__stat-lbl">Countries</div></div>
            <div><div className="au-panel__stat-val">4.9★</div><div className="au-panel__stat-lbl">Rating</div></div>
          </div>
        </div>
      </aside>

      {/* ── Right / Form ── */}
      <main className="au-main" aria-label="Login form">
        <div className="au-main__blob-a" /><div className="au-main__blob-b" />
        <div className={"au-card" + (shake ? " au-shake" : "")} ref={formRef}>
          {/* Mobile logo */}
          <Link to="/" className="au-logo-mob">
            <div className="au-logo-mob__icon"><IconCompass size={18} /></div>
            <span className="au-logo-mob__text">WanderWise</span>
          </Link>

          <h1 className="au-card__title">Welcome back 👋</h1>
          <p className="au-card__sub">Sign in to continue your travel journey.</p>

          {/* Error banner */}
          {error && (
            <div className="au-alert au-alert--err" role="alert" style={{ marginBottom: 18 }}>
              <IconAlertCircle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
              {error}
            </div>
          )}

          <form className="au-form" onSubmit={handleSubmit} noValidate>
            {/* Email */}
            <div className="au-field">
              <label htmlFor="login-email" className="au-lbl">Email Address <sup>*</sup></label>
              <div className="au-input-wrap">
                <span className="au-input-icon"><IconMail size={17} /></span>
                <input
                  id="login-email"
                  type="email"
                  className={"au-input" + (error ? " au-input--err" : "")}
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={e => set("email", e.target.value)}
                  autoComplete="email"
                  aria-required="true"
                  aria-describedby="login-email-err"
                />
              </div>
            </div>

            {/* Password */}
            <div className="au-field">
              <label htmlFor="login-pwd" className="au-lbl">Password <sup>*</sup></label>
              <div className="au-input-wrap">
                <span className="au-input-icon"><IconLock size={17} /></span>
                <input
                  id="login-pwd"
                  type={showPwd ? "text" : "password"}
                  className={"au-input au-input--pr" + (error ? " au-input--err" : "")}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => set("password", e.target.value)}
                  autoComplete="current-password"
                  aria-required="true"
                />
                <button
                  type="button"
                  className="au-input-icon au-input-icon--r"
                  onClick={() => setShowPwd(s => !s)}
                  aria-label={showPwd ? "Hide password" : "Show password"}
                >
                  {showPwd ? <IconEyeOff size={17} /> : <IconEye size={17} />}
                </button>
              </div>
            </div>

            {/* Remember & Forgot */}
            <div className="au-extras">
              <label className="au-remember">
                <input type="checkbox" checked={form.remember} onChange={e => set("remember", e.target.checked)} aria-label="Remember me" />
                <span>Remember me</span>
              </label>
              <Link to="/forgot-password" className="au-link" aria-label="Forgot password">Forgot password?</Link>
            </div>

            {/* Submit */}
            <button type="submit" className="au-btn au-btn--primary" disabled={loading} id="login-submit-btn">
              {loading ? <><span className="au-spinner" aria-hidden="true" /> Signing in…</> : "Sign In"}
            </button>
          </form>

          {/* Divider */}
          <div className="au-divider" style={{ margin: "20px 0" }}>
            <div className="au-divider__line" />
            <span className="au-divider__text">or continue with</span>
            <div className="au-divider__line" />
          </div>

          {/* Google */}
          <button className="au-btn au-btn--google" type="button" id="login-google-btn" aria-label="Sign in with Google">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </button>

          {/* Sign up link */}
          <p className="au-signup-row">
            Don&apos;t have an account? <Link to="/register">Create one free</Link>
          </p>

          {/* Footer links */}
          <div className="au-foot">
            <a href="#" className="au-foot__link">Privacy Policy</a>
            <a href="#" className="au-foot__link">Terms of Service</a>
            <span className="au-foot__link">v2.0.0</span>
          </div>
        </div>
      </main>
    </div>
  );
}
