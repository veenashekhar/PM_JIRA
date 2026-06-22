# Project plan and execution checklist

This document is the execution plan. Each part includes a checklist, tests, and success criteria.

## Part 1: Plan

**Checklist**
- [x] Expand this plan with detailed steps, tests, and success criteria for each part.
- [x] Create frontend/AGENTS.md describing existing frontend architecture and key files.
- [x] Confirm plan with the user before proceeding to Part 2.

**Tests**
- No code changes required.

**Success criteria**
- This document is complete and approved by the user.
- frontend/AGENTS.md exists and accurately describes the current frontend.

## Test coverage target (applies to Parts 3, 4, 6, 7, 9, 10)

**Policy**
- Aim for at least 80% line coverage on backend and frontend unit tests.
- Focus on meaningful behavior (core flows, edge cases, and regressions). Avoid shallow or redundant tests.
- Use coverage reports to identify gaps; do not add tests for trivial lines.

**Tooling**
- Frontend: Vitest coverage (v8) for unit tests.
- Backend: pytest coverage via pytest-cov.

**Success criteria**
- Coverage reports show at least 80% line coverage where applicable.
- Tests reflect real user or system behavior, not implementation trivia.

## Part 2: Scaffolding

**Decisions**
- Single Docker container running FastAPI and serving static assets.
- Example static HTML served from a route like /hello (not /).

**Checklist**
- [x] Add Dockerfile and docker setup for a single container.
- [x] Initialize backend/ FastAPI app with uv.
- [x] Serve a simple HTML page at /hello (static or templated).
- [x] Add a basic API route (e.g., /api/health or /api/hello).
- [x] Add start/stop scripts for macOS, Windows, Linux in scripts/.
- [x] Ensure local run works with docker build and docker run.

**Tests**
- Manual: hit /hello and /api/health locally.
- Backend: pytest + httpx basic test for the API route.

**Success criteria**
- Single container serves /hello and /api/health.
- Start/stop scripts work on all supported OS targets.

## Part 3: Add in Frontend

**Checklist**
- [x] Configure backend to serve the built Next.js static site at /.
- [x] Add build pipeline to produce static assets from frontend/.
- [x] Confirm the demo Kanban board appears at /.
- [x] Update Docker build to include the static build output.

**Tests**
- Frontend: Playwright checks that / renders the Kanban board.
- Backend: pytest + httpx verifies / returns HTML.
- Frontend unit coverage: reach 80% line coverage with meaningful tests.

**Success criteria**
- Static frontend is served at / from the single container.
- Playwright tests pass against the built container.

## Part 4: Add a fake user sign in experience

**Checklist**
- [x] Add a login screen gated at /.
- [x] Accept only dummy credentials ("user", "password").
- [x] Add logout flow to return to login screen.
- [x] Ensure session state is handled in the frontend only for MVP.

**Tests**
- Frontend: Playwright login, logout, and invalid login flows.
- Frontend unit coverage: reach 80% line coverage with meaningful tests.
- Backend: no changes required unless routing changes are introduced.

**Success criteria**
- User must log in to see the Kanban board.
- Logout returns to login page.
- Board changes persist after logout and subsequent login.

## Part 5: Database modeling

**Checklist**
- [x] Define the SQLite data model for users, boards, columns, cards.
- [x] Save the database data structure as JSON in docs/ (example data structure).
- [x] Document database approach in docs/ and get user sign off.

**Tests**
- No runtime tests required.

**Success criteria**
- JSON data structure is saved and reviewed.
- User approves the data model.

## Part 6: Backend

**Checklist**
- [x] Add database initialization and auto-create if missing.
- [x] Implement API routes to read and update the Kanban for a user.
- [x] Add validation for board, columns, cards payloads.

**Tests**
- Backend: pytest + httpx unit tests for read and update routes.
- Backend unit coverage: reach 80% line coverage with meaningful tests.

**Success criteria**
- Backend APIs return and persist Kanban state for a user.
- Tests cover CRUD flows and error cases.

## Part 7: Frontend + Backend

**Checklist**
- [x] Replace frontend demo state with real API calls.
- [x] Ensure drag/drop and edits persist to backend.
- [x] Handle loading and error states.

**Tests**
- Frontend: Playwright flows for create/edit/move cards.
- Backend: pytest + httpx integration tests for persistence.
- Backend unit coverage: reach 80% line coverage with meaningful tests.

**Success criteria**
- Kanban state persists across refreshes.
- UI reflects backend state changes.

## Part 8: AI connectivity

**Checklist**
- [x] Add OpenRouter client and configuration.
- [x] Add backend endpoint to run a simple AI call.
- [x] Use model openai/gpt-oss-120b.

**Tests**
- Backend: pytest + httpx with a mocked OpenRouter call.
- Backend unit coverage: reach 80% line coverage with meaningful tests.
- Manual: optional live call returns 4 for "2+2".

**Success criteria**
- AI call path is wired and testable.
- Configuration uses OPENROUTER_API_KEY.

## Part 9: Structured outputs for Kanban updates

**Checklist**
- [x] Create OpenAI-style JSON schema for structured output.
- [x] Send current Kanban JSON + user query + history to AI.
- [x] Parse structured response with optional Kanban updates.
- [x] Validate and apply updates on the backend.
- [x] Add mock AI mode with structured, task-based responses when credits are unavailable.

**Tests**
- Backend: pytest + httpx validates schema parsing and update application.
- Unit tests for schema validation and error handling.
- Backend unit coverage: reach 80% line coverage with meaningful tests.

**Success criteria**
- Backend returns AI response and applies updates safely.
- Invalid outputs are handled gracefully.
- Mock mode supports add, move, rename, and summary commands with predictable updates.

## Part 10: AI chat sidebar in UI

**Checklist**
- [x] Build sidebar UI for chat, history, and send input.
- [x] Connect to backend AI endpoint.
- [x] Apply Kanban updates from AI response and refresh UI.
- [x] Ensure UI responsiveness on mobile.
- [x] Add chat toggle control and mock mode toggle in the sidebar.

**Tests**
- Frontend: Playwright tests for chat send/receive and Kanban update.
- Frontend unit coverage: reach 80% line coverage with meaningful tests.

**Success criteria**
- Chat works end-to-end.
- Kanban updates appear immediately after AI response.
- Mock mode can add cards to named columns with parsed title/description synonyms.
- Mock mode can move a card by title to a named column and rename a specified column.
- Mock mode summary returns all columns with card titles.