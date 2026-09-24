const API_BASE = 'http://localhost:8000';

/**
 * Custom fetch wrapper with error parsing
 */
async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = 'Network response error';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  // Authentication & Session
  async getAuthStatus(sessionId = 'default_user') {
    return request(`/auth/status?session_id=${encodeURIComponent(sessionId)}`);
  },

  async logout(sessionId = 'default_user') {
    return request(`/auth/logout?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'POST',
    });
  },

  async enableDemoMode(sessionId = 'default_user') {
    return request(`/auth/demo-mode?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'POST',
    });
  },

  getLoginUrl(sessionId = 'default_user') {
    return `${API_BASE}/auth/login?session_id=${encodeURIComponent(sessionId)}`;
  },

  // Jira AI Chat & Commands
  async sendMessage(message, sessionId = 'default_user', projectContext = null) {
    return request('/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        message,
        session_id: sessionId,
        project_context: projectContext,
      }),
    });
  },

  async confirmAction(actionId, confirmed, sessionId = 'default_user') {
    return request('/chat/confirm', {
      method: 'POST',
      body: JSON.stringify({
        action_id: actionId,
        confirmed,
        session_id: sessionId,
      }),
    });
  },

  async getExamplePrompts() {
    return request('/chat/examples');
  },

  // Jira Direct Operations
  async getProjects(sessionId = 'default_user') {
    return request(`/jira/projects?session_id=${encodeURIComponent(sessionId)}`);
  },

  async getIssue(issueKey, sessionId = 'default_user') {
    return request(`/jira/issues/${encodeURIComponent(issueKey)}?session_id=${encodeURIComponent(sessionId)}`);
  },

  async searchIssues(jql, sessionId = 'default_user') {
    return request(`/jira/issues?jql=${encodeURIComponent(jql)}&session_id=${encodeURIComponent(sessionId)}`);
  },

  async getSprints(projectKey = null, sessionId = 'default_user') {
    const url = projectKey
      ? `/jira/sprints?project_key=${encodeURIComponent(projectKey)}&session_id=${encodeURIComponent(sessionId)}`
      : `/jira/sprints?session_id=${encodeURIComponent(sessionId)}`;
    return request(url);
  },
};
