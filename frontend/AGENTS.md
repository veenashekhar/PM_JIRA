# Frontend overview (existing demo)

## Purpose

This frontend is a Next.js App Router demo that renders a single Kanban board with drag-and-drop, column renaming, and card add/remove. It is currently frontend-only and keeps state in React.

## Architecture

- Next.js App Router: entry in src/app/page.tsx renders KanbanBoard.
- Global layout: src/app/layout.tsx sets fonts (Space Grotesk, Manrope) and metadata.
- Styling: Tailwind CSS v4 via @import "tailwindcss" in src/app/globals.css, with CSS variables for the color system.
- State: KanbanBoard owns all board state (React useState) and updates columns/cards locally.
- Drag and drop: @dnd-kit/core + @dnd-kit/sortable with DragOverlay and PointerSensor.

## Key modules

- src/components/KanbanBoard.tsx: main UI, board state, DnD handlers, column rename/add/delete.
- src/components/KanbanColumn.tsx: column UI, droppable area, column title edit, list of cards.
- src/components/KanbanCard.tsx: draggable card view with remove button.
- src/components/KanbanCardPreview.tsx: drag overlay preview.
- src/components/NewCardForm.tsx: inline add-card form.
- src/lib/kanban.ts: data types, initial board data, moveCard helper, createId.

## Tests

- Unit tests: Vitest + Testing Library in src/**/*.test.tsx and src/**/*.test.ts.
  - KanbanBoard.test.tsx covers render, rename, add/remove.
  - kanban.test.ts covers moveCard behavior.
- E2E tests: Playwright in tests/kanban.spec.ts (board loads, add card, drag card).

## Scripts (package.json)

- dev: next dev
- build: next build
- start: next start
- test:unit: vitest run
- test:e2e: playwright test
- test:all: unit + e2e
