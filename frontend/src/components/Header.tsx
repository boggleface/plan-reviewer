import React from 'react';

type Props = {
  plans: { id: string; title: string }[];
  selectedId: string;
  onSelectPlan: (id: string) => void;
  planTitle?: string;
};

export const Header: React.FC<Props> = ({
  plans,
  selectedId,
  onSelectPlan,
  planTitle,
}) => {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-mark">✓</div>
        <h1 className="brand-title">Plan reviewer</h1>
      </div>

      <div className="header-controls">
        <div className="plan-select-wrap">
          <label htmlFor="plan-select" className="select-label">
            Plan
          </label>
          <select
            id="plan-select"
            className="plan-select"
            value={selectedId}
            onChange={(e) => onSelectPlan(e.target.value)}
          >
            {plans.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
        </div>
        {planTitle && (
          <span className="header-meta">
            {planTitle}
          </span>
        )}
      </div>
    </header>
  );
};
