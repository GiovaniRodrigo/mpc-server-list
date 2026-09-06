# Ordered Atomic Implementation Plan

This file reorganizes the UI gap work into a strict delivery sequence and describes the implementation actions expected in the codebase for each atomic task.

## 1. Server dashboard foundation

### 1.1 Create server status dashboard

Goal:
- Display all configured MCP servers in a single operational view.

Implementation actions in code:
- Extend `MCPRouter` with a method to return server metadata in a UI-friendly structure.
- Add a function such as `list_servers()` output normalized into `[{key, command, description, status}]`.
- Add an endpoint or view layer that renders a card/table for each server.
- Add a `status` field derived from connection checks, configuration validation, and last execution state.
- Provide a basic filter/search box by server key and description.

Code targets:
- `src/router.py`
- `main.py`
- future `ui` or `app` layer

Acceptance criteria:
- All configured servers are visible from one screen.
- Status is readable at a glance.
- Broken or missing servers are clearly highlighted.

### 1.2 Add health summary widgets

Goal:
- Summarize operational health in compact KPI cards.

Implementation actions in code:
- Add a summary service that computes totals for `total`, `online`, `failed`, and `last_activity`.
- Expose a lightweight `health_summary()` method from the router layer.
- Create UI cards that render each metric with color-coded states.
- Ensure the data refreshes on page load or poll cycle.

Code targets:
- `src/router.py`
- future dashboard rendering module

Acceptance criteria:
- KPIs display current operational state.
- Metrics are immediately understandable without reading raw backend config.

### 1.3 Execution history panel

Goal:
- Provide a readable history of tool calls and their outcomes.

Implementation actions in code:
- Create a structured execution record with fields: `timestamp`, `server_key`, `tool_name`, `status`, `duration_ms`, `request`, `response`.
- Add a logging layer or memory-backed store to persist recent runs.
- Add a table or timeline view that renders the last executions.
- Add quick filtering by server or failure-only view.

Code targets:
- `src/router.py`
- `main.py`
- future `history` or `logs` module

Acceptance criteria:
- A user can review recent actions without reading terminal output.
- Failed executions show meaningful context.

## 2. Tool discovery and testing flow

### 2.1 Create tool catalog page

Goal:
- Make available tools discoverable without raw configuration or terminal access.

Implementation actions in code:
- Add a method to list tools for a server and normalize them into a UI model.
- Return `name`, `description`, `input_schema`, and `server_key` for each tool.
- Build a catalog page with filters and grouping by server.
- Add search by tool name or keyword.

Code targets:
- `src/router.py`
- future `tool_catalog` view

Acceptance criteria:
- Users can browse the available tool set visually.
- Metadata is readable and consistent.

### 2.2 Create tool detail view

Goal:
- Show detailed information before execution.

Implementation actions in code:
- Add a selected-tool detail screen that displays:
  - tool description
  - required arguments
  - input schema
  - sample invocation
  - server ownership
- Add a "Run tool" action from this detail panel.

Code targets:
- future `tool_detail` view
- `src/router.py`

Acceptance criteria:
- A user understands the purpose and required inputs before running a tool.
- The panel is scannable, not overloaded with raw JSON alone.

### 2.3 Implement execution form

Goal:
- Let users execute tools from a safe UI without terminal interaction.

Implementation actions in code:
- Create a tool form with fields generated from the tool schema.
- Add validation rules for required fields and JSON structure.
- Add a request preview before submission.
- Capture response and render it in a readable panel.
- Add handling for execution errors and timeout states.

Code targets:
- `src/router.py`
- `main.py`
- future `tool_executor` view

Acceptance criteria:
- A user can trigger a tool from the UI.
- Invalid inputs are blocked before the backend call.
- Response output is readable and structured.

## 3. Configuration and operations management

### 3.1 Build server configuration editor

Goal:
- Remove manual JSON editing from daily operations.

Implementation actions in code:
- Add a configuration model in the backend to represent server entries.
- Create a form with fields for `name`, `command`, `args`, `env`, `description`, and `enabled`.
- Add `save_server_config`, `update_server`, and `delete_server` actions.
- Validate fields before updating the JSON catalog.

Code targets:
- `src/router.py`
- `config/mcp_servers.json`
- future admin UI module

Acceptance criteria:
- New servers can be created from the interface.
- Existing entries can be edited without raw file manipulation.
- Deletions and updates are explicit and reversible.

### 3.2 Add validation and rollback

Goal:
- Prevent broken configuration from reaching production.

Implementation actions in code:
- Add validation logic to check required fields and argument structure.
- Show warnings before saving invalid config.
- Add a rollback mechanism for previous configuration state.
- Provide error messages that explain missing or malformed values.

Code targets:
- `src/router.py`
- config management module

Acceptance criteria:
- Invalid config is blocked before save.
- Users can recover from failed changes without losing prior working settings.

### 3.3 Add roles and permissions model

Goal:
- Protect privileged operations and sensitive tools.

Implementation actions in code:
- Define role objects such as `viewer`, `operator`, and `admin`.
- Add permission checks before tool execution or config editing.
- Attach audit metadata to every sensitive operation.
- Add a permission screen to assign roles or scopes.

Code targets:
- future auth/permission layer
- backend execution guard

Acceptance criteria:
- Unauthorized activity is denied with a clear message.
- Audit records exist for role-based actions.

## 4. Adoption and product polish

### 4.1 Create onboarding flow

Goal:
- Help a first-time user understand the product quickly.

Implementation actions in code:
- Add a landing page with a plain-language explanation of the platform.
- Create a guided onboarding flow for first-time setup.
- Provide example workflows: connect server, discover tools, execute sample call.

Code targets:
- `main.py`
- future landing page/app shell

Acceptance criteria:
- A user understands the value proposition in a few minutes.
- The first successful execution path is easy to follow.

### 4.2 Establish design system

Goal:
- Create a coherent visual language.

Implementation actions in code:
- Define color tokens for healthy, warning, and failed states.
- Standardize card, table, form, and badge components.
- Reuse consistent spacing and layout rules across dashboards.

Code targets:
- future frontend style system
- shared component library

Acceptance criteria:
- Interface patterns remain visually consistent across the product.
- Operational screens feel trustworthy and easy to scan.

### 4.3 Accessibility and responsive review

Goal:
- Make the tool usable for a larger range of users and devices.

Implementation actions in code:
- Ensure keyboard navigation is supported.
- Maintain readable contrast and focus states.
- Add responsive layout rules for tablet and smaller screens.
- Review label clarity for forms and forms errors.

Code targets:
- future frontend layout and component styles

Acceptance criteria:
- The product remains usable on smaller layouts.
- Core user flows work with keyboard-only navigation.

## Recommended sequence for implementation

1. Server dashboard
2. Server health metrics
3. Execution history
4. Tool catalog
5. Tool detail view
6. Tool execution form
7. Configuration editor
8. Validation and rollback
9. Permission model
10. Onboarding
11. Design system
12. Accessibility review

## Definition of done

The UI gap initiative is complete only when:
- all servers are visible and status-aware
- tools can be discovered and executed through a UI
- configuration can be managed without raw JSON edits
- execution history and failures are visible
- permissions and audit flows exist
- onboarding makes the product understandable to new users
