import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api from "../api/axios";
import {
  IconMail, IconCompass, IconSparkles, IconMap2, IconShieldCheck,
  IconAlertCircle, IconCheck, IconRefresh, IconEdit, IconArrowRight
} from "@tabler/icons-react";
import "./auth.css";

export default function EmailVerification() {
  const [params]              = useSearchParams();
  const token                 = params.get("token") || "";
  const [status, setStatus]   = useState(token ? "verifying" : "pending");
  const [email, setEmail]     = useState(() => { try { return JSON.parse(localStorage.getItem("user") || "{}").email || ""; } catch(_){ return ""; } });
  const [newEmail, setNewEmail] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [resendCD, setResendCD] = useState(0);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const navigate                = useNavigate();

  const startCooldown = () => {
    setResendCD(60);
    const t = setInterval(() => setResendCD(s => { if(s<=1){clearInterval(t);return 0;} return s-1; }), 1000);
  };

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        await api.post("/api/auth/verify-email", { token });
        setStatus("success");
      } catch(err) {
        setStatus(err.response?.status === 410 ? "expired" : "error");
        setError(err.response?.data?.detail || "Verification failed.");
      }
    })();
  }, [token]);

  const handleResend = async () => {
    if (resendCD > 0) return;
    setLoading(true); setError("");
    try {
      await api.post("/api/auth/resend-verification", { email: editMode ? newEmail : email });
      if (editMode && newEmail) setEmail(newEmail);
      setEditMode(false);
      startCooldown();
    } catch(err) {
      setError(err.response?.data?.detail || "Failed to send email.");
    }
    setLoading(false);
  };

  const PANEL = (
    <aside className="au-panel">
      <div className="au-panel__bg"/>
      <div className="au-panel__blobs"><div className="au-panel__blob au-panel__blob--a"/><div className="au-panel__blob au-panel__blob--b"/><div className="au-panel__blob au-panel__blob--c"/></div>
      <div className="au-panel__dots">{Array.from({length:80}).map((_,i)=><div key={i} className="au-panel__dot"/>)}</div>
      <div className="au-panel__logo"><div className="au-panel__logo-icon"><IconCompass size={20} stroke={2.5}/></div><span className="au-panel__logo-text">WanderWise</span></div>
      <div className="au-panel__content">
        <div className="au-panel__badge"><span className="au-panel__badge-dot"/> Email Verification</div>
        <h2 className="au-panel__headline">One Last<br/>Step to<br/><span style={{color:"#34d399"}}>Explore More.</span></h2>
        <p className="au-panel__sub">Verifying your email unlocks personalised AI features, saved itineraries and your secure document vault.</p>
        <div className="au-panel__features">
          {[{icon:IconSparkles,text:"Full AI itinerary generator"},{icon:IconMap2,text:"Personalised destination picks"},{icon:IconShieldCheck,text:"Encrypted document vault"}].map((f,i)=>(
            <div key={i} className="au-panel__feature"><div className="au-panel__feature-icon"><f.icon size={16}/></div><span className="au-panel__feature-text">{f.text}</span></div>
          ))}
        </div>
      </div>
    </aside>
  );

  const MOB_LOGO = (
    <Link to="/" className="au-logo-mob"><div className="au-logo-mob__icon"><IconCompass size={18}/></div><span className="au-logo-mob__text">WanderWise</span></Link>
  );

  if (status === "verifying") {
    return (
      <div className="au">{PANEL}
        <main className="au-main"><div className="au-main__blob-a"/><div className="au-main__blob-b"/>
          <div className="au-card">{MOB_LOGO}
            <div className="au-success">
              <div className="au-success__ring au-success__ring--blue" style={{animation:"au-pulse 1.5s ease-in-out infinite"}}>
                <IconMail size={36}/>
              </div>
              <h2 className="au-success__title">Verifying…</h2>
              <p className="au-success__sub">Please wait while we verify your email address.</p>
              <div className="au-btn au-btn--outline" style={{width:180,justifyContent:"center",cursor:"default"}}>
                <span className="au-spinner au-spinner--dark"/>Verifying email
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="au">{PANEL}
        <main className="au-main"><div className="au-main__blob-a"/><div className="au-main__blob-b"/>
          <div className="au-card">{MOB_LOGO}
            <div className="au-success">
              <div className="au-success__ring au-success__ring--green">
                <svg className="au-check-anim" viewBox="0 0 52 52">
                  <circle cx="26" cy="26" r="23"/>
                  <path d="M14 26l8 8 16-16"/>
                </svg>
              </div>
              <h2 className="au-success__title">Email Verified! 🎉</h2>
              <p className="au-success__sub">Your account is now fully verified. Welcome to WanderWise — your AI travel journey begins now!</p>
              <div className="au-success__actions">
                <button className="au-btn au-btn--primary" onClick={()=>navigate("/dashboard")} id="verify-dashboard-btn">
                  <IconSparkles size={17}/> Go to Dashboard <IconArrowRight size={16}/>
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (status === "expired") {
    return (
      <div className="au">{PANEL}
        <main className="au-main"><div className="au-main__blob-a"/><div className="au-main__blob-b"/>
          <div className="au-card">{MOB_LOGO}
            <div className="au-success">
              <div className="au-success__ring" style={{background:"rgba(239,68,68,0.1)",border:"2px solid rgba(239,68,68,0.3)",color:"#EF4444"}}>
                <IconAlertCircle size={36}/>
              </div>
              <h2 className="au-success__title">Link Expired</h2>
              <p className="au-success__sub">Your verification link has expired. Request a new one below — it is valid for 24 hours.</p>
              {error&&<div className="au-alert au-alert--err" style={{width:"100%",maxWidth:380}}><IconAlertCircle size={14} style={{flexShrink:0}}/>{error}</div>}
              <div className="au-success__actions">
                <button className="au-btn au-btn--primary" onClick={handleResend} disabled={loading||resendCD>0} id="verify-resend-btn">
                  {loading?<><span className="au-spinner"/>Sending…</>:resendCD>0?`Resend in ${resendCD}s`:<><IconRefresh size={16}/> Send New Link</>}
                </button>
                <Link to="/login" className="au-btn au-btn--outline">Back to Login</Link>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  /* Default: "pending" state — waiting for user to click email link */
  return (
    <div className="au">{PANEL}
      <main className="au-main"><div className="au-main__blob-a"/><div className="au-main__blob-b"/>
        <div className="au-card">{MOB_LOGO}
          <div className="au-success">
            <div className="au-success__ring au-success__ring--blue">
              <IconMail size={36}/>
            </div>
            <h2 className="au-success__title">Verify your email</h2>
            <p className="au-success__sub">We sent a verification link to your email. Click it to activate your account and unlock all AI features.</p>
            {email&&<div className="au-success__email">{email}</div>}
            {error&&<div className="au-alert au-alert--err" style={{width:"100%",maxWidth:380}}><IconAlertCircle size={14} style={{flexShrink:0}}/>{error}</div>}

            {editMode ? (
              <div className="au-form" style={{width:"100%",maxWidth:360}}>
                <div className="au-field">
                  <label className="au-lbl">New Email Address</label>
                  <div className="au-input-wrap">
                    <span className="au-input-icon"><IconMail size={16}/></span>
                    <input type="email" className="au-input" placeholder="new@email.com" value={newEmail} onChange={e=>setNewEmail(e.target.value)}/>
                  </div>
                </div>
                <div style={{display:"flex",gap:10}}>
                  <button className="au-btn au-btn--outline" style={{flex:1}} onClick={()=>setEditMode(false)}>Cancel</button>
                  <button className="au-btn au-btn--primary" style={{flex:1}} onClick={handleResend} disabled={loading||!newEmail}>
                    {loading?<><span className="au-spinner"/>Sending…</>:<><IconMail size={15}/> Update &amp; Send</>}
                  </button>
                </div>
              </div>
            ) : (
              <div className="au-success__actions">
                <button className="au-btn au-btn--primary" onClick={handleResend} disabled={loading||resendCD>0} id="verify-resend2-btn">
                  {loading?<><span className="au-spinner"/>Sending…</>:resendCD>0?`Resend in ${resendCD}s`:<><IconRefresh size={16}/> Resend Verification</>}
                </button>
                <button className="au-btn au-btn--outline" onClick={()=>setEditMode(true)}>
                  <IconEdit size={15}/> Change Email
                </button>
                <Link to="/dashboard" className="au-btn--ghost au-link" style={{fontSize:13,marginTop:4}}>Skip for now <IconArrowRight size={13}/></Link>
              </div>
            )}
            <p className="au-success__note">The link expires in 24 hours. Check your spam folder if you don&apos;t see it.</p>
          </div>
          <div className="au-foot"><a href="#" className="au-foot__link">Privacy Policy</a><a href="#" className="au-foot__link">Terms of Service</a><a href="#" className="au-foot__link">Contact Support</a></div>
        </div>
      </main>
    </div>
  );
}
