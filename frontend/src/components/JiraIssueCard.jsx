import React from 'react';
import { ExternalLink, AlertCircle, CheckCircle2, Clock, User, Tag } from 'lucide-react';

export default function JiraIssueCard({ issue }) {
  if (!issue) return null;

  const getStatusClass = (status) => {
    const name = (status?.name || '').toLowerCase();
    const cat = (status?.category || '').toLowerCase();
    if (name.includes('done') || name.includes('resolved') || name.includes('closed') || cat === 'done') {
      return 'done';
    }
    if (name.includes('progress') || name.includes('review') || cat === 'indeterminate') {
      return 'inprogress';
    }
    return 'todo';
  };

  const getPriorityClass = (priority) => {
    const name = (priority?.name || '').toLowerCase();
    if (name.includes('p0') || name.includes('highest')) return 'p0';
    if (name.includes('p1') || name.includes('high')) return 'p1';
    if (name.includes('p2') || name.includes('medium')) return 'p2';
    return 'low';
  };

  return (
    <div className="jira-issue-card">
      <div className="issue-top-row">
        <a 
          href={issue.url || `https://jira.atlassian.com/browse/${issue.key}`} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="issue-key-badge"
          title="View in Jira Cloud"
        >
          <span>{issue.key}</span>
          <ExternalLink size={12} />
        </a>
        <span className={`status-badge ${getStatusClass(issue.status)}`}>
          {issue.status?.name || 'Open'}
        </span>
      </div>

      <div className="issue-summary">
        {issue.summary}
      </div>

      <div className="issue-meta-row">
        <span className={`priority-pill ${getPriorityClass(issue.priority)}`}>
          <AlertCircle size={12} />
          {issue.priority?.name || 'Medium'}
        </span>

        <div className="assignee-chip" title={`Assignee: ${issue.assignee?.displayName || 'Unassigned'}`}>
          {issue.assignee?.avatarUrl ? (
            <img 
              src={issue.assignee.avatarUrl} 
              alt={issue.assignee.displayName} 
              style={{ width: 18, height: 18, borderRadius: '50%' }}
            />
          ) : (
            <User size={13} color="#8b949e" />
          )}
          <span style={{ maxWidth: 110, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {issue.assignee?.displayName || 'Unassigned'}
          </span>
        </div>
      </div>

      {issue.components && issue.components.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 2 }}>
          {issue.components.map((comp, idx) => (
            <span 
              key={idx} 
              style={{ 
                fontSize: 10.5, 
                padding: '2px 6px', 
                background: 'rgba(255,255,255,0.06)', 
                borderRadius: 4, 
                color: '#8b949e',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4
              }}
            >
              <Tag size={10} />
              {comp}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
