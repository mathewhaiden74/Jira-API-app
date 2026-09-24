import React, { useState } from 'react';
import { Copy, Check, FileText, Download } from 'lucide-react';

export default function TestCaseCard({ testCases }) {
  const [copied, setCopied] = useState(false);

  if (!testCases || testCases.length === 0) return null;

  const copyAsMarkdown = () => {
    let md = '# Test Cases\n\n| ID | Title | Type | Priority | Expected Result |\n|---|---|---|---|---|\n';
    testCases.forEach(tc => {
      md += `| ${tc.id} | ${tc.title} | ${tc.type} | ${tc.priority} | ${tc.expected_result} |\n`;
    });
    md += '\n## Detailed Steps\n\n';
    testCases.forEach(tc => {
      md += `### ${tc.id}: ${tc.title}\n`;
      md += `- **Type**: ${tc.type} | **Priority**: ${tc.priority}\n`;
      md += `- **Preconditions**: ${tc.preconditions || 'None'}\n`;
      md += `- **Test Data**: ${tc.test_data || 'N/A'}\n`;
      md += `- **Steps**:\n`;
      (tc.steps || []).forEach((s, idx) => {
        md += `  ${idx + 1}. ${s}\n`;
      });
      md += `- **Expected Result**: ${tc.expected_result}\n\n`;
    });

    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const exportAsJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(testCases, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `test_cases_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="test-cases-container">
      <div className="test-cases-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, fontSize: 14 }}>
          <FileText size={16} color="#0B66E4" />
          <span>Structured Test Cases ({testCases.length})</span>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn-copy-test-cases" onClick={copyAsMarkdown} title="Copy as Markdown table">
            {copied ? <Check size={13} color="#36b37e" /> : <Copy size={13} />}
            <span>{copied ? 'Copied MD' : 'Copy Table'}</span>
          </button>
          <button className="btn-copy-test-cases" onClick={exportAsJSON} title="Download JSON">
            <Download size={13} />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="test-cases-table">
          <thead>
            <tr>
              <th style={{ width: 80 }}>ID</th>
              <th>Test Title & Scenario</th>
              <th style={{ width: 100 }}>Type</th>
              <th style={{ width: 90 }}>Priority</th>
              <th>Expected Result</th>
            </tr>
          </thead>
          <tbody>
            {testCases.map((tc) => (
              <tr key={tc.id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#58a6ff' }}>
                  {tc.id}
                </td>
                <td>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                    {tc.title}
                  </div>
                  {tc.steps && tc.steps.length > 0 && (
                    <ol style={{ fontSize: 12, color: 'var(--text-secondary)', paddingLeft: 16, marginTop: 4 }}>
                      {tc.steps.map((step, sIdx) => (
                        <li key={sIdx}>{step}</li>
                      ))}
                    </ol>
                  )}
                </td>
                <td>
                  <span style={{ fontSize: 11, padding: '2px 6px', background: 'rgba(255,255,255,0.06)', borderRadius: 4 }}>
                    {tc.type}
                  </span>
                </td>
                <td>
                  <span className={`priority-pill ${tc.priority?.toLowerCase() || 'medium'}`}>
                    {tc.priority}
                  </span>
                </td>
                <td style={{ fontSize: 12.5, color: '#e6edf3' }}>
                  {tc.expected_result}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
