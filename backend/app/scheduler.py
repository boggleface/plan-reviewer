from ortools.sat.python import cp_model

SOLVER_TIME_LIMIT_SECONDS = 8.0
MAX_CP_SAT_INTEGER = (1 << 63) - 1


class ScheduleOptimizationError(RuntimeError):
    """Raised when the solver cannot produce a feasible schedule."""


def _find_cycle(by_id: dict[str, dict]) -> list[str]:
    state: dict[str, str] = {}
    stack: list[str] = []
    stack_positions: dict[str, int] = {}

    def visit(task_id: str) -> list[str] | None:
        state[task_id] = "visiting"
        stack_positions[task_id] = len(stack)
        stack.append(task_id)

        for dependency_id in by_id[task_id].get("depends_on", []):
            dependency_state = state.get(dependency_id)
            if dependency_state == "visiting":
                return stack[stack_positions[dependency_id]:]
            if dependency_state is None:
                cycle = visit(dependency_id)
                if cycle:
                    return cycle

        stack.pop()
        stack_positions.pop(task_id, None)
        state[task_id] = "done"
        return None

    for task_id in by_id:
        if state.get(task_id) is None:
            cycle = visit(task_id)
            if cycle:
                return cycle
    return []


def _serial_schedule(tasks: list[dict]) -> tuple[list[dict], int]:
    by_id = {task["id"]: task for task in tasks}
    successors = {task_id: [] for task_id in by_id}
    remaining_dependencies = {}
    for task in tasks:
        dependencies = task.get("depends_on", [])
        remaining_dependencies[task["id"]] = len(dependencies)
        for dependency_id in dependencies:
            successors[dependency_id].append(task["id"])

    ready = [
        task["id"]
        for task in tasks
        if remaining_dependencies[task["id"]] == 0
    ]
    scheduled = {}
    end_day = 0
    while ready:
        task_id = ready.pop(0)
        duration = by_id[task_id]["duration_days"]
        scheduled[task_id] = {
            "id": task_id,
            "start_day": end_day,
            "end_day": end_day + duration,
        }
        end_day += duration
        for successor_id in successors[task_id]:
            remaining_dependencies[successor_id] -= 1
            if remaining_dependencies[successor_id] == 0:
                ready.append(successor_id)

    return [scheduled[task["id"]] for task in tasks], end_day


def schedule(tasks: list[dict], deadline_day: int) -> dict:
    if not tasks:
        return {
            "status": "scheduled",
            "schedule": [],
            "end_day": 0,
            "deadline_day": deadline_day,
            "meets_deadline": 0 <= deadline_day,
            "days_late": max(0, -deadline_day),
            "cycle": [],
            "optimal": True,
        }

    by_id = {task["id"]: task for task in tasks}
    cycle = _find_cycle(by_id)
    if cycle:
        return {
            "status": "cycle",
            "schedule": [],
            "end_day": None,
            "deadline_day": deadline_day,
            "meets_deadline": None,
            "days_late": None,
            "cycle": cycle,
        }

    horizon = sum(task["duration_days"] for task in tasks)
    if horizon > MAX_CP_SAT_INTEGER:
        schedule_list, end_day = _serial_schedule(tasks)
        return _scheduled_result(schedule_list, end_day, deadline_day, optimal=False)

    model = cp_model.CpModel()
    start_vars = {}
    end_vars = {}
    owner_intervals: dict[str, list] = {}

    for task in tasks:
        task_id = task["id"]
        duration = task["duration_days"]
        start = model.NewIntVar(0, horizon - duration, f"start_{task_id}")
        end = model.NewIntVar(duration, horizon, f"end_{task_id}")
        interval = model.NewIntervalVar(start, duration, end, f"interval_{task_id}")
        start_vars[task_id] = start
        end_vars[task_id] = end

        owner = task.get("owner")
        if owner is not None:
            owner_intervals.setdefault(owner, []).append(interval)

    for task in tasks:
        task_id = task["id"]
        for dependency_id in task.get("depends_on", []):
            model.Add(start_vars[task_id] >= end_vars[dependency_id])

    for intervals in owner_intervals.values():
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, list(end_vars.values()))
    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIME_LIMIT_SECONDS
    status = solver.Solve(model)
    if status == cp_model.UNKNOWN:
        schedule_list, end_day = _serial_schedule(tasks)
        return _scheduled_result(schedule_list, end_day, deadline_day, optimal=False)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        status_name = solver.StatusName(status)
        raise ScheduleOptimizationError(
            "Could not produce a feasible schedule "
            f"(solver status: {status_name})."
        )

    schedule_list = [
        {
            "id": task["id"],
            "start_day": solver.Value(start_vars[task["id"]]),
            "end_day": solver.Value(end_vars[task["id"]]),
        }
        for task in tasks
    ]
    end_day = solver.Value(makespan)
    return _scheduled_result(
        schedule_list,
        end_day,
        deadline_day,
        optimal=status == cp_model.OPTIMAL,
    )


def _scheduled_result(
    schedule_list: list[dict],
    end_day: int,
    deadline_day: int,
    optimal: bool,
) -> dict:
    return {
        "status": "scheduled",
        "schedule": schedule_list,
        "end_day": end_day,
        "deadline_day": deadline_day,
        "meets_deadline": end_day <= deadline_day,
        "days_late": max(0, end_day - deadline_day),
        "cycle": [],
        "optimal": optimal,
    }
