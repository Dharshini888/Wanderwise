import { useEffect, useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";
import { IconCompass, IconAlertCircle, IconSparkles } from "@tabler/icons-react";
import "./auth.css";

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setSession } = useAuth();

  const [status, setStatus] = useState("processing");
  const [errorMessage, setErrorMessage] = useState("");
  const [errorDetails, setErrorDetails] = useState("");

  useEffect(() => {
    const error = searchParams.get("error");
    const details = searchParams.get("details");
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");
    const redirectTo = searchParams.get("redirect_to") || "/dashboard";

    if (error) {
      setStatus("error");
      if (error === "unconfigured_oauth") {
        setErrorMessage("Google OAuth is not configured.");
        setErrorDetails(
          details || "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env to enable Google Sign-In."
        );
      } else if (error === "cancelled" || error === "access_denied") {
        setErrorMessage("Google Sign-In was cancelled.");
        setErrorDetails("You closed the Google account selector or denied authorization.");
      } else {
        setErrorMessage(`Authentication Error: ${error}`);
        setErrorDetails(details || "Unable to complete Google authentication. Please try again.");
      }
      return;
    }

    if (!accessToken) {
      setStatus("error");
      setErrorMessage("Missing authentication token.");
      setErrorDetails("No token was received from the authentication provider.");
      return;
    }

    // Process valid login
    const completeAuth = async () => {
      try {
        setSession(accessToken, refreshToken, null);
        const res = await api.get("/api/auth/me", {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (res.data) {
          setSession(accessToken, refreshToken, res.data);
        }
        setStatus("success");
        setTimeout(() => {
          navigate(redirectTo, { replace: true });
        }, 800);
      } catch (err) {
        setStatus("error");
        setErrorMessage("Failed to retrieve user profile.");
        setErrorDetails(err.response?.data?.detail || err.message || "An unexpected error occurred.");
      }
    };

    completeAuth();
  }, [searchParams, navigate, setSession]);

  return (
    <div className="au">
      <main className="au-main" style={{ width: "100%", minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="au-card" style={{ maxWidth: 440, width: "100%", margin: "auto", textAlign: "center" }}>
          <div className="au-panel__logo" style={{ justifyContent: "center", marginBottom: 20 }}>
            <div className="au-panel__logo-icon">
              <IconCompass size={22} stroke={2.5} />
            </div>
            <span className="au-panel__logo-text">WanderWise</span>
          </div>

          {status === "processing" && (
            <div>
              <div className="au-spinner" style={{ width: 36, height: 36, margin: "20px auto" }} />
              <h2 className="au-card__title" style={{ marginTop: 16 }}>Signing you in…</h2>
              <p className="au-card__sub">Connecting your Google account with WanderWise.</p>
            </div>
          )}

          {status === "success" && (
            <div>
              <div className="au-success__ring au-success__ring--green" style={{ margin: "20px auto" }}>
                <svg className="au-check-anim" viewBox="0 0 52 52">
                  <circle cx="26" cy="26" r="23" />
                  <path d="M14 26l8 8 16-16" />
                </svg>
              </div>
              <h2 className="au-card__title">Sign-In Successful!</h2>
              <p className="au-card__sub">Redirecting to your dashboard…</p>
            </div>
          )}

          {status === "error" && (
            <div>
              <div className="au-alert au-alert--err" style={{ marginBottom: 20, textAlign: "left" }}>
                <IconAlertCircle size={20} style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ fontWeight: 700 }}>{errorMessage}</div>
                  {errorDetails && <div style={{ fontSize: 12, marginTop: 4, opacity: 0.9 }}>{errorDetails}</div>}
                </div>
              </div>
              <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
                <Link to="/login" className="au-btn au-btn--primary">
                  Return to Login
                </Link>
                <Link to="/register" className="au-btn au-btn--outline">
                  Register
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
