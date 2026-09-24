import React from 'react';
import { BarChart3, AlertOctagon, CheckCircle2, Clock, Layers } from 'lucide-react';

export default function BugAnalysisCard({ analysis }) {
  if (!analysis) return null;

  return (
    <div className="analysis-dashboard-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, fontSize: 14 }}>
        <BarChart3 size={16} color="#0B66E4" />
        <span>Jira Bug Metrics & Distribution</span>
      </div>

      <div className="metrics-row">
        <div className="metric-item">
          <div className="metric-val">{analysis.total_bugs}</div>
          <div className="metric-lbl">Total Bugs</div>
        </div>
        <div className="metric-item">
          <div className="metric-val p0">{analysis.highest_priority_count}</div>
          <div className="metric-lbl">P0 / High</div>
        </div>
        <div className="metric-item">
          <div className="metric-val open">{analysis.open_bugs + analysis.in_progress_bugs}</div>
          <div className="metric-lbl">Open / Active</div>
        </div>
        <div className="metric-item">
          <div className="metric-val resolved">{analysis.resolved_bugs}</div>
          <div className="metric-lbl">Resolved</div>
        </div>
      </div>

      {/* Breakdown by Assignee */}
      {analysis.bugs_by_assignee && Object.keys(analysis.bugs_by_assignee).length > 0 && (
        <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>
            Bugs by Assignee
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {Object.entries(analysis.bugs_by_assignee).map(([assignee, count]) => {
              const pct = Math.round((count / Math.max(analysis.total_bugs, 1)) * 100);
              return (
                <div key={assignee} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12.5 }}>
                  <div style={{ width: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{assignee}</div>
                  <div style={{ flex: 1, background: 'rgba(255,255,255,0.06)', height: 8, borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, background: '#0B66E4', height: '100%' }} />
                  </div>
                  <div style={{ width: 40, textAlign: 'right', fontWeight: 600, color: '#8b949e' }}>{count} ({pct}%)</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
