# Work IQ Architecture and Flow (Code-Derived)

This document describes the architecture and runtime flows based on the current implementation.

## 1) System Architecture

```mermaid
flowchart LR
    U[Browser UI\nindex.html + flyout-panel.html] -->|HTTP/JSON| F[Flask App\napp.py]

    F -->|Simulator mode| SE[Simulator Engine\nsimulator/engine.py]
    F -->|Hybrid mode| AOAI[Azure OpenAI\nOpenAIChatCompletionClient]
    F -->|Tool calls| MCP[MCP Stdio Tool\nWork IQ simulator process]

    F -->|Panel aggregation| ORCH[PanelOrchestrator\nsimulator/agents/orchestrator.py]
    ORCH --> AG1[SuggestionsAgent]
    ORCH --> AG2[TimelineAgent]
    ORCH --> AG3[NextStepsAgent]
    ORCH --> AG4[ProgressAgent]

    F -->|Feature gating| ACL[FeatureACL\nsimulator/agents/acl_manager.py]

    F -->|Connector APIs| CM[ConnectorManager\nconnectors/manager.py]
    CM --> C1[MSGraphConnector]
    CM --> C2[CustomAPIConnector]
    CM --> C3[GCPConnector]
    CM --> C4[AWSConnector]
    CM --> C5[SocialMediaConnector]
```

## 2) Core Backend Building Blocks

- Flask web/API layer
  - Route entry points are implemented in app.py.
  - Serves UI files directly using send_file for index and flyout panel.

- Runtime modes
  - Simulator-only mode when Azure endpoint is absent.
  - Hybrid mode when Azure endpoint is configured, with MCP tool integration.

