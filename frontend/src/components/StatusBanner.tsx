import React from 'react';

export type ScheduleResult = {
  status: 'scheduled' | 'cycle';
  schedule: { id: string; start_day: number; end_day: number }[];
  end_day: number | null;
  deadline_day: number;
  meets_deadline: boolean | null;
  days_late: number | null;
  cycle: string[];
};

type Props = {
  schedule: ScheduleResult | null;
  initialSchedule: ScheduleResult | null;
  isEdited: boolean;
  onReset: () => void;
};

export const StatusBanner: React.FC<Props> = ({
  schedule,
  initialSchedule,
  isEdited,
  onReset,
}) => {
  if (!schedule) return null;

  const isCycle = schedule.status === 'cycle';
  const isLate = schedule.status === 'scheduled' && !schedule.meets_deadline;
  const isOnTrack = schedule.status === 'scheduled' && schedule.meets_deadline;

  const bannerClass = isCycle ? 'cycle' : isLate ? 'late' : 'success';

  return (
    <div className={`status-banner ${bannerClass}`}>
      <div className="status-row">
        <div className="status-main">
          <div className={`status-icon ${bannerClass}`}>
            {isOnTrack ? '✓' : isLate ? '✗' : '⚠'}
          </div>
          <div>
            <div className="status-headline">
              {isOnTrack && (
                <>
                  On track · finishes day {schedule.end_day} of {schedule.deadline_day}
                </>
              )}
              {isLate && (
                <>
                  {schedule.days_late} {schedule.days_late === 1 ? 'day' : 'days'} late · finishes day {schedule.end_day} of {schedule.deadline_day}
                </>
              )}
              {isCycle && <>Circular dependency · cannot schedule</>}
            </div>
            <div className="status-subline">
              {isOnTrack && (
                schedule.deadline_day - (schedule.end_day || 0) === 0
                  ? 'Finishes on the deadline day.'
                  : `${schedule.deadline_day - (schedule.end_day || 0)} days to spare.`
              )}
              {isLate && 'The plan cannot meet its deadline.'}
              {isCycle && (
                <>
                  Tasks {schedule.cycle.join(' and ')} depend on each other.
                </>
              )}
            </div>
          </div>
        </div>

        <div className="status-pills">
          <span className="pill pill-muted tabular">
            Deadline: Day {schedule.deadline_day}
          </span>
          {schedule.end_day !== null && (
            <span
              className={`pill tabular ${isOnTrack ? 'pill-success' : 'pill-late'}`}
            >
              Finish: Day {schedule.end_day}
            </span>
          )}
        </div>
      </div>

      {isEdited && initialSchedule && (
        <div className="diff-notice">
          <span>
            <strong>Modified view:</strong> Originally{' '}
            {initialSchedule.status === 'cycle'
              ? 'had a cycle'
              : `finished day ${initialSchedule.end_day} (${
                  initialSchedule.meets_deadline ? 'on track' : `${initialSchedule.days_late} days late`
                })`}
            {schedule.status === 'scheduled' && initialSchedule.end_day !== null && schedule.end_day !== null && (
              <> · {schedule.end_day - initialSchedule.end_day >= 0 ? `+${schedule.end_day - initialSchedule.end_day}` : schedule.end_day - initialSchedule.end_day} days change</>
            )}
          </span>
          <button className="btn-link" onClick={onReset}>
            Reset to original plan
          </button>
        </div>
      )}
    </div>
  );
};
