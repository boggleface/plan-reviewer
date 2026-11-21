import { useEffect, useState, useCallback } from 'react';
import './styles.css';
import { Header } from './components/Header';
import { StatusBanner, ScheduleResult } from './components/StatusBanner';
import { Timeline, Task } from './components/Timeline';
import { TaskTable } from './components/TaskTable';
import { FindingsPanel, Finding } from './components/FindingsPanel';
import { PlanText } from './components/PlanText';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '');

type PlanSummary = {
  id: string;
  title: string;
};

type ApiResponse = {
  id: string;
  text: string;
  review: {
    deadline_day: number | null;
    tasks: {
      id: string;
      name: string;
      owner: string | null;
      duration_days: number;
      depends_on: string[];
      quote: string;
    }[];
    findings: Finding[];
  };
  schedule: ScheduleResult;
};

export default function App() {
  const [plans, setPlans] = useState<PlanSummary[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(true);

  // Plan data state
  const [planTitle, setPlanTitle] = useState('');
  const [planText, setPlanText] = useState('');
  const [deadlineDay, setDeadlineDay] = useState<number | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [initialTasks, setInitialTasks] = useState<Task[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [schedule, setSchedule] = useState<ScheduleResult | null>(null);
  const [initialSchedule, setInitialSchedule] = useState<ScheduleResult | null>(null);
  const [isEdited, setIsEdited] = useState(false);

  // Interaction state
  const [activeQuote, setActiveQuote] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  // Fetch plan list on load
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/plans`)
      .then((res) => res.json())
      .then((items: PlanSummary[]) => {
        setPlans(items);
        if (items.length > 0) {
          setSelectedId(items[0].id);
        }
      })
      .catch((err) => console.error('Failed to load plans:', err));
  }, []);

  // Fetch selected plan
  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    setActiveQuote(null);
    setSelectedTaskId(null);

    fetch(`${API_BASE_URL}/api/plans/${selectedId}`)
      .then((res) => res.json())
      .then((data: ApiResponse) => {
        const found = plans.find((p) => p.id === selectedId);
        setPlanTitle(found ? found.title : selectedId);
        setPlanText(data.text);
        setDeadlineDay(data.review.deadline_day);

        const loadedTasks: Task[] = data.review.tasks.map((t) => ({
          ...t,
          isEdited: false,
        }));
        setTasks(loadedTasks);
        setInitialTasks(loadedTasks);

        setFindings(data.review.findings);
        setSchedule(data.schedule);
        setInitialSchedule(data.schedule);
        setIsEdited(false);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load plan details:', err);
        setLoading(false);
      });
  }, [selectedId, plans]);

  // Re-schedule API call when tasks are edited
  const recomputeSchedule = useCallback(
    async (updatedTasks: Task[]) => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/schedule`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tasks: updatedTasks.map((t) => ({
              id: t.id,
              name: t.name,
              owner: t.owner,
              duration_days: t.duration_days,
              depends_on: t.depends_on,
            })),
            deadline_day: deadlineDay ?? 0,
          }),
        });
        if (response.ok) {
          const result: ScheduleResult = await response.json();
          setSchedule(result);
        }
      } catch (err) {
        console.error('Error re-scheduling:', err);
      }
    },
    [deadlineDay]
  );

  // Update a single task field
  const handleUpdateTask = (index: number, updated: Partial<Task>) => {
    const nextTasks = tasks.map((t, idx) => {
      if (idx === index) {
        return { ...t, ...updated, isEdited: true };
      }
      return t;
    });
    setTasks(nextTasks);
    setIsEdited(true);
    recomputeSchedule(nextTasks);
  };

  // Reset to original plan
  const handleReset = () => {
    setTasks(initialTasks);
    setSchedule(initialSchedule);
    setIsEdited(false);
  };

  return (
    <div className="app-container">
      <Header
        plans={plans}
        selectedId={selectedId}
        onSelectPlan={setSelectedId}
        planTitle={planTitle}
      />

      <main className="main-content">
        {loading ? (
          <div className="empty-state">Loading event plan...</div>
        ) : (
          <>
            <StatusBanner
              schedule={schedule}
              initialSchedule={initialSchedule}
              isEdited={isEdited}
              onReset={handleReset}
            />

            <Timeline
              tasks={tasks}
              schedule={schedule}
              selectedTaskId={selectedTaskId}
              onSelectTask={(id) => {
                setSelectedTaskId(id);
                const task = tasks.find((t) => t.id === id);
                if (task) setActiveQuote(task.quote);
              }}
            />

            <div className="workspace-grid">
              <div className="left-stack">
                <TaskTable
                  tasks={tasks}
                  schedule={schedule}
                  activeQuote={activeQuote}
                  selectedTaskId={selectedTaskId}
                  onSelectTask={setSelectedTaskId}
                  onSelectQuote={setActiveQuote}
                  onUpdateTask={handleUpdateTask}
                />

                <FindingsPanel
                  findings={findings}
                  activeQuote={activeQuote}
                  onSelectQuote={setActiveQuote}
                />
              </div>

              <div className="right-col">
                <PlanText
                  text={planText}
                  activeQuote={activeQuote}
                  onClearQuote={() => setActiveQuote(null)}
                />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
