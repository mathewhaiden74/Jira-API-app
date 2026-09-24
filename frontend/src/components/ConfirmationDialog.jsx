import React, { useState } from 'react';
import { ShieldAlert, Check, X, Loader2 } from 'lucide-react';

export default function ConfirmationDialog({ pendingAction, onConfirm }) {
  const [loading, setLoading] = useState(false);
  const [responded, setResponded] = useState(false);

  if (!pendingAction || responded) return null;

  const handleAction = async (confirmed) => {
    setLoading(true);
    try {
      await onConfirm(pendingAction.action_id, confirmed);
      setResponded(true);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="confirmation-card">
      <div className="confirmation-header">
        <ShieldAlert size={18} />
        <span>Safety Gate: Jira Modification Confirmation Required</span>
      </div>

      <div className="confirmation-body">
        <div style={{ fontWeight: 600, marginBottom: 6 }}>
          Action: <span style={{ color: '#58a6ff' }}>{pendingAction.action}</span>
        </div>
        <div>{pendingAction.summary_text}</div>
      </div>

      <div className="confirmation-actions">
        <button 
          className="btn-cancel" 
          onClick={() => handleAction(false)}
          disabled={loading}
        >
          <X size={14} />
          <span>Cancel</span>
        </button>

        <button 
          className="btn-confirm" 
          onClick={() => handleAction(true)}
          disabled={loading}
        >
          {loading ? <Loader2 size={14} className="spinner" /> : <Check size={14} />}
          <span>Confirm & Execute</span>
        </button>
      </div>
    </div>
  );
}
