import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import {
  IconMail, IconCompass, IconSparkles, IconMap2, IconShieldCheck,
  IconAlertCircle, IconArrowLeft, IconSend, IconRefresh
} from "@tabler/icons-react";
import "./auth.css";

const PANEL_FEATURES = [
  { icon: IconSparkles,    text: "AI-generated day-by-day itineraries" },
  { icon: IconMap2,        text: "Smart destination recommendations" },
  { icon: IconShieldCheck, text: "Real-time safety and travel alerts" },
];

export default function ForgotPassword() {
  const [email, setEmail]   = useState("");
  const [sent, setSent]     = useState(false);
  const [error, setError]   = useState("");
  const [loading, setLoading] = useState(false);
  const [resendCD, setResendCD] = useState(0);

  const handleSubmit = async e => {
    e.preventDefault();
    if (!email.includes("@")) { setError("Please enter a valid email address."); return; }
    setLoading(true); setError("");
    try {
      await api.post("/api/auth/forgot-password", { email });
      setSent(true);
      startCooldown();
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (err.response?.status === 404) { setSent(true); startCooldown(); }
      else setError(msg || "Something went wrong. Please try again.");
    }
    setLoading(false);
  };

  const startCooldown = () => {
    setResendCD(60);
    const t = setInterval(() => setResendCD(s => { if (s <= 1) { clearInterval(t); return 0; } return s - 1; }), 1000);
  };

  const handleResend = async () => {
    if (resendCD > 0 || !email) return;
    setLoading(true);
    try { await api.post("/api/auth/forgot-password", { email }); } catch (_) {}
    setLoading(false);
    startCooldown();
  };

  return (
    <div className="au">
      <aside className="au-panel">
        <div className="au-panel__bg"/>
        <div className="au-panel__blobs"><div className="au-panel__blob au-panel__blob--a"/><div className="au-panel__blob au-panel__blob--b"/><div className="au-panel__blob au-panel__blob--c"/></div>
        <div className="au-panel__dots">{Array.from({length:80}).map((_,i)=><div key={i} className="au-panel__dot"/>)}</div>
        <div className="au-panel__logo"><div className="au-panel__logo-icon"><IconCompass size={20} stroke={2.5}/></div><span className="au-panel__logo-text">WanderWise</span></div>
        <div className="au-panel__content">
          <div className="au-panel__badge"><span className="au-panel__badge-dot"/> Secure Account Recovery</div>
          <h2 className="au-panel__headline">Reset Your<br/>Password<br/><span style={{color:"#34d399"}}>Securely.</span></h2>
          <p className="au-panel__sub">We take your account security seriously. Your reset link expires in 15 minutes and can only be used once.</p>
          <div className="au-panel__features">{PANEL_FEATURES.map((f,i)=><div key={i} className="au-panel__feature"><div className="au-panel__feature-icon"><f.icon size={16}/></div><span className="au-panel__feature-text">{f.text}</span></div>)}</div>
        </div>
      </aside>

      <main className="au-main">
        <div className="au-main__blob-a"/><div className="au-main__blob-b"/>
        <div className="au-card">
          <Link to="/" className="au-logo-mob"><div className="au-logo-mob__icon"><IconCompass size={18}/></div><span className="au-logo-mob__text">WanderWise</span></Link>

          {!sent ? (
            <>
              <h1 className="au-card__title">Forgot password?</h1>
              <p className="au-card__sub">Enter your account email and we will send you a secure reset link.</p>

              {error&&<div className="au-alert au-alert--err" style={{marginBottom:18}}><IconAlertCircle size={16} style={{flexShrink:0}}/>{error}</div>}

              <form className="au-form" onSubmit={handleSubmit} noValidate>
                <div className="au-field">
                  <label htmlFor="fp-email" className="au-lbl">Email Address <sup>*</sup></label>
                  <div className="au-input-wrap">
                    <span className="au-input-icon"><IconMail size={17}/></span>
                    <input id="fp-email" type="email" className="au-input" placeholder="you@example.com"
                      value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email" required aria-required="true"/>
                  </div>
                </div>
                <button type="submit" className="au-btn au-btn--primary" disabled={loading} id="fp-submit-btn">
                  {loading?<><span className="au-spinner"/>Sending…</>:<><IconSend size={17}/> Send Reset Link</>}
                </button>
              </form>
              <p className="au-signup-row"><Link to="/login" className="au-link" style={{display:"inline-flex",alignItems:"center",gap:5}}><IconArrowLeft size={14}/> Back to Login</Link></p>
            </>
          ) : (
            <div className="au-success">
              <div className="au-success__ring au-success__ring--blue">
                <IconMail size={36}/>
              </div>
              <h2 className="au-success__title">Check your inbox</h2>
              <p className="au-success__sub">We have sent a password reset link to your email address. It expires in <strong>15 minutes</strong>.</p>
              <div className="au-success__email">{email}</div>
              <div className="au-alert au-alert--info" style={{width:"100%",maxWidth:380,textAlign:"left"}}>
                <IconAlertCircle size={15} style={{flexShrink:0}}/>
                <span>Didn&apos;t receive the email? Check your spam folder or request a new link below.</span>
              </div>
              <div className="au-success__actions">
                <button className="au-btn au-btn--outline" disabled={resendCD>0||loading} onClick={handleResend} id="fp-resend-btn">
                  {loading?<><span className="au-spinner au-spinner--dark"/>Sending…</>:resendCD>0?<>Resend in {resendCD}s</>:<><IconRefresh size={16}/> Resend Email</>}
                </button>
                <Link to="/login" className="au-btn au-btn--primary"><IconArrowLeft size={16}/> Back to Login</Link>
              </div>
              <p className="au-success__note">Wrong email? <button className="au-btn--ghost au-link" style={{display:"inline",padding:0}} onClick={()=>{setSent(false);setEmail("");}}>Change email address</button></p>
            </div>
          )}

          <div className="au-foot" style={{marginTop:24}}>
            <a href="#" className="au-foot__link">Privacy Policy</a>
            <a href="#" className="au-foot__link">Terms of Service</a>
            <a href="#" className="au-foot__link">Contact Support</a>
          </div>
        </div>
      </main>
    </div>
  );
}
