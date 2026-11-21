def schedule(tasks, deadline_day):
    by_id = {t["id"]: t for t in tasks}

    def find_cycle():
        state = {}
        stack = []
        stack_positions = {}

        def visit(task_id):
            state[task_id] = "visiting"
            stack_positions[task_id] = len(stack)
            stack.append(task_id)

            for dependency_id in by_id[task_id]["depends_on"]:
                if dependency_id not in by_id:
                    continue
                dependency_state = state.get(dependency_id)
                if dependency_state == "visiting":
                    start = stack_positions[dependency_id]
                    return stack[start:] + [dependency_id]
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
            "cycle": cycle[:-1],
        }

    def end_of(task):
        start = max([end_of(by_id[d]) for d in task["depends_on"]], default=0)
        return start + task["duration_days"]

    items = []
    for t in tasks:
        end = end_of(t)
        items.append({"id": t["id"], "start_day": end - t["duration_days"], "end_day": end})

    end_day = max([i["end_day"] for i in items], default=0)
    return {
        "status": "scheduled",
        "schedule": items,
        "end_day": end_day,
        "deadline_day": deadline_day,
        "meets_deadline": end_day <= deadline_day,
        "days_late": max(0, end_day - deadline_day),
        "cycle": [],
    }
