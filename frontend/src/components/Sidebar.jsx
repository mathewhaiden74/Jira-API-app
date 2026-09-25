import React, { useState } from 'react';
import { 
  Plus, MessageSquare, Layers,
  Sparkles, Bug, BarChart3, Search, LogIn, LogOut
} from 'lucide-react';
import ConnectJiraModal from './ConnectJiraModal';

export default function Sidebar({
  authStatus,
  projects,
  selectedProject,
  onSelectProject,
  onNewChat,
  onQuickPrompt,
  onLogin,
  onLogout,
  onToggleDemo
}) {
  const [showConnectModal, setShowConnectModal] = useState(false);
  const isAuth = authStatus?.is_authenticated;
  const isDemo = authStatus?.is_mock_mode;
  const user = authStatus?.user;

  // Use selected project key for prompts, fallback to first project or generic
  const projKey = selectedProject || (projects && projects[0]?.key) || 'YOUR-PROJECT';
  // Build example issue keys from the selected project
  const exampleIssue1 = `${projKey}-1`;
  const exampleIssue2 = `${projKey}-2`;

  const quickFeatures = [
    { label: 'Show Open Bugs', prompt: `Show me all open bugs in project ${projKey}.`, icon: <Bug size={15} color="#ff7452" /> },
    { label: 'My P0/P1 Bugs', prompt: `Show P0 and P1 bugs assigned to me in ${projKey}.`, icon: <Bug size={15} color="#ff5630" /> },
    { label: 'Create Epic', prompt: `Create an epic for Core Platform Architecture in ${projKey}.`, icon: <Layers size={15} color="#0052cc" /> },
    { label: 'Create Subtask', prompt: `Create a subtask for ${exampleIssue1} with summary: Implement unit test coverage.`, icon: <Plus size={15} color="#36b37e" /> },
    { label: 'Breakdown Subtasks', prompt: `Break down ${exampleIssue1} into subtasks: 1. DB Schema 2. Backend API 3. Frontend UI 4. QA Tests.`, icon: <Sparkles size={15} color="#58a6ff" /> },
    { label: 'Sprint Summary', prompt: `Give me a summary of this sprint for ${projKey}.`, icon: <BarChart3 size={15} color="#0B66E4" /> },
    { label: 'Generate Test Cases', prompt: `Generate test cases for ${exampleIssue2}.`, icon: <Sparkles size={15} color="#a371f7" /> },
    { label: 'Bug Analysis', prompt: `Analyze bugs from this sprint in ${projKey}.`, icon: <BarChart3 size={15} color="#36b37e" /> },
    { label: 'Find Duplicate Bugs', prompt: `Find duplicate or similar bugs for ${exampleIssue1}.`, icon: <Search size={15} color="#ffab00" /> },
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="logo-wrap">
          <div className="jira-icon-badge">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
              <path d="M11.53 2c0 2.4 1.97 4.35 4.35 4.35h1.78v1.7c0 2.4 1.94 4.34 4.34 4.35V2.84C22 2.38 21.62 2 21.16 2H11.53zm-5.6 5.88c0 2.4 1.97 4.35 4.35 4.35h1.78v1.7c0 2.4 1.94 4.35 4.34 4.35V8.72c0-.46-.38-.84-.84-.84H5.93zm-5.6 5.88c0 2.4 1.97 4.35 4.35 4.35h1.78v1.7c0 2.4 1.94 4.35 4.34 4.35V14.6c0-.46-.38-.84-.84-.84H.33z"/>
            </svg>
          </div>
          <span>Jira AI Assistant</span>
          <span className="ai-pill">v1.0</span>
        </div>
      </div>

      {/* New Chat Button */}
      <button className="btn-new-chat" onClick={onNewChat}>
        <Plus size={16} />
        <span>New Conversation</span>
      </button>

      {/* Scrollable Section */}
      <div className="sidebar-section">
        {/* Project Selector */}
        <div className="section-title">Active Project Context</div>
        <select 
          className="project-select-box"
          value={selectedProject || ''}
          onChange={(e) => onSelectProject(e.target.value)}
        >
          <option value="">All Visible Projects</option>
          {projects && projects.map((p) => (
            <option key={p.id || p.key} value={p.key}>
              {p.key} - {p.name}
            </option>
          ))}
        </select>

        {/* Quick Features */}
        <div className="section-title">Quick Actions</div>
        <div className="quick-action-list">
          {quickFeatures.map((item, idx) => (
            <button 
              key={idx} 
              className="quick-action-btn"
              onClick={() => onQuickPrompt(item.prompt)}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>

        {/* Chat History */}
        <div className="section-title">Recent Conversations</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <div className="history-item active">
            <MessageSquare size={14} />
            <span>Sprint 24 Triage & Bugs</span>
          </div>
          <div className="history-item" onClick={() => onQuickPrompt('Generate test cases for PROJ-125.')}>
            <MessageSquare size={14} />
            <span>PROJ-125 Test Generation</span>
          </div>
          <div className="history-item" onClick={() => onQuickPrompt('Find duplicate bugs for PROJ-123.')}>
            <MessageSquare size={14} />
            <span>OAuth Bug Deduplication</span>
          </div>
        </div>
      </div>

      {/* Footer / User Profile & Auth Connection */}
      <div className="sidebar-footer">
        <div className="connection-card">
          <div className="user-profile-row">
            {user?.avatarUrl ? (
              <img src={user.avatarUrl} alt="Avatar" className="user-avatar" />
            ) : (
              <div className="user-avatar" style={{ background: '#21262d', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Layers size={16} color="#8b949e" />
              </div>
            )}
            <div className="user-meta">
              <div className="user-name">{user?.displayName || 'Not Connected'}</div>
              <div className="user-site">{authStatus?.site_name || 'No Jira site attached'}</div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 2 }}>
            <span className={`status-indicator-badge ${isAuth ? (isDemo ? 'demo' : 'connected') : 'disconnected'}`}>
              <span className="dot" />
              {isAuth ? (isDemo ? 'Demo Mode' : 'Connected') : 'Disconnected'}
            </span>
          </div>

          {isAuth ? (
            <button className="btn-auth-action disconnect" onClick={onLogout}>
              <LogOut size={13} />
              <span>Disconnect Jira</span>
            </button>
          ) : (
            <>
              <button className="btn-auth-action connect" onClick={() => setShowConnectModal(true)}>
                <LogIn size={13} />
                <span>Connect Jira Cloud</span>
              </button>
              {!isAuth && (
                <button
                  className="btn-auth-action"
                  style={{ background: 'transparent', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', marginTop: 4 }}
                  onClick={onToggleDemo}
                >
                  <Sparkles size={13} />
                  <span>Try Demo Mode</span>
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {showConnectModal && (
        <ConnectJiraModal onClose={() => setShowConnectModal(false)} />
      )}
    </aside>
  );
}
