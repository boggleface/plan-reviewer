import React from 'react';

export type Finding = {
  title: string;
  detail: string;
  quote: string | null;
};

type Props = {
  findings: Finding[];
  activeQuote: string | null;
  onSelectQuote: (quote: string) => void;
};

export const FindingsPanel: React.FC<Props> = ({
  findings,
  activeQuote,
  onSelectQuote,
}) => {
  return (
    <div className="card">
      <div className="card-header">
        <span className="section-label">Findings & Observations</span>
        <span className="meta-line">
          {findings.length} {findings.length === 1 ? 'finding' : 'findings'}
        </span>
      </div>

      {findings.length === 0 ? (
        <div className="empty-state">
          No findings · The review found no missing owners, risks or ambiguous dates.
        </div>
      ) : (
        <div className="findings-list">
          {findings.map((finding, idx) => {
            const isQuoteActive = finding.quote && activeQuote === finding.quote;
            return (
              <div key={idx} className="finding-item">
                <div className="finding-title">{finding.title}</div>
                <div className="finding-detail">{finding.detail}</div>
                {finding.quote && (
                  <div
                    className="finding-quote-box"
                    style={{
                      outline: isQuoteActive ? '2px solid var(--primary)' : 'none',
                    }}
                    onClick={() => onSelectQuote(finding.quote!)}
                    title="Click to view and highlight in plan text"
                  >
                    <span>"{finding.quote}"</span>
                    <span style={{ fontSize: '10px', textTransform: 'uppercase', fontStyle: 'normal' }}>
                      Locate in plan →
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