- Scenario and persona state
  - Scenario loaded from simulator/scenarios/*.
  - Persona loaded from scenario personas.json and persisted in Flask session.

- Connector framework
  - ConnectorType and DataConnector abstractions in connectors/base.py.
  - ConnectorManager registry + orchestration in connectors/manager.py.
  - Connectors initialized at startup and exposed via connector endpoints.

- Panel agent framework
  - Parallel panel orchestration in simulator/agents/orchestrator.py.
  - Feature ACL checks in simulator/agents/acl_manager.py.

## 3) Startup Flow

```mermaid
sequenceDiagram
    participant Main as app.py main()
    participant Init as init_agent()
    participant Sim as simulator/engine.py
    participant AOAI as Azure OpenAI Client
    participant Conn as _init_connectors()

    Main->>Init: initialize globals, env, scenario path
    Init->>Sim: load_scenario(...)

    alt no Azure endpoint
        Init-->>Main: simulator_only = true
    else Azure endpoint configured
        Init->>AOAI: create OpenAIChatCompletionClient
        Init->>Init: resolve MCP command/args
        Init->>Conn: register MS Graph + config connectors
        Init-->>Main: simulator_only = false
    end

    Main->>Main: app.run(host=127.0.0.1, port=WORKIQ_PORT)
```

## 4) Chat Request Flow

### 4.1 Simulator-Only Path

```mermaid
sequenceDiagram
    participant UI as Browser
    participant API as POST /api/chat
    participant Sim as sim_engine.ask()

    UI->>API: message, transport, optional data_filters
    API->>Sim: ask(scenario, message, persona_id)
    API->>API: _maybe_enforce_source_intent(...)
    API->>API: _build_demo_trace(mode=simulator-only)
    API-->>UI: response + citations + trace + active_persona
```

### 4.2 Hybrid (Agent + MCP) Path

```mermaid
sequenceDiagram
    participant UI as Browser
    participant API as POST /api/chat
    participant Agent as Agent(client, tools=[MCPStdioTool])
    participant MCP as workiq-mcp tool process

    UI->>API: message, transport
    API->>Agent: run(user_message)
    Agent->>MCP: ask_work_iq/fetch/create_entity/update_entity
    MCP-->>Agent: tool outputs
    Agent-->>API: synthesized response
    API->>API: _extract_token_usage(response)
    API->>API: _extract_citations(response)
    API->>API: fallback citation-id resolve via simulator
    API->>API: _build_demo_trace(mode=agent+mcp)
    API-->>UI: response + citations + token_usage trace
```

## 5) Panel Load and Update Flow

### 5.1 Initial Page Load

```mermaid
sequenceDiagram
    participant UI as index.html
    participant JS as static/orchestrator.js
    participant API as Flask panel endpoints

    UI->>JS: initPanelOrchestrator()
    JS->>API: GET /api/feature-acl
    JS->>API: POST /api/agent/orchestrate
    JS->>API: POST /api/agent/scenario-timeline
    JS->>API: POST /api/agent/whatif-simulation
    JS->>API: POST /api/agent/pre-mortem-generator
    JS->>API: POST /api/agent/progress-tracking
    JS->>API: POST /api/agent/interactive-dashboard
    API-->>JS: panel payloads (or fallback-safe responses)
    JS-->>UI: render panel sections
```

### 5.2 Post-Message Updates

```mermaid
flowchart TD
    A[Chat response received in index.html] --> B[updateAllPanelsAfterMessage(response)]
    B --> C[POST /api/agent/timeline]
    B --> D[POST /api/agent/nextsteps]
    C --> E[UI timeline refreshed]
    D --> F[UI next steps refreshed]
```

## 6) Feature ACL Flow

```mermaid
flowchart LR
    P[Active persona in session] --> N[FeatureACL.normalize_persona_id]
    N --> K{Feature key in FEATURE_ACCESS?}
    K -->|No| Deny[Deny access]
    K -->|Yes| Check[persona in allowed set]
    Check -->|Yes| Allow[Return 200 with data]
    Check -->|No| Deny403[Return 403 access restricted]
```

## 7) Connector Flow

```mermaid
sequenceDiagram
    participant UI as Connector UI
    participant API as /api/connectors*
    participant CM as ConnectorManager
    participant CX as DataConnector impl

    UI->>API: GET /api/connectors
    API->>CM: list_connectors()
    CM-->>API: connector metadata
    API-->>UI: list

    UI->>API: POST /api/connectors/create-custom
    API->>CM: register_connector(CustomAPIConnector)
    API-->>UI: created connector_id

    UI->>API: POST /api/connectors/fetch
    API->>CM: fetch_resource_from_all(...)
    CM->>CX: fetch_resource(...)
    CX-->>CM: ConnectorResponse
    CM-->>API: aggregated responses
    API-->>UI: normalized result set
```

## 8) API Surface (Grouped)

- UI and session
  - GET /
  - GET /flyout-panel
  - GET /api/status
  - GET /api/personas
  - POST /api/persona
  - POST /api/clear

- Chat and trace
  - POST /api/chat

- Connectors
  - GET /api/connectors
  - GET /api/connectors/<connector_id>/status
  - POST /api/connectors/<connector_id>/authenticate
  - GET /api/connectors/<connector_id>/resources
  - POST /api/connectors/fetch
  - POST /api/connectors/search
  - POST /api/connectors/create-custom

- Agent and panel endpoints
  - POST /api/agent/orchestrate
  - POST /api/agent/timeline
  - POST /api/agent/nextsteps
  - POST /api/agent/progress-trend
  - GET /api/feature-acl
  - POST /api/agent/executive-brief
  - POST /api/agent/action-recommendations
  - POST /api/agent/scenario-timeline
  - POST /api/agent/whatif-simulation
  - POST /api/agent/pre-mortem-generator
  - POST /api/agent/progress-tracking
  - POST /api/agent/interactive-dashboard

## 9) Key Code Anchors Used

- app.py
  - Initialization, chat, connectors, orchestrator and panel routes.

- templates/index.html
  - UI bootstrap, chat request calls, panel initialization trigger.

- static/orchestrator.js
  - Panel orchestration, ACL load, panel-specific loaders and update hooks.

- simulator/agents/orchestrator.py
  - Parallel execution + fallback path for panel worker agents.

- simulator/agents/acl_manager.py
  - Persona-to-feature access policy.

- connectors/base.py and connectors/manager.py
  - Connector contracts, registry, auth and multi-source operations.
