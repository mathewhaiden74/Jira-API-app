import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Layers, ShieldCheck, Terminal, AlertCircle } from 'lucide-react';
import Message from './Message';

export default function Chat({
  messages,
  loading,
  onSendMessage,
  onConfirmAction,
  authStatus,
  selectedProject,
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;
    const msg = input;
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    onSendMessage(msg);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputResize = (e) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  // Use real project key for example prompts
  const projKey = selectedProject || 'YOUR-PROJECT';
  const exampleIssue1 = `${projKey}-1`;
  const exampleIssue2 = `${projKey}-2`;

  const promptExamples = [
    {
      category: 'Create Multiple Subtasks (1-Click)',
      text: `Create subtasks for ${exampleIssue1}: 1. Implement token validation 2. Write unit tests 3. Add API documentation`,
    },
    {
      category: 'Create Subtask',
      text: `Create a subtask for ${exampleIssue1} with summary: Implement token validation.`,
    },
    {
      category: 'Create Epic',
      text: `Create an epic for User Authentication System in ${projKey}.`,
    },
    {
      category: 'Create Bug / Task',
      text: `Create a bug for login failure in ${projKey}.`,
    },
    {
      category: 'Search & Triage',
      text: `Show me all open bugs in project ${projKey}.`,
    },
    {
      category: 'Assigned Work',
      text: `Show P0 and P1 bugs assigned to me in ${projKey}.`,
    },
    {
      category: 'Status Transition',
      text: `Move ${exampleIssue1} to In Progress.`,
    },
    {
      category: 'AI Test Design',
      text: `Generate test cases for ${exampleIssue2}.`,
    },
    {
      category: 'Sprint Health',
      text: `Give me a summary of this sprint for ${projKey}.`,
    },
  ];

  return (
    <div className="main-container">
      {/* Top Header */}
      <header className="chat-header">
        <div className="header-left">
          <div className="header-title">
            {selectedProject ? `Project: ${selectedProject}` : 'Jira AI Assistant Workspace'}
          </div>
          <div className="badge-tag">
            <span className="dot" style={{ background: '#36b37e' }} />
            <span>Jira Cloud REST v3</span>
          </div>
        </div>

        <div className="header-right">
          <div className="badge-tag" title="AI Model">
            <Sparkles size={13} color="#a371f7" />
            <span>OpenAI GPT-4o Engine</span>
          </div>
          <div className="badge-tag" title="Safety Gate Active">
            <ShieldCheck size={13} color="#36b37e" />
            <span>Write Safety Guard</span>
          </div>
        </div>
      </header>

      {/* Messages Scroll Area */}
      <div className="messages-viewport">
        <div className="messages-inner-wrap">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon-box">
                <svg width="34" height="34" viewBox="0 0 24 24" fill="white">
                  <path d="M11.53 2c0 2.4 1.97 4.35 4.35 4.35h1.78v1.7c0 2.4 1.94 4.34 4.34 4.35V2.84C22 2.38 21.62 2 21.16 2H11.53zm-5.6 5.88c0 2.4 1.97 4.35 4.35 4.35h1.78v1.7c0 2.4 1.94 4.35 4.34 4.35V8.72c0-.46-.38-.84-.84-.84H5.93zm-5.6 5.88c0 2.4 1.97 4.35 4.35 4.35h1.78v1.7c0 2.4 1.94 4.35 4.34 4.35V14.6c0-.46-.38-.84-.84-.84H.33z"/>
                </svg>
              </div>

              <h1 className="welcome-title">What would you like to do in Jira?</h1>
              <p className="welcome-desc">
                Interact with your Jira Cloud issues, sprints, and requirements using natural language. Query data, generate test cases, analyze bugs, or execute verified changes safely.
              </p>

              <div className="prompts-grid">
                {promptExamples.map((item, idx) => (
                  <div 
                    key={idx} 
                    className="prompt-card"
                    onClick={() => onSendMessage(item.text)}
                  >
                    <span className="prompt-category">{item.category}</span>
                    <span className="prompt-text">"{item.text}"</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <Message 
                key={idx} 
                message={msg} 
                onConfirmAction={onConfirmAction}
              />
            ))
          )}

          {loading && (
            <div className="message-row assistant">
              <div className="message-avatar ai">
                <Sparkles size={18} />
              </div>
              <div className="message-content-box">
                <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-secondary)' }}>
                  <div className="spinner" />
                  <span>Querying Jira API & synthesizing response...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Form Bar */}
      <div className="chat-input-container">
        <form className="input-box-wrapper" onSubmit={handleSend}>
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            rows={1}
            value={input}
            onChange={handleInputResize}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your Jira (e.g. 'Show open bugs', 'Create a bug...', 'Generate test cases for PROJ-125')..."
          />

          <button 
            type="submit" 
            className="btn-send-message"
            disabled={!input.trim() || loading}
            title="Send request"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
