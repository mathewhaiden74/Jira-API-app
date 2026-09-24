import React, { useState } from 'react';
import { 
  ShieldAlert, Check, X, Loader2, Layers, Bug, CheckSquare, 
  Bookmark, GitCommit, Plus, Trash2, Sparkles, ListPlus
} from 'lucide-react';

export default function ConfirmationDialog({ pendingAction, onConfirm }) {
  const [loading, setLoading] = useState(false);
  const [responded, setResponded] = useState(false);

  if (!pendingAction || responded) return null;

  const action = pendingAction.action || 'CREATE_ISSUE';
  const initialParams = pendingAction.parameters || {};

  // Editable Form State
  const [summary, setSummary] = useState(initialParams.summary || '');
  const [issueType, setIssueType] = useState(initialParams.issue_type || (action === 'CREATE_MULTIPLE_SUBTASKS' ? 'Subtask' : 'Task'));
  const [priority, setPriority] = useState(initialParams.priority || 'Medium');
  const [projectKey, setProjectKey] = useState(initialParams.project_key || 'KAN');
  const [parentKey, setParentKey] = useState(initialParams.parent_key || '');
  const [description, setDescription] = useState(initialParams.description || '');
  const [assignee, setAssignee] = useState(initialParams.assignee || '');
  const [status, setStatus] = useState(initialParams.status || 'In Progress');
  const [commentBody, setCommentBody] = useState(initialParams.body || '');

  // Subtasks list for batch creation
  const defaultSubtasks = initialParams.subtasks 
    ? initialParams.subtasks.map(s => typeof s === 'string' ? { summary: s, priority: 'Medium' } : s)
    : (action === 'CREATE_MULTIPLE_SUBTASKS' ? [
        { summary: 'Backend API & Database Implementation', priority: 'High' },
        { summary: 'Frontend UI Integration & Components', priority: 'Medium' },
        { summary: 'Unit & Automated Integration Testing', priority: 'Medium' },
        { summary: 'API Documentation & Review', priority: 'Low' }
      ] : []);

  const [subtasks, setSubtasks] = useState(defaultSubtasks);
  const [showSubtaskSection, setShowSubtaskSection] = useState(action === 'CREATE_MULTIPLE_SUBTASKS' || defaultSubtasks.length > 0);

  const handleAddSubtaskRow = (subSummary = '', subPriority = 'Medium') => {
    setSubtasks(prev => [...prev, { summary: subSummary, priority: subPriority }]);
    setShowSubtaskSection(true);
  };

  const handleUpdateSubtaskRow = (index, field, value) => {
    setSubtasks(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleRemoveSubtaskRow = (index) => {
    setSubtasks(prev => prev.filter((_, idx) => idx !== index));
  };

  const handleLoadStandardStack = () => {
    const pKey = parentKey || summary || 'Task';
    setSubtasks([
      { summary: `Database Schema & Data Models for ${pKey}`, priority: 'High' },
      { summary: `Backend REST API Endpoints & Auth for ${pKey}`, priority: 'High' },
      { summary: `Frontend UI & Interactive States for ${pKey}`, priority: 'Medium' },
      { summary: `Automated Unit & E2E Testing for ${pKey}`, priority: 'Medium' },
      { summary: `Documentation & Staging Deployment for ${pKey}`, priority: 'Low' }
    ]);
    setShowSubtaskSection(true);
  };

  const handleAction = async (confirmed) => {
    setLoading(true);
    try {
      if (!confirmed) {
        await onConfirm(pendingAction.action_id, false);
      } else {
        const modified = { ...initialParams };
        
        if (action === 'CREATE_MULTIPLE_SUBTASKS') {
          modified.parent_key = parentKey.trim() || initialParams.parent_key || `${projectKey}-1`;
          modified.project_key = projectKey.trim() || initialParams.project_key;
          modified.subtasks = subtasks.filter(s => s.summary && s.summary.trim()).map(s => ({
            summary: s.summary.trim(),
            priority: s.priority || 'Medium'
          }));
        } else if (action === 'CREATE_ISSUE') {
          modified.summary = summary.trim() || initialParams.summary || 'New Issue';
          modified.issue_type = issueType;
          modified.priority = priority;
          modified.project_key = projectKey.trim() || initialParams.project_key;
          if (issueType.toLowerCase() === 'subtask' || parentKey.trim()) {
            modified.parent_key = parentKey.trim();
          }
          if (description.trim()) {
            modified.description = description.trim();
          }
          if (subtasks.length > 0) {
            modified.subtasks = subtasks.filter(s => s.summary && s.summary.trim()).map(s => ({
              summary: s.summary.trim(),
              priority: s.priority || 'Medium'
            }));
          }
        } else if (action === 'UPDATE_ISSUE') {
          modified.fields = { ...(initialParams.fields || {}) };
          if (summary) modified.fields.summary = summary;
          if (priority) modified.fields.priority = priority;
          if (description) modified.fields.description = description;
        } else if (action === 'ASSIGN_ISSUE') {
          modified.assignee = assignee.trim() || initialParams.assignee;
        } else if (action === 'TRANSITION_ISSUE') {
          modified.status = status;
        } else if (action === 'ADD_COMMENT') {
          modified.body = commentBody.trim() || initialParams.body;
        }

        await onConfirm(pendingAction.action_id, true, modified);
      }
      setResponded(true);
    } catch (err) {
      console.error('Confirmation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getIssueTypeIcon = (type) => {
    switch ((type || '').toLowerCase()) {
      case 'epic': return <Layers size={14} color="#0052cc" />;
      case 'bug': return <Bug size={14} color="#ff5630" />;
      case 'story': return <Bookmark size={14} color="#36b37e" />;
      case 'subtask':
      case 'sub-task': return <GitCommit size={14} color="#6554c0" />;
      default: return <CheckSquare size={14} color="#0065ff" />;
    }
  };

  const validSubtaskCount = subtasks.filter(s => s.summary && s.summary.trim()).length;

  return (
    <div className="confirmation-card interactive-gate">
      {/* Header */}
      <div className="confirmation-header">
        <div className="gate-title-wrap">
          <ShieldAlert size={18} color="#ffab00" />
          <span>
            {action === 'CREATE_MULTIPLE_SUBTASKS' 
              ? 'Safety Gate: 1-Click Multi-Subtask Creation' 
              : 'Safety Gate: Confirm Jira Modification'}
          </span>
        </div>
        <div className="action-tag">
          {action}
        </div>
      </div>

      {/* Interactive Editor Body */}
      <div className="confirmation-editor-body">
        
        {/* 1. BATCH MULTIPLE SUBTASKS CREATION */}
        {action === 'CREATE_MULTIPLE_SUBTASKS' && (
          <div className="edit-form-grid">
            {/* Parent Key */}
            <div className="form-field full-width">
              <label className="field-label">
                <span>Parent Issue Key *</span>
                <span className="field-hint">All subtasks will be attached to this issue</span>
              </label>
              <input 
                type="text" 
                className="edit-input highlight-parent" 
                value={parentKey} 
                onChange={(e) => setParentKey(e.target.value.toUpperCase())}
                placeholder="e.g. KAN-1"
              />
            </div>

            {/* Subtasks Multi-Row Editor */}
            <div className="subtasks-batch-container full-width">
              <div className="subtasks-batch-header">
                <div className="batch-title">
                  <ListPlus size={15} color="#58a6ff" />
                  <span>Subtasks to Create ({validSubtaskCount})</span>
                </div>
                <button 
                  type="button" 
                  className="btn-preset-stack"
                  onClick={handleLoadStandardStack}
                >
                  <Sparkles size={12} />
                  <span>Insert Full Stack Template</span>
                </button>
              </div>

              <div className="subtask-rows-list">
                {subtasks.map((st, idx) => (
                  <div key={idx} className="subtask-edit-row">
                    <div className="subtask-num">#{idx + 1}</div>
                    <input 
                      type="text" 
                      className="edit-input subtask-title-input" 
                      value={st.summary} 
                      onChange={(e) => handleUpdateSubtaskRow(idx, 'summary', e.target.value)}
                      placeholder={`Subtask #${idx + 1} title (e.g. API validation, QA tests...)`}
                    />
                    <select 
                      className="edit-select subtask-prio-select"
                      value={st.priority || 'Medium'}
                      onChange={(e) => handleUpdateSubtaskRow(idx, 'priority', e.target.value)}
                    >
                      <option value="Highest">Highest (P0)</option>
                      <option value="High">High (P1)</option>
                      <option value="Medium">Medium (P2)</option>
                      <option value="Low">Low (P3)</option>
                    </select>
                    <button 
                      type="button" 
                      className="btn-remove-subtask"
                      onClick={() => handleRemoveSubtaskRow(idx)}
                      title="Remove subtask"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>

              <button 
                type="button" 
                className="btn-add-subtask-row"
                onClick={() => handleAddSubtaskRow()}
              >
                <Plus size={14} />
                <span>Add Another Subtask</span>
              </button>
            </div>
          </div>
        )}

        {/* 2. SINGLE ISSUE CREATION (WITH OPTIONAL SIMULTANEOUS SUBTASKS) */}
        {action === 'CREATE_ISSUE' && (
          <div className="edit-form-grid">
            {/* Title / Summary Heading Field */}
            <div className="form-field full-width">
              <label className="field-label">
                <span>Issue Title / Heading</span>
                <span className="field-hint">Edit title before creating</span>
              </label>
              <input 
                type="text" 
                className="edit-input title-input" 
                value={summary} 
                onChange={(e) => setSummary(e.target.value)}
                placeholder="e.g. Core Platform Architecture Migration"
              />
            </div>

            {/* Issue Type Selector */}
            <div className="form-field">
              <label className="field-label">
                <span>Issue Type</span>
              </label>
              <div className="select-with-icon">
                {getIssueTypeIcon(issueType)}
                <select 
                  className="edit-select"
                  value={issueType}
                  onChange={(e) => {
                    const newType = e.target.value;
                    setIssueType(newType);
                    if (newType.toLowerCase() === 'subtask' && !parentKey) {
                      setParentKey(`${projectKey}-1`);
                    }
                  }}
                >
                  <option value="Epic">Epic</option>
                  <option value="Task">Task</option>
                  <option value="Story">Story</option>
                  <option value="Bug">Bug</option>
                  <option value="Subtask">Subtask</option>
                </select>
              </div>
            </div>

            {/* Priority Selector */}
            <div className="form-field">
              <label className="field-label">
                <span>Priority</span>
              </label>
              <select 
                className="edit-select"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="Highest">Highest (P0)</option>
                <option value="High">High (P1)</option>
                <option value="Medium">Medium (P2)</option>
                <option value="Low">Low (P3)</option>
                <option value="Lowest">Lowest (P4)</option>
              </select>
            </div>

            {/* Target Project */}
            <div className="form-field">
              <label className="field-label">
                <span>Target Project</span>
              </label>
              <input 
                type="text" 
                className="edit-input" 
                value={projectKey} 
                onChange={(e) => setProjectKey(e.target.value.toUpperCase())}
                placeholder="e.g. KAN"
              />
            </div>

            {/* Parent Issue Key (For Subtasks) */}
            {(issueType.toLowerCase() === 'subtask' || parentKey) && (
              <div className="form-field">
                <label className="field-label">
                  <span>Parent Issue Key *</span>
                  <span className="field-hint">Required for Subtask</span>
                </label>
                <input 
                  type="text" 
                  className="edit-input highlight-parent" 
                  value={parentKey} 
                  onChange={(e) => setParentKey(e.target.value.toUpperCase())}
                  placeholder="e.g. KAN-1"
                />
              </div>
            )}

            {/* Optional Description */}
            <div className="form-field full-width">
              <label className="field-label">
                <span>Description / Details (Optional)</span>
              </label>
              <textarea 
                className="edit-textarea"
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Additional notes or acceptance criteria..."
              />
            </div>

            {/* Optional Subtasks simultaneously with this issue */}
            {issueType.toLowerCase() !== 'subtask' && (
              <div className="subtasks-batch-container full-width">
                <div className="subtasks-batch-header">
                  <div className="batch-title">
                    <ListPlus size={15} color="#58a6ff" />
                    <span>Create Subtasks Simultaneously ({subtasks.length})</span>
                  </div>
                  <button 
                    type="button" 
                    className="btn-preset-stack"
                    onClick={() => {
                      if (!showSubtaskSection || subtasks.length === 0) {
                        handleLoadStandardStack();
                      } else {
                        handleAddSubtaskRow();
                      }
                    }}
                  >
                    <Plus size={12} />
                    <span>Add Subtasks</span>
                  </button>
                </div>

                {showSubtaskSection && subtasks.length > 0 && (
                  <>
                    <div className="subtask-rows-list">
                      {subtasks.map((st, idx) => (
                        <div key={idx} className="subtask-edit-row">
                          <div className="subtask-num">#{idx + 1}</div>
                          <input 
                            type="text" 
                            className="edit-input subtask-title-input" 
                            value={st.summary} 
                            onChange={(e) => handleUpdateSubtaskRow(idx, 'summary', e.target.value)}
                            placeholder={`Subtask #${idx + 1} title`}
                          />
                          <select 
                            className="edit-select subtask-prio-select"
                            value={st.priority || 'Medium'}
                            onChange={(e) => handleUpdateSubtaskRow(idx, 'priority', e.target.value)}
                          >
                            <option value="Highest">Highest</option>
                            <option value="High">High</option>
                            <option value="Medium">Medium</option>
                            <option value="Low">Low</option>
                          </select>
                          <button 
                            type="button" 
                            className="btn-remove-subtask"
                            onClick={() => handleRemoveSubtaskRow(idx)}
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      ))}
                    </div>
                    <button 
                      type="button" 
                      className="btn-add-subtask-row"
                      onClick={() => handleAddSubtaskRow()}
                    >
                      <Plus size={14} />
                      <span>Add Another Subtask</span>
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {/* 3. UPDATE ISSUE */}
        {action === 'UPDATE_ISSUE' && (
          <div className="edit-form-grid">
            <div className="form-field full-width">
              <label className="field-label">Updating Issue: <strong>{pendingAction.issue_key}</strong></label>
            </div>
            <div className="form-field">
              <label className="field-label">Priority</label>
              <select className="edit-select" value={priority} onChange={(e) => setPriority(e.target.value)}>
                <option value="Highest">Highest</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
            <div className="form-field full-width">
              <label className="field-label">Summary</label>
              <input className="edit-input" value={summary} onChange={(e) => setSummary(e.target.value)} />
            </div>
          </div>
        )}

        {/* 4. ASSIGN ISSUE */}
        {action === 'ASSIGN_ISSUE' && (
          <div className="edit-form-grid">
            <div className="form-field full-width">
              <label className="field-label">Assign Issue <strong>{pendingAction.issue_key}</strong> to:</label>
              <input className="edit-input" value={assignee} onChange={(e) => setAssignee(e.target.value)} placeholder="User display name or email" />
            </div>
          </div>
        )}

        {/* 5. TRANSITION ISSUE */}
        {action === 'TRANSITION_ISSUE' && (
          <div className="edit-form-grid">
            <div className="form-field full-width">
              <label className="field-label">Move <strong>{pendingAction.issue_key}</strong> to Status:</label>
              <select className="edit-select" value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="In Progress">In Progress</option>
                <option value="Done">Done</option>
                <option value="In Review">In Review</option>
                <option value="To Do">To Do</option>
              </select>
            </div>
          </div>
        )}

        {/* 6. ADD COMMENT */}
        {action === 'ADD_COMMENT' && (
          <div className="edit-form-grid">
            <div className="form-field full-width">
              <label className="field-label">Comment to post on <strong>{pendingAction.issue_key}</strong>:</label>
              <textarea className="edit-textarea" rows={3} value={commentBody} onChange={(e) => setCommentBody(e.target.value)} />
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
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
          <span>
            {action === 'CREATE_MULTIPLE_SUBTASKS' 
              ? `Confirm & Create All (${validSubtaskCount}) Subtasks in 1 Click` 
              : (subtasks.length > 0 && issueType.toLowerCase() !== 'subtask'
                  ? `Confirm & Create Issue + ${validSubtaskCount} Subtasks`
                  : 'Confirm & Execute')}
          </span>
        </button>
      </div>
    </div>
  );
}
