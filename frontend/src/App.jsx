import React, { useState, useEffect } from 'react';
import { api } from './api';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';

export default function App() {
  const [authStatus, setAuthStatus] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load initial Auth & Projects
  const fetchStatusAndProjects = async () => {
    try {
      const status = await api.getAuthStatus();
      setAuthStatus(status);

      if (status.is_authenticated) {
        const projs = await api.getProjects();
        setProjects(projs || []);
        if (projs && projs.length > 0) {
          setSelectedProject((prev) => prev || projs[0].key);
        }
      }
    } catch (err) {
      console.error('Failed to load initial status:', err);
    }
  };

  useEffect(() => {
    fetchStatusAndProjects();

    // Check for query params from OAuth redirects
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth_success') || params.get('mock_auth_success')) {
      window.history.replaceState({}, document.title, window.location.pathname);
      fetchStatusAndProjects();
    }
  }, []);

  const handleSendMessage = async (text) => {
    const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await api.sendMessage(text, 'default_user', selectedProject);
      setMessages((prev) => [...prev, response]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          message: `⚠️ **Error connecting to Jira Assistant API**: ${err.message}`,
          action: 'ERROR',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAction = async (actionId, confirmed, modifiedParameters = null) => {
    setLoading(true);
    try {
      const response = await api.confirmAction(actionId, confirmed, 'default_user', modifiedParameters);
      setMessages((prev) => [...prev, response]);
    } catch (err) {
      console.error('Confirm error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          message: `⚠️ **Failed to process action**: ${err.message}`,
          action: 'ERROR',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  const handleLogin = () => {
    window.location.href = api.getLoginUrl();
  };

  const handleLogout = async () => {
    try {
      await api.logout();
      setAuthStatus(null);
      setProjects([]);
      setMessages([]);
      await fetchStatusAndProjects();
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  const handleToggleDemo = async () => {
    try {
      const status = await api.enableDemoMode();
      setAuthStatus(status);
      const projs = await api.getProjects();
      setProjects(projs || []);
    } catch (err) {
      console.error('Demo toggle error:', err);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar 
        authStatus={authStatus}
        projects={projects}
        selectedProject={selectedProject}
        onSelectProject={setSelectedProject}
        onNewChat={handleNewChat}
        onQuickPrompt={handleSendMessage}
        onLogin={handleLogin}
        onLogout={handleLogout}
        onToggleDemo={handleToggleDemo}
      />

      <Chat 
        messages={messages}
        loading={loading}
        onSendMessage={handleSendMessage}
        onConfirmAction={handleConfirmAction}
        authStatus={authStatus}
        selectedProject={selectedProject}
      />
    </div>
  );
}
