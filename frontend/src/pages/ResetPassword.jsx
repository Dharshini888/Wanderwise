import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api from "../api/axios";
import {
  IconLock, IconEye, IconEyeOff, IconCompass, IconShieldCheck,
  IconAlertCircle, IconCheck, IconArrowLeft, IconSparkles
} from "@tabler/icons-react";
import "./auth.css";

function calcStrength(pwd) {
  let s=0;
  if(pwd.length>=8)s++;
  if(/[A-Z]/.test(pwd))s++;
  if(/[0-9]/.test(pwd))s++;
  if(/[^A-Za-z0-9]/.test(pwd))s++;
  return s;
}
const LABELS=["","Weak","Fair","Good","Strong"];

export default function ResetPassword() {
  const [params]            = useSearchParams();
  const token               = params.get("token") || "";
  const [pwd, setPwd]       = useState("");
  const [con, setCon]       = useState("");
  const [showPwd, setShowP] = useState(false);
  const [showCon, setShowC] = useState(false);
  const [error, setError]   = useState("");
  const [done, setDone]     = useState(false);
  const [loading, setLoad]  = useState(false);
  const navigate            = useNavigate();

  const str = calcStrength(pwd);
  const reqs = [
    { label:"At least 8 characters",  ok: pwd.length >= 8 },
    { label:"Uppercase letter (A-Z)", ok: /[A-Z]/.test(pwd) },
    { label:"Lowercase letter (a-z)", ok: /[a-z]/.test(pwd) },
    { label:"Number (0-9)",           ok: /[0-9]/.test(pwd) },
    { label:"Special character",      ok: /[^A-Za-z0-9]/.test(pwd) },
    { label:"Passwords match",        ok: pwd.length>0&&pwd===con },
  ];

  const handleSubmit = async e => {
    e.preventDefault();
    if (str < 2)           { setError("Please choose a stronger password."); return; }
    if (pwd !== con)       { setError("Passwords do not match."); return; }
    if (!token)            { setError("Invalid or expired reset link. Please request a new one."); return; }
    setLoad(true); setError("");
    try {
      await api.post("/api/auth/reset-password", { token, new_password: pwd });
      setDone(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Reset failed. The link may have expired.");
    }
    setLoad(false);
  };

  if (done) {
    return (
      <div className="au">
        <aside className="au-panel">
          <div className="au-panel__bg"/>
          <div className="au-panel__blobs"><div className="au-panel__blob au-panel__blob--a"/><div className="au-panel__blob au-panel__blob--b"/><div className="au-panel__blob au-panel__blob--c"/></div>
          <div className="au-panel__dots">{Array.from({length:80}).map((_,i)=><div key={i} className="au-panel__dot"/>)}</div>
          <div className="au-panel__logo"><div className="au-panel__logo-icon"><IconCompass size={20} stroke={2.5}/></div><span className="au-panel__logo-text">WanderWise</span></div>
          <div className="au-panel__content">
            <div className="au-panel__badge"><span className="au-panel__badge-dot"/> Password Updated Successfully</div>
            <h2 className="au-panel__headline">Your Account<br/>Is Secured<br/><span style={{color:"#34d399"}}>Again.</span></h2>
            <p className="au-panel__sub">Your password has been reset. You can now sign in with your new password and continue your travels.</p>
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
              <h2 className="au-success__title">Password updated! 🔐</h2>
              <p className="au-success__sub">Your password has been successfully reset. Sign in to continue your journey.</p>
              <div className="au-success__actions">
                <button className="au-btn au-btn--primary" onClick={()=>navigate("/login")}><IconSparkles size={17}/> Continue to Login</button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="au">
      <aside className="au-panel">
        <div className="au-panel__bg"/>
        <div className="au-panel__blobs"><div className="au-panel__blob au-panel__blob--a"/><div className="au-panel__blob au-panel__blob--b"/><div className="au-panel__blob au-panel__blob--c"/></div>
        <div className="au-panel__dots">{Array.from({length:80}).map((_,i)=><div key={i} className="au-panel__dot"/>)}</div>
        <div className="au-panel__logo"><div className="au-panel__logo-icon"><IconCompass size={20} stroke={2.5}/></div><span className="au-panel__logo-text">WanderWise</span></div>
        <div className="au-panel__content">
          <div className="au-panel__badge"><span className="au-panel__badge-dot"/> Secure Password Reset</div>
          <h2 className="au-panel__headline">Create a<br/>Strong New<br/><span style={{color:"#34d399"}}>Password.</span></h2>
          <p className="au-panel__sub">A strong password protects your trips, travel documents and personal details.</p>
          <div style={{marginTop:20}}>
            {[["Minimum 8 characters","Length requirement"],["Mix of cases","Uppercase and lowercase"],["Include numbers","Numeric characters"],["Special symbols","!, @, #, $ etc."]].map(([t,s],i)=>(
              <div key={i} className="au-panel__feature" style={{marginBottom:10}}>
                <div className="au-panel__feature-icon"><IconShieldCheck size={15}/></div>
                <div><div style={{color:"rgba(255,255,255,0.9)",fontSize:13,fontWeight:600}}>{t}</div><div style={{color:"rgba(255,255,255,0.5)",fontSize:11}}>{s}</div></div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      <main className="au-main">
        <div className="au-main__blob-a"/><div className="au-main__blob-b"/>
        <div className="au-card">
          <Link to="/" className="au-logo-mob"><div className="au-logo-mob__icon"><IconCompass size={18}/></div><span className="au-logo-mob__text">WanderWise</span></Link>
          <h1 className="au-card__title">Reset password</h1>
          <p className="au-card__sub">Enter and confirm your new password below.</p>

          {!token&&(
            <div className="au-alert au-alert--err" style={{marginBottom:18}}>
              <IconAlertCircle size={15} style={{flexShrink:0}}/>
              Invalid or missing reset token. <Link to="/forgot-password" className="au-link">Request a new link</Link>.
            </div>
          )}
          {error&&<div className="au-alert au-alert--err" style={{marginBottom:18}}><IconAlertCircle size={15} style={{flexShrink:0}}/>{error}</div>}

          <form className="au-form" onSubmit={handleSubmit} noValidate>
            <div className="au-field">
              <label htmlFor="rp-pwd" className="au-lbl">New Password <sup>*</sup></label>
              <div className="au-input-wrap">
                <span className="au-input-icon"><IconLock size={17}/></span>
                <input id="rp-pwd" type={showPwd?"text":"password"} className="au-input au-input--pr" placeholder="Min. 8 characters"
                  value={pwd} onChange={e=>setPwd(e.target.value)} autoComplete="new-password" required/>
                <button type="button" className="au-input-icon au-input-icon--r" onClick={()=>setShowP(s=>!s)} aria-label={showPwd?"Hide":"Show"}>
                  {showPwd?<IconEyeOff size={17}/>:<IconEye size={17}/>}
                </button>
              </div>
              {pwd&&(
                <div className="au-strength">
                  <div className="au-strength__bars">
                    {[1,2,3,4].map(n=><div key={n} className={"au-strength__bar"+(str>=n?" au-strength__bar--"+str:"")}/>)}
                  </div>
                  <span className={"au-strength__label au-strength__label--"+str}>{LABELS[str]}</span>
                </div>
              )}
            </div>
            <div className="au-field">
              <label htmlFor="rp-con" className="au-lbl">Confirm New Password <sup>*</sup></label>
              <div className="au-input-wrap">
                <span className="au-input-icon"><IconLock size={17}/></span>
                <input id="rp-con" type={showCon?"text":"password"} className={"au-input au-input--pr"+(con&&con!==pwd?" au-input--err":con&&con===pwd?" au-input--ok":"")}
                  placeholder="Repeat password" value={con} onChange={e=>setCon(e.target.value)} autoComplete="new-password" required/>
                <button type="button" className="au-input-icon au-input-icon--r" onClick={()=>setShowC(s=>!s)} aria-label="Toggle">
                  {showCon?<IconEyeOff size={17}/>:<IconEye size={17}/>}
                </button>
              </div>
            </div>
            <div className="au-req-list">
              {reqs.map((r,i)=><div key={i} className={"au-req"+(r.ok?" au-req--ok":"")}>
                <div className="au-req__dot"/>
                {r.ok?<IconCheck size={12}/>:null}{r.label}
              </div>)}
            </div>
            <button type="submit" className="au-btn au-btn--primary" disabled={loading||!token} id="rp-submit-btn">
              {loading?<><span className="au-spinner"/>Resetting…</>:<><IconShieldCheck size={17}/> Reset Password</>}
            </button>
          </form>

          <p className="au-signup-row">
            <Link to="/login" className="au-link" style={{display:"inline-flex",alignItems:"center",gap:5}}><IconArrowLeft size={14}/> Back to Login</Link>
          </p>
          <div className="au-foot"><a href="#" className="au-foot__link">Privacy Policy</a><a href="#" className="au-foot__link">Terms of Service</a></div>
        </div>
      </main>
    </div>
  );
}
