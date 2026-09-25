import React, { useState } from "react";
import {
  X, ExternalLink, ChevronRight, ChevronLeft, Shield,
  Key, Globe, CheckCircle2, Loader2, AlertCircle, Copy, Check,
  Sparkles, Lock, ArrowRight
} from "lucide-react";

const STEPS = [
  { id: 1, label: "Create App" },
  { id: 2, label: "OAuth Creds" },
  { id: 3, label: "Connect" },
];

const REDIRECT_URI = "http://localhost:8000/auth/callback";

export default function ConnectJiraModal({ onClose }) {
  const [step, setStep] = useState(1);
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copiedUri, setCopiedUri] = useState(false);

  const handleCopyUri = () => {
    navigator.clipboard.writeText(REDIRECT_URI);
    setCopiedUri(true);
    setTimeout(() => setCopiedUri(false), 2000);
  };

  const handleConnect = async () => {
    if (!clientId.trim() || !clientSecret.trim()) {
      setError("Both Client ID and Client Secret are required.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/auth/configure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: clientId.trim(), client_secret: clientSecret.trim() }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to save credentials");
      }
      window.location.href = "http://localhost:8000/auth/login?session_id=default_user";
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  };

  const advanceStep = () => {
    if (step === 2 && (!clientId.trim() || !clientSecret.trim())) {
      setError("Both Client ID and Client Secret are required.");
      return;
    }
    setError("");
    setStep((s) => s + 1);
  };

  return (
    <div className="cjm-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="cjm-modal">

        {/* Header */}
        <div className="cjm-header">
          <div className="cjm-header-brand">
            <div className="cjm-jira-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                <path d="M11.53 2c0 2.4 1.97 4.35 4.35 4.35h1.78v1.7c0 2.4 1.94 4.34 4.34 4.35V2.84C22 2.38 21.62 2 21.16 2H11.53zm-5.6 5.88c0 2.4 1.97 4.35 4.35 4.35h1.78v1.7c0 2.4 1.94 4.35 4.34 4.35V8.72c0-.46-.38-.84-.84-.84H5.93zm-5.6 5.88c0 2.4 1.97 4.35 4.35 4.35h1.78v1.7c0 2.4 1.94 4.35 4.34 4.35V14.6c0-.46-.38-.84-.84-.84H.33z"/>
              </svg>
            </div>
            <div>
              <div className="cjm-title">Connect Your Jira Cloud Workspace</div>
              <div className="cjm-subtitle">Authorize your Atlassian account in 3 steps — takes about 3 minutes</div>
            </div>
          </div>
          <button className="cjm-close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        {/* Step Tracker */}
        <div className="cjm-steps-bar">
          {STEPS.map((s, idx) => (
            <React.Fragment key={s.id}>
              <div className={`cjm-step-item ${step === s.id ? "active" : step > s.id ? "done" : ""}`}>
                <div className="cjm-step-circle">
                  {step > s.id ? <CheckCircle2 size={14} /> : s.id}
                </div>
                <div className="cjm-step-label">{s.label}</div>
              </div>
              {idx < STEPS.length - 1 && (
                <div className={`cjm-step-connector ${step > s.id ? "done" : ""}`} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Body */}
        <div className="cjm-body">

          {/* Step 1: Create App */}
          {step === 1 && (
            <div className="cjm-step-content">
              <div className="cjm-step-icon-header">
                <div className="cjm-icon-circle blue"><Globe size={22} /></div>
                <div>
                  <div className="cjm-step-heading">Create a Free Atlassian OAuth App</div>
                  <div className="cjm-step-desc">Register an app on the Atlassian Developer Console. Free and takes 2 minutes.</div>
                </div>
              </div>

              <div className="cjm-instruction-list">
                <div className="cjm-instruction-item">
                  <div className="cjm-inst-num">1</div>
                  <div className="cjm-inst-body">
                    <div className="cjm-inst-title">Open the Atlassian Developer Console</div>
                    <div className="cjm-inst-desc">Click the button below to open it in a new tab.</div>
                    <a href="https://developer.atlassian.com/console/myapps/" target="_blank" rel="noopener noreferrer" className="cjm-link-btn">
                      <ExternalLink size={13} /> Open Atlassian Developer Console
                    </a>
                  </div>
                </div>

                <div className="cjm-instruction-item">
                  <div className="cjm-inst-num">2</div>
                  <div className="cjm-inst-body">
                    <div className="cjm-inst-title">Create a new OAuth 2.0 app</div>
                    <div className="cjm-inst-desc">Click <strong>Create</strong> and choose <strong>OAuth 2.0 integration</strong>. Name it anything (e.g. <em>Jira AI Assistant</em>).</div>
                  </div>
                </div>

                <div className="cjm-instruction-item">
                  <div className="cjm-inst-num">3</div>
                  <div className="cjm-inst-body">
                    <div className="cjm-inst-title">Enable required API scopes</div>
                    <div className="cjm-inst-desc">In the <strong>Permissions</strong> tab, add the <strong>Jira API</strong> and enable these scopes:</div>
                    <div className="cjm-scopes-grid">
                      {["read:jira-work", "write:jira-work", "read:jira-user", "read:me", "offline_access"].map((sc) => (
                        <span key={sc} className="cjm-scope-badge">{sc}</span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="cjm-instruction-item">
                  <div className="cjm-inst-num">4</div>
                  <div className="cjm-inst-body">
                    <div className="cjm-inst-title">Set the Callback / Redirect URL</div>
                    <div className="cjm-inst-desc">In the <strong>Authorization</strong> tab, add this exact redirect URI:</div>
                    <div className="cjm-copy-field">
                      <code>{REDIRECT_URI}</code>
                      <button className="cjm-copy-btn" onClick={handleCopyUri} title="Copy">
                        {copiedUri ? <Check size={13} color="#36b37e" /> : <Copy size={13} />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="cjm-info-callout">
                <Shield size={14} color="#36b37e" />
                <span>Your credentials are stored only on your local machine. All Jira data travels directly between your browser and Atlassian APIs — never via a third party.</span>
              </div>
            </div>
          )}

          {/* Step 2: Credentials */}
          {step === 2 && (
            <div className="cjm-step-content">
              <div className="cjm-step-icon-header">
                <div className="cjm-icon-circle purple"><Key size={22} /></div>
                <div>
                  <div className="cjm-step-heading">Enter Your OAuth Credentials</div>
                  <div className="cjm-step-desc">From your app on the Atlassian Developer Console, open <strong>Settings</strong> and copy the Client ID and Client Secret.</div>
                </div>
              </div>

              <div className="cjm-cred-guide">
                <span className="cjm-cred-guide-label">Where to find them:</span>
                <span className="cjm-cred-guide-path">Your App ? Settings ? App Details ? Client ID &amp; Secret</span>
              </div>

              <div className="cjm-form">
                <div className="cjm-form-group">
                  <label className="cjm-label"><Key size={13} /> Client ID <span className="cjm-required">*</span></label>
                  <input
                    type="text"
                    className={`cjm-input${error && !clientId.trim() ? " error" : ""}`}
                    placeholder="e.g. bTx5qVzmYntYX0fzRUIv..."
                    value={clientId}
                    onChange={(e) => { setClientId(e.target.value); setError(""); }}
                    spellCheck={false}
                  />
                  <div className="cjm-input-hint">32-character string from Atlassian Developer Console</div>
                </div>

                <div className="cjm-form-group">
                  <label className="cjm-label"><Lock size={13} /> Client Secret <span className="cjm-required">*</span></label>
                  <input
                    type="password"
                    className={`cjm-input${error && !clientSecret.trim() ? " error" : ""}`}
                    placeholder="ATOA1pSscYSmhtuKq51K..."
                    value={clientSecret}
                    onChange={(e) => { setClientSecret(e.target.value); setError(""); }}
                    spellCheck={false}
                  />
                  <div className="cjm-input-hint">Keep secret — never share publicly or commit to git</div>
                </div>

                {error && (
                  <div className="cjm-error-callout">
                    <AlertCircle size={14} /><span>{error}</span>
                  </div>
                )}
              </div>

              <div className="cjm-info-callout">
                <Shield size={14} color="#36b37e" />
                <span>Credentials are saved only to your local <code>.env</code> file. They are never transmitted anywhere except to Atlassian during OAuth authorization.</span>
              </div>
            </div>
          )}

          {/* Step 3: Authorize */}
          {step === 3 && (
            <div className="cjm-step-content">
              <div className="cjm-step-icon-header">
                <div className="cjm-icon-circle green"><CheckCircle2 size={22} /></div>
                <div>
                  <div className="cjm-step-heading">Authorize &amp; Launch</div>
                  <div className="cjm-step-desc">Click below to open Atlassian secure login. Approve access — you will be redirected back instantly.</div>
                </div>
              </div>

              <div className="cjm-flow-preview">
                <div className="cjm-flow-item">
                  <div className="cjm-flow-num">1</div>
                  <div className="cjm-flow-text">Atlassian sign-in opens in browser</div>
                </div>
                <div className="cjm-flow-arrow"><ArrowRight size={14} color="#8b949e" /></div>
                <div className="cjm-flow-item">
                  <div className="cjm-flow-num">2</div>
                  <div className="cjm-flow-text">Log in and approve requested permissions</div>
                </div>
                <div className="cjm-flow-arrow"><ArrowRight size={14} color="#8b949e" /></div>
                <div className="cjm-flow-item">
                  <div className="cjm-flow-num">3</div>
                  <div className="cjm-flow-text">Redirected back — workspace connected!</div>
                </div>
              </div>

              {error && (
                <div className="cjm-error-callout">
                  <AlertCircle size={14} /><span>{error}</span>
                </div>
              )}

              <div className="cjm-info-callout">
                <Sparkles size={14} color="#58a6ff" />
                <span>Once connected, you can query, create, and manage your real Jira Cloud projects, issues, and sprints using natural language — all safely gated before any write operation.</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="cjm-footer">
          <button className="cjm-btn-secondary" onClick={step === 1 ? onClose : () => setStep((s) => s - 1)}>
            {step === 1 ? <><X size={14} /> Cancel</> : <><ChevronLeft size={14} /> Back</>}
          </button>
          <div style={{ display: "flex", gap: 10 }}>
            {step < 3 && (
              <button className="cjm-btn-primary" onClick={advanceStep}>
                Next Step <ChevronRight size={14} />
              </button>
            )}
            {step === 3 && (
              <button className="cjm-btn-connect" onClick={handleConnect} disabled={loading}>
                {loading
                  ? <><Loader2 size={14} className="spinner" /> Connecting...</>
                  : <><Globe size={14} /> Authorize with Atlassian</>
                }
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
