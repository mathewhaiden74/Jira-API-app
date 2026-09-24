import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, ShieldCheck } from 'lucide-react';

import JiraIssueCard from './JiraIssueCard';
import ConfirmationDialog from './ConfirmationDialog';
import TestCaseCard from './TestCaseCard';
import BugAnalysisCard from './BugAnalysisCard';
import DuplicateAnalysisCard from './DuplicateAnalysisCard';

export default function Message({ message, onConfirmAction }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <div className={`message-avatar ${isUser ? 'user' : 'ai'}`}>
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      <div className="message-content-box">
        {/* Main Text / Markdown Bubble */}
        <div className="message-bubble">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content || message.message || ''}
          </ReactMarkdown>
        </div>

        {/* Action Confirmation Gate */}
        {message.confirmation_required && message.pending_action && (
          <ConfirmationDialog 
            pendingAction={message.pending_action}
            onConfirm={onConfirmAction}
          />
        )}

        {/* Jira Issue Cards Grid */}
        {message.issues && message.issues.length > 0 && (
          <div className="issues-grid-container">
            {message.issues.map((issue) => (
              <JiraIssueCard key={issue.key || issue.id} issue={issue} />
            ))}
          </div>
        )}

        {/* Structured Test Cases */}
        {message.test_cases && message.test_cases.length > 0 && (
          <TestCaseCard testCases={message.test_cases} />
        )}

        {/* Bug Analytics Dashboard */}
        {message.bug_analysis && (
          <BugAnalysisCard analysis={message.bug_analysis} />
        )}

        {/* Duplicate Bug Candidates */}
        {message.duplicate_analysis && (
          <DuplicateAnalysisCard duplicateAnalysis={message.duplicate_analysis} />
        )}
      </div>
    </div>
  );
}
