# Notes

## Time spent

About 2 hours total:
- ~30 min: Exact CP-SAT scheduler with unary resource constraints and unit tests.
- ~20 min: API validation (Pydantic schemas, 400/404 handling) and test coverage.
- ~45 min: Frontend redesign following WhiteSpace brand (StatusBanner, Timeline, TaskTable with inline edits, PlanText with quote highlighting).
- ~15 min: Review retry logic and contract verification.

## What I did

1. **Owner-aware resource scheduling**: The scheduler uses OR-Tools CP-SAT to minimize project makespan while enforcing dependency precedence and preventing tasks with the same non-null owner from overlapping. It reports circular dependencies, including self-loops. Within its 8-second limit, it returns the best feasible schedule found and marks whether optimality was proven; if the solver finds no feasible schedule, a serial dependency-respecting fallback ensures valid input still receives a schedule.
2. **Backend validation and error handling**:
   - Added Pydantic schemas validating task constraints (<= 60 tasks, unique IDs, duration >= 1, valid dependencies).
   - Provided clean HTTP 400 JSON responses on validation errors and HTTP 404 for missing plans.
   - Added retry logic with exponential backoff for transient OpenRouter/LLM failures in `review.py`.
3. **Frontend aligned with Nora's priorities and WhiteSpace brand**:
   - **At a glance (Priority 1)**: Prominent `StatusBanner` at the top showing whether the plan meets its date, the exact days late or to spare, and cycle alerts in plain, calm language.
   - **Traceability (Priority 2)**: Verbatim quotes are accessible on each task and finding; clicking a quote highlights the matching text in the source plan document and scrolls to it.
   - **Editability (Priority 3)**: Inline editable task table allows Nora to adjust durations, owners, or dependencies. Edits re-schedule live via `POST /api/schedule` and display a diff compared to the original review.
   - **Visual Timeline**: Gantt-style schedule bar chart with owner color palettes and a deadline marker.
   - **Brand design**: Built with Inter and Source Serif 4, warm canvas (`#F8F7F2`), white cards, hairline borders, tabular figures, `#6C962C` primary marks, `#CDEB9B` chips, and `#CB593B` terracotta reserved exclusively for warnings/lateness.

## What I cut and why

- **Persistent backend edits**: Nora's what-if edits are maintained in client state rather than mutating the stored JSON files on disk. The stored reviews remain the AI's direct output, while Nora can freely explore what-if scenarios and reset at any time.
- **Heavy chart libraries**: Built the visual timeline using native flexbox and CSS percentages, keeping the frontend bundle small and fast with zero third-party chart dependencies.

## What is not ready

- **Multi-user concurrency**: Edits are per-session in the browser. If multiple officers review the same plan simultaneously, there is no shared state or edit history.
- **Complex calendar rules**: The scheduler models 7-day continuous project days (per contract spec); bank holidays and non-working weekends are not factored into duration calculations unless volunteers represent them as task days.

## What I would do next and a rough estimate

- **Export and print summary** (~1 hour): A 1-page PDF/print view that Nora can attach when emailing the committee back with the verbatim quotes and schedule verdict.
- **What-if undo/redo stack** (~30 min): History state for exploring multiple edit scenarios.
- **Optimization diagnostics** (~1 hour): Surface solver duration and optimality diagnostics in an optional debug view for unusually difficult schedules.

## How I used AI tools

Used an AI assistant to scaffold boilerplate components, explore heuristic tie-breakers for RCPSP, and verify contract check edge cases. All generated code was inspected, tested against `check_contract.py`, and verified with automated test suites.

## Environment variables my review command needs

- `OPENROUTER_API_KEY` - required to call OpenRouter.
- `REVIEW_MODEL` - optional; defaults to `nvidia/nemotron-3.5-super-vl:free`.
- `OPENROUTER_BASE_URL` - optional; defaults to `https://openrouter.ai/api/v1`.
