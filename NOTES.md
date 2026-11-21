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

- **Plan upload and automatic AI review**: Nora has no workflow to receive or upload a new plan, and no incoming plan automatically triggers the AI review. Plans currently enter the system by being added to `data/plans/` by a developer or through the review command, and a corresponding stored review must also be generated before the app can display it. The prototype concentrated the available time on parsing, scheduling, verification, and the review interface rather than intake infrastructure. Adding reliable intake would require a new upload and persistence layer, authenticated ingestion or mailbox/webhook integration, async job handling, and a way to manage model/API failures in the deployed environment.
- **Persistent backend edits**: Nora's what-if edits are maintained in client state rather than mutating the stored JSON files on disk. The stored reviews remain the AI's direct output, while Nora can freely explore what-if scenarios and reset at any time.
- **Heavy chart libraries**: Built the visual timeline using native flexbox and CSS percentages, keeping the frontend bundle small and fast with zero third-party chart dependencies.

## What is not ready

- **Multi-user concurrency**: Edits are per-session in the browser. If multiple officers review the same plan simultaneously, there is no shared state or edit history.
- **Complex calendar rules**: The scheduler models 7-day continuous project days (per contract spec); bank holidays and non-working weekends are not factored into duration calculations unless volunteers represent them as task days.

## What I would do next and a rough estimate

- **Plan upload and management** (~2-3 hours): Let Nora upload plans and manage the stored plan and review lifecycle.
- **Better persistence** (~2-3 hours): Replace file-based plan and review storage with a database to support reliable saving, querying, and concurrent use.
- **Observability and user feedback** (~2-3 hours): Add Grafana dashboards or similar monitoring for application health and model-performance metrics, along with in-app controls for collecting Nora's user-satisfaction feedback.

## How I used AI tools

I first used Copilot to explore the codebase, fix cyclic-dependency handling, and switch to a free model for generating reviews. For the rewrite, I created a plan with Claude Opus 4.6 using Google Antigravity on the free tier. I then implemented the changes using Gemini 3.5 Flash according to my available budget. From there, I verified the implementation again with Copilot and upgraded the scheduling algorithm to CP-SAT, an exact constraint programming solver, for more accurate schedules. Verification included my own manual testing, manual code review, AI code review, and exploratory testing.

## Environment variables my review command needs

- `OPENROUTER_API_KEY` - required to call OpenRouter.
- `REVIEW_MODEL` - optional; defaults to `nvidia/nemotron-3.5-super-vl:free`.
- `OPENROUTER_BASE_URL` - optional; defaults to `https://openrouter.ai/api/v1`.
