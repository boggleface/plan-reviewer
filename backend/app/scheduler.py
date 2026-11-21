def schedule(tasks: list[dict], deadline_day: int) -> dict:
    if not tasks:
        return {
            "status": "scheduled",
            "schedule": [],
            "end_day": 0,
            "deadline_day": deadline_day,
            "meets_deadline": 0 <= deadline_day,
            "days_late": 0,
            "cycle": [],
        }

    by_id = {t["id"]: t for t in tasks}

    def find_cycle() -> list[str]:
        state: dict[str, str] = {}
        stack: list[str] = []
        stack_positions: dict[str, int] = {}

        def visit(task_id: str) -> list[str] | None:
            state[task_id] = "visiting"
            stack_positions[task_id] = len(stack)
            stack.append(task_id)

            for dependency_id in by_id[task_id].get("depends_on", []):
                if dependency_id not in by_id:
                    continue
                dependency_state = state.get(dependency_id)
                if dependency_state == "visiting":
                    start = stack_positions[dependency_id]
                    return stack[start:]
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

    cycle = find_cycle()
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

    # Graph structure: dependencies and successors
    successors: dict[str, list[str]] = {tid: [] for tid in by_id}
    for tid, t in by_id.items():
        for dep in t.get("depends_on", []):
            if dep in successors:
                successors[dep].append(tid)

    # Critical path length from task to any sink (longest path of duration_days)
    cp_length: dict[str, int] = {}

    def get_cp(tid: str) -> int:
        if tid in cp_length:
            return cp_length[tid]
        dur = by_id[tid]["duration_days"]
        succ_max = max((get_cp(sid) for sid in successors[tid]), default=0)
        cp_length[tid] = dur + succ_max
        return cp_length[tid]

    for tid in by_id:
        get_cp(tid)

    def find_earliest_slot(intervals: list[tuple[int, int]], earliest_start: int, duration: int) -> int:
        t = earliest_start
        for start, end in intervals:
            if end <= t:
                continue
            if t + duration <= start:
                return t
            t = max(t, end)
        return t

    def simulate(order: list[str]) -> dict[str, dict]:
        scheduled: dict[str, dict] = {}
        owner_intervals: dict[str, list[tuple[int, int]]] = {}
        for tid in order:
            t = by_id[tid]
            earliest = max(
                (scheduled[d]["end_day"] for d in t.get("depends_on", []) if d in scheduled),
                default=0,
            )
            owner = t.get("owner")
            dur = t["duration_days"]
            if owner is not None:
                start = find_earliest_slot(owner_intervals.get(owner, []), earliest, dur)
                owner_intervals.setdefault(owner, []).append((start, start + dur))
                owner_intervals[owner].sort()
            else:
                start = earliest

            scheduled[tid] = {
                "id": tid,
                "start_day": start,
                "end_day": start + dur,
            }
        return scheduled

    # Evaluate multiple priority tie-breaking heuristics, all strictly respecting topological order
    task_keys = list(by_id.keys())
    candidate_orders = [
        sorted(task_keys, key=lambda tid: (-cp_length[tid], -by_id[tid]["duration_days"], tid)),
        sorted(task_keys, key=lambda tid: (-cp_length[tid], by_id[tid]["duration_days"], tid)),
        sorted(task_keys, key=lambda tid: (-cp_length[tid], -len(successors[tid]), tid)),
        sorted(task_keys, key=lambda tid: (-cp_length[tid], tid)),
    ]

    best_scheduled: dict[str, dict] | None = None
    best_end_day = float("inf")
    best_sum_end = float("inf")

    for order in candidate_orders:
        sched = simulate(order)
        end_day = max((s["end_day"] for s in sched.values()), default=0)
        sum_end = sum(s["end_day"] for s in sched.values())
        if end_day < best_end_day or (end_day == best_end_day and sum_end < best_sum_end):
            best_end_day = end_day
            best_sum_end = sum_end
            best_scheduled = sched

    assert best_scheduled is not None
    schedule_list = [best_scheduled[t["id"]] for t in tasks]
    end_day = int(best_end_day)

    return {
        "status": "scheduled",
        "schedule": schedule_list,
        "end_day": end_day,
        "deadline_day": deadline_day,
        "meets_deadline": end_day <= deadline_day,
        "days_late": max(0, end_day - deadline_day),
        "cycle": [],
    }
