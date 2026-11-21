import React from 'react';
import { ScheduleResult } from './StatusBanner';

export type Task = {
  id: string;
  name: string;
  owner: string | null;
  duration_days: number;
  depends_on: string[];
  quote: string;
  isEdited?: boolean;
};

type Props = {
  tasks: Task[];
  schedule: ScheduleResult | null;
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
};

// Soft, calm owner colors aligned with BRAND.md guidelines
const OWNER_PALETTE = [
  { bg: '#EAF2DC', border: '#B8D992', text: '#2A4D1B' }, // soft green/lime
  { bg: '#E3EDF4', border: '#A6C5DB', text: '#1E3E56' }, // soft sky
  { bg: '#F4EFE6', border: '#D5C4AA', text: '#543F24' }, // soft warm sand
  { bg: '#EDE8F5', border: '#C0B3D9', text: '#43345E' }, // soft lavender
  { bg: '#FDEEE9', border: '#E7B8A8', text: '#6E3222' }, // soft apricot
  { bg: '#E0F2E9', border: '#9FD4B9', text: '#195539' }, // soft sage
];

export const Timeline: React.FC<Props> = ({
  tasks,
  schedule,
  selectedTaskId,
  onSelectTask,
}) => {
  if (!schedule || schedule.status === 'cycle') {
    return (
      <div className="card timeline-card">
        <div className="card-header">
          <span className="section-label">Schedule Timeline</span>
        </div>
        <div className="empty-state">
          {schedule?.status === 'cycle'
            ? 'Timeline unavailable while a circular dependency exists.'
            : 'No schedule available.'}
        </div>
      </div>
    );
  }

  const scheduledMap = new Map(schedule.schedule.map((s) => [s.id, s]));
  const deadlineDay = schedule.deadline_day;
  const maxDay = Math.max(schedule.end_day || 0, deadlineDay, 10);

  // Distinct owners for color mapping
  const owners = Array.from(
    new Set(tasks.map((t) => t.owner || 'Unassigned'))
  ).sort();
  const ownerColorMap = new Map<string, (typeof OWNER_PALETTE)[0]>();
  owners.forEach((owner, idx) => {
    ownerColorMap.set(owner, OWNER_PALETTE[idx % OWNER_PALETTE.length]);
  });

  // Calculate day ticks for x-axis
  const step = maxDay > 30 ? 5 : maxDay > 15 ? 2 : 1;
  const ticks: number[] = [];
  for (let d = 0; d <= maxDay; d += step) {
    ticks.push(d);
  }
  if (!ticks.includes(maxDay)) {
    ticks.push(maxDay);
  }

  const deadlinePercent = (deadlineDay / maxDay) * 100;

  return (
    <div className="card timeline-card">
      <div className="card-header">
        <span className="section-label">Schedule Timeline</span>
        <span className="meta-line tabular">
          Day 0 to Day {maxDay} · {tasks.length} tasks
        </span>
      </div>

      <div style={{ padding: '16px 8px 8px 8px', overflowX: 'auto' }}>
        {/* X-axis ticks */}
        <div className="timeline-axis" style={{ height: '20px' }}>
          {ticks.map((tick) => {
            const pct = (tick / maxDay) * 100;
            return (
              <span
                key={tick}
                className="tabular"
                style={{
                  position: 'absolute',
                  left: `${pct}%`,
                  transform: 'translateX(-50%)',
                }}
              >
                {tick}
              </span>
            );
          })}
        </div>

        {/* Timeline canvas */}
        <div className="timeline-canvas">
          {/* Deadline marker line */}
          <div
            className="timeline-deadline-marker"
            style={{ left: `${deadlinePercent}%` }}
          >
            <span className="timeline-deadline-label tabular">
              Deadline ({deadlineDay})
            </span>
          </div>

          {/* Task rows */}
          {tasks.map((task) => {
            const scheduled = scheduledMap.get(task.id);
            if (!scheduled) return null;

            const startPct = (scheduled.start_day / maxDay) * 100;
            const widthPct = Math.max(
              2,
              ((scheduled.end_day - scheduled.start_day) / maxDay) * 100
            );

            const ownerName = task.owner || 'Unassigned';
            const colors =
              ownerColorMap.get(ownerName) || OWNER_PALETTE[0];
            const isSelected = selectedTaskId === task.id;

            return (
              <div key={task.id} className="timeline-row">
                <div
                  className="timeline-task-bar"
                  onClick={() => onSelectTask(task.id)}
                  title={`${task.id}: ${task.name} (${ownerName}) · Days ${scheduled.start_day} → ${scheduled.end_day}`}
                  style={{
                    left: `${startPct}%`,
                    width: `${widthPct}%`,
                    backgroundColor: colors.bg,
                    borderColor: isSelected ? 'var(--text)' : colors.border,
                    color: colors.text,
                    outline: isSelected ? '2px solid var(--primary)' : 'none',
                  }}
                >
                  <span style={{ fontWeight: 600, marginRight: 4 }}>
                    {task.id}
                  </span>
                  <span>{task.name}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
