import React from 'react';
import { Copy, AlertTriangle, ExternalLink, ArrowRight } from 'lucide-react';

export default function DuplicateAnalysisCard({ duplicateAnalysis }) {
  if (!duplicateAnalysis || !duplicateAnalysis.candidates || duplicateAnalysis.candidates.length === 0) {
    return null;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: '#f0f6fc', display: 'flex', alignItems: 'center', gap: 6 }}>
        <AlertTriangle size={15} color="#ffab00" />
        <span>Potential Duplicate Candidate Tickets for `{duplicateAnalysis.target_issue_key}`</span>
      </div>

      {duplicateAnalysis.candidates.map((cand) => (
        <div key={cand.issue_key} className="duplicate-candidate-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <a 
              href={`https://jira.atlassian.com/browse/${cand.issue_key}`}
              target="_blank" 
              rel="noopener noreferrer"
              className="issue-key-badge"
            >
              <span>{cand.issue_key}</span>
              <ExternalLink size={12} />
            </a>

            <div className="similarity-gauge">
              <span>Similarity Score:</span>
              <span style={{ 
                color: cand.similarity_score > 75 ? '#ff5630' : '#ffab00',
                fontSize: 13,
                fontWeight: 800
              }}>
                {cand.similarity_score}%
              </span>
            </div>
          </div>

          <div style={{ fontWeight: 600, fontSize: 13.5, color: 'var(--text-primary)' }}>
            {cand.summary}
          </div>

          <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', background: 'rgba(0,0,0,0.2)', padding: 10, borderRadius: 6 }}>
            <div style={{ marginBottom: 4, color: '#e6edf3' }}>
              <strong>AI Match Reason:</strong> {cand.similarity_reason}
            </div>
            {cand.possible_duplicate_explanation && (
              <div style={{ color: '#8b949e', fontStyle: 'italic' }}>
                💡 {cand.possible_duplicate_explanation}
              </div>
            )}
          </div>

          {cand.matching_symptoms && cand.matching_symptoms.length > 0 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {cand.matching_symptoms.map((symptom, idx) => (
                <span key={idx} style={{ fontSize: 11, background: 'rgba(255, 171, 0, 0.1)', color: '#ffab00', padding: '2px 8px', borderRadius: 4 }}>
                  ✓ {symptom}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
