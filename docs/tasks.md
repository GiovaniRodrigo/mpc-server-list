# Atomic Task List for UI Gap Implementation

This file breaks the UI action plan into small, executable tasks that can be implemented incrementally.

## Phase 1 — Server visibility and operational overview

### Task 1.1 — Create server status dashboard (completed)
- Goal: Add a page that shows all registered MCP servers in one place.
- Scope:
  - list all server keys from the configuration
  - show name, command, description, and status
  - include online/offline/misconfigured state badges
- Acceptance criteria:
  - dashboard loads without manual code inspection
  - server list is clear and searchable
  - unknown or broken server states are visibly labeled
- Delivered by `app.py` and `frontend/index.html` through `GET /api/servers`.
  The current status is configuration-based; live connectivity checks remain
  future work.

### Task 1.2 — Add health summary widgets (partial)
- Goal: Provide high-level operational metrics.
- Scope:
  - total servers
  - online servers
  - failed servers
  - last execution timestamp
- Acceptance criteria:
  - summary cards are visible above the list
  - values refresh correctly
  - status colors clearly communicate health
- The catalog total and configured-state summary are available. Live health,
  failure counts, and last execution metrics are not implemented yet.

### Task 1.3 — Execution history panel (completed for HTTP activity)
- Goal: Add a log of recent tool executions.
- Scope:
  - timestamp
  - server key
  - tool name
  - status
  - response summary
- Acceptance criteria:
  - user can see the last executions in a timeline or table
  - failed calls show error context
  - panel is readable without technical knowledge
- Delivered by `ActivityLog` in `app.py` and `frontend/monitor.html`. The
  bounded in-memory monitor covers gateway requests and does not persist direct
  router calls.

## Phase 2 — Tool discovery and execution UX

### Task 2.1 — Create tool catalog page (completed)
- Goal: Expose available tools in a browsable UI.
- Scope:
  - list discovered tools by server
  - show description and parameter metadata
  - allow keyword-based filtering
- Acceptance criteria:
  - users can browse tools without editing config files
  - tool metadata is displayed clearly and consistently
- Delivered by the server catalog page and `GET /api/servers/{server_key}/tools`.

### Task 2.2 — Create tool detail view (completed)
- Goal: Show detailed metadata for a selected tool.
- Scope:
  - schema preview
  - required fields
  - example usage
  - server ownership
- Acceptance criteria:
  - a user can understand what the tool does before running it
  - the detail view is scannable and not overloaded
- Delivered in `frontend/index.html` with schema, description, ownership, and
  execution controls.

### Task 2.3 — Implement execution form (completed)
- Goal: Add a form to test a tool from the UI.
- Scope:
  - request JSON editor or form builder
  - validation for required arguments
  - response preview panel
- Acceptance criteria:
  - execution can be triggered without terminal access
  - invalid payloads are blocked before submission
  - responses are rendered clearly
- Delivered by the dashboard form and `POST /api/servers/{server_key}/execute`.

## Phase 3 — Configuration and governance

### Task 3.1 — Build server configuration editor
- Goal: Replace direct JSON editing with a guided UI.
- Scope:
  - add server
  - edit command, args, env fields
  - enable/disable server
  - delete server
- Acceptance criteria:
  - server definitions can be managed visually
  - validation prevents broken entries
  - user changes can be saved safely

### Task 3.2 — Add validation and rollback
- Goal: Prevent invalid configuration from breaking the system.
- Scope:
  - validate required fields before save
  - show warnings for malformed values
  - rollback on failed save
- Acceptance criteria:
  - invalid configuration is flagged immediately
  - users can revert changes safely

### Task 3.3 — Add roles and permissions model
- Goal: Prepare controlled access to sensitive tools.
- Scope:
  - define roles such as viewer, operator, admin
  - restrict execution or mutation based on role
- Acceptance criteria:
  - access rules are enforced consistently
  - unauthorized actions are blocked with a readable message

## Phase 4 — Adoption and polish

### Task 4.1 — Create onboarding flow
- Goal: Help new users understand the product quickly.
- Scope:
  - landing page
  - introduction to server registry concept
  - first-run example for connecting and executing a tool
- Acceptance criteria:
  - first-time users can complete a guided introduction
  - product value is understandable within a few minutes

### Task 4.2 — Establish design system
- Goal: Create a consistent interface language.
- Scope:
  - color palette for status and actions
  - typography scale
  - reusable card, button, and badge patterns
- Acceptance criteria:
  - repeated UI patterns look coherent
  - main operational screens share consistent styling

### Task 4.3 — Accessibility and responsive review
- Goal: Ensure the dashboard is usable across devices and audiences.
- Scope:
  - keyboard navigation
  - readable contrast
  - responsive layout for smaller screens
- Acceptance criteria:
  - interface remains usable on desktop and tablet
  - basic accessibility standards are met

## Definition of done for the overall initiative

The UI gap initiative is complete when:
- all configured servers are visible in a dashboard
- tools can be discovered and tested from the interface
- configuration changes can be managed without raw JSON editing
- execution outcomes are traceable and understandable
- permissions and audit flows are in place for operational trust
- first-time users can understand the value of the product quickly

## Recommended implementation order

1. Server dashboard
2. Execution history
3. Tool catalog
4. Execution console
5. Configuration editor
6. Permissions and audit
7. Onboarding
8. Design polish and accessibility
