import React, { useState } from 'react';
import { Task } from './Timeline';
import { ScheduleResult } from './StatusBanner';

type Props = {
  tasks: Task[];
  schedule: ScheduleResult | null;
  activeQuote: string | null;
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
  onSelectQuote: (quote: string) => void;
  onUpdateTask: (index: number, updated: Partial<Task>) => void;
};

export const TaskTable: React.FC<Props> = ({
  tasks,
  schedule,
  activeQuote,
  selectedTaskId,
  onSelectTask,
  onSelectQuote,
  onUpdateTask,
}) => {
  const [expandedQuotes, setExpandedQuotes] = useState<Record<string, boolean>>({});

  const toggleQuote = (taskId: string, quote: string) => {
    const isExpanding = !expandedQuotes[taskId];
    setExpandedQuotes((prev) => ({ ...prev, [taskId]: isExpanding }));
    if (isExpanding) {
      onSelectQuote(quote);
    }
  };

  const scheduledMap = new Map(
    schedule?.schedule.map((s) => [s.id, s]) || []
  );

  return (
    <div className="card">
      <div className="card-header">
        <span className="section-label">Tasks & Resource Schedule</span>
        <span className="meta-line">
          {tasks.length} tasks · Click fields to edit & re-schedule
        </span>
      </div>

      <div className="task-table-wrap">
        <table className="task-table">
          <thead>
            <tr>
              <th style={{ width: '45px' }}>ID</th>
              <th>Task Name</th>
              <th style={{ width: '100px' }}>Owner</th>
              <th style={{ width: '60px' }}>Days</th>
              <th style={{ width: '90px' }}>Depends on</th>
              <th style={{ width: '55px' }}>Start</th>
              <th style={{ width: '55px' }}>End</th>
              <th style={{ width: '70px', textAlign: 'center' }}>Quote</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task, index) => {
              const sched = scheduledMap.get(task.id);
              const isSelected = selectedTaskId === task.id;
              const isQuoteExpanded = !!expandedQuotes[task.id];
              const isQuoteActive = activeQuote === task.quote;

              return (
                <React.Fragment key={task.id}>
                  <tr
                    className={`task-row ${isSelected ? 'highlighted' : ''}`}
                    onClick={() => onSelectTask(task.id)}
                  >
                    <td>
                      <span className="task-id-badge">{task.id}</span>
                      {task.isEdited && <span className="edited-tag">Edited</span>}
                    </td>
                    <td>
                      <span style={{ fontWeight: 500 }}>{task.name}</span>
                    </td>
                    <td>
                      <input
                        type="text"
                        className="input-cell input-owner"
                        placeholder="null"
                        value={task.owner ?? ''}
                        onChange={(e) => {
                          const val = e.target.value.trim();
                          onUpdateTask(index, { owner: val === '' ? null : val });
                        }}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="1"
                        className="input-cell input-duration tabular"
                        value={task.duration_days}
                        onChange={(e) => {
                          const val = parseInt(e.target.value, 10);
                          if (!isNaN(val) && val >= 1) {
                            onUpdateTask(index, { duration_days: val });
                          }
                        }}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        className="input-cell input-deps"
                        placeholder="none"
                        value={task.depends_on.join(', ')}
                        onChange={(e) => {
                          const list = e.target.value
                            .split(',')
                            .map((s) => s.trim())
                            .filter(Boolean);
                          onUpdateTask(index, { depends_on: list });
                        }}
                      />
                    </td>
                    <td className="tabular" style={{ color: 'var(--text-muted)' }}>
                      {sched ? sched.start_day : '—'}
                    </td>
                    <td className="tabular" style={{ fontWeight: 600 }}>
                      {sched ? sched.end_day : '—'}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        type="button"
                        className={`btn-quote ${isQuoteActive ? 'active' : ''}`}
                        title="View verbatim quote from plan"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleQuote(task.id, task.quote);
                        }}
                      >
                        ❝ {isQuoteExpanded ? 'Hide' : 'Quote'}
                      </button>
                    </td>
                  </tr>

                  {isQuoteExpanded && (
                    <tr className="inline-quote-row">
                      <td colSpan={8}>
                        <div className="inline-quote-label">
                          Verbatim source quote (Task {task.id}):
                        </div>
                        <div className="inline-quote-text">
                          "{task.quote}"
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
