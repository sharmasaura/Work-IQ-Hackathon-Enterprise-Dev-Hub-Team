"""
Web UI for the Work IQ Agent using Flask.
Provides a browser-based chat interface.
"""

import os
import asyncio
import sys
import shlex
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify, session, send_file
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework import MCPStdioTool

# Data Connector Framework
from connectors import (
    get_connector_manager,
    ConnectorConfig,
    ConnectorType,
    MSGraphConnector,
    CustomAPIConnector,
)

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-change-in-production")

# Global agent instance
agent = None
mcp_tool = None
sim_engine = None
sim_scenario = None
sim_persona = None
simulator_only = False
model_client = None
mcp_command_cfg = None
mcp_args_cfg = []
available_personas = []

# Global token usage tracker (captured from Azure responses)
last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

AGENT_INSTRUCTIONS = """You are a helpful Work IQ assistant.
You have access to Work IQ tools through the connected MCP server:
- ask_work_iq: Query Work IQ for information about people, meetings, emails, Teams chats, files, and OneNote pages
- fetch: Read rows from Work IQ tables
- create_entity: Create new rows in Work IQ tables
- update_entity: Update existing rows in Work IQ tables

RESPONSE FORMAT GUIDELINES:

1. Use ask_work_iq as your primary tool to ground answers in the user's work context
2. Provide a clear, direct answer without including any "Sources", "Citations", or "References" sections
3. When you answer questions, mention the source document type inline like:
   - Reference emails as: "Email EML-XXX states..." or "According to the email (EML-XXX)..."
   - Reference meetings as: "In meeting MTG-XXX..." or "The meeting notes (MTG-XXX) show..."
   - Reference OneNote as: "OneNote page ONE-XXX indicates..." 
   - Reference files as: "File FIL-XXX contains..."
   This allows source links to be shown alongside your answer.
4. Do NOT include JSON blocks or tool output in your response
5. The ask_work_iq tool returns citations automatically; preserve the source IDs in your synthesis
6. Focus on providing insights and answering the question clearly

Format examples:
- "The status (ACT-002) shows it's currently Open and due 2026-06-11"
- "Email EML-005 indicates the rollback was successful"
- "Meeting MTG-001 noted that monitoring should continue for 2 hours"

This approach keeps your response natural while preserving the evidence trail."""


def _env_truthy(name: str) -> bool:
    """Parse common truthy env values."""
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _extract_citations(response_obj) -> list:
    """Best-effort citation extraction across possible agent response shapes.
    
    Tries multiple strategies:
    1. Direct dict/object attributes
    2. Nested payloads in common attributes
    3. Parse JSON strings in response text for embedded citations
    """
    # Direct list on known dict/object shapes.
    try:
        if isinstance(response_obj, dict):
            cits = response_obj.get("citations")
            if isinstance(cits, list):
                return cits
        cits = getattr(response_obj, "citations", None)
        if isinstance(cits, list):
            return cits
    except Exception:
        pass

    # Some SDK responses expose nested payloads.
    for attr in ("output", "result", "data", "message"):
        try:
            nested = getattr(response_obj, attr, None)
            if isinstance(nested, dict):
                cits = nested.get("citations")
                if isinstance(cits, list):
                    return cits
            elif nested is not None:
                cits = getattr(nested, "citations", None)
                if isinstance(cits, list):
                    return cits
        except Exception:
            continue

    # Try to parse JSON from response text to find embedded citations
    # (handles MCP tool responses embedded in agent output)
    try:
        response_text = str(response_obj) if response_obj else ""
        if "{" in response_text and "citations" in response_text.lower():
            # Try to extract JSON blocks
            import re
            json_pattern = r"\{[^{}]*\"citations\"[^{}]*\}"
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if "citations" in data and isinstance(data["citations"], list):
                        return data["citations"]
                except Exception:
                    continue
    except Exception:
        pass

    return []


def _extract_citation_ids_from_text(text: str) -> list[str]:
    """Extract citation ID patterns from response text like EML-003, MTG-001, ACT-002, etc."""
    if not text:
        return []
    
    import re
    # Match patterns like: EML-123, MTG-456, ACT-789, FIL-012, ONE-345, etc.
    pattern = r'\b([A-Z]{2,3})-(\d{3,4})\b'
    matches = re.findall(pattern, text)
    
    # Build full citation IDs, de-duplicate while preserving order
    seen = set()
    citation_ids = []
    for prefix, num in matches:
        cid = f"{prefix}-{num}"
        if cid not in seen:
            citation_ids.append(cid)
            seen.add(cid)
    
    return citation_ids


def _maybe_enforce_source_intent(sc, engine_module, question: str, persona_id: str | None, result: dict) -> dict:
    """If a source-specific question (e.g., OneNote) returns mismatched golden sources,
    re-answer via source-filtered retrieval to keep citations aligned with user intent."""
    try:
        detect_hints = getattr(engine_module, "_detect_source_hints", None)
        if not callable(detect_hints):
            return result

        hints = detect_hints(question) or set()
        if not hints:
            return result

        if result.get("source") != "golden":
            return result

        matched_id = result.get("matched")
        if not matched_id:
            return result

        golden_entry = next((g for g in sc.golden if g.get("id") == matched_id), None)
        if not golden_entry:
            return result

        cited_kinds = set()
        for cid in golden_entry.get("citations", []):
            entry = sc.index.get(cid)
            if entry is None:
                continue
            kind, _ = entry
            cited_kinds.add(kind)

        if cited_kinds & set(hints):
            return result

        all_snippets = engine_module._all_snippets(sc, persona_id)
        filter_by_hints = getattr(engine_module, "_filter_snippets_by_hints", None)
        if callable(filter_by_hints):
            all_snippets = filter_by_hints(sc, all_snippets, hints)

        top = engine_module._retrieve(all_snippets, question)
        cited_ids = [s.get("id") for s in top if s.get("id")]
        visible, _ = engine_module.resolve_citations(sc, cited_ids, persona_id)

        if top:
            bullets = "\n".join(f"- [{s['id']}] {s['text'][:140]}" for s in top)
            response = (
                "Answer constrained to requested source type(s). Closest matching signals:\n"
                f"{bullets}"
            )
        else:
            response = "No relevant signals were found for the requested source type(s)."

        return {
            "response": response,
            "conversationId": result.get("conversationId"),
            "citations": visible,
            "trimmed": [],
            "source": "retrieval-only",
            "matched": None,
            "tool": None,
        }
    except Exception:
        return result


def _fixture_for_kind(kind: str) -> str:
    mapping = {
        "email": "emails.json",
        "meeting": "meetings.json",
        "action_item": "meetings.json#action_items",
        "teams_message": "teams.json",
        "file": "files.json",
        "onenote_page": "onenote.json",
        "person": "people.json",
        "milestone": "tables/milestone_tracker.json",
        "capa": "tables/capa_tracker.json",
    }
    return mapping.get(kind, "tables/*.json")


def _extract_token_usage(response_obj) -> dict:
    """Extract token usage information from agent response.
    
    Returns dict with: {
        'prompt_tokens': int,
        'completion_tokens': int, 
        'total_tokens': int
    }
    
    Handles Azure OpenAI field names (input_token_count, output_token_count, total_token_count)
    as well as standard OpenAI field names (prompt_tokens, completion_tokens, total_tokens).
    """
    global last_token_usage
    usage_info = {}
    
    try:
        # First, try to get from global tracker (captured by Azure SDK)
        if last_token_usage.get('total_tokens', 0) > 0:
            return last_token_usage.copy()
        
        # Try usage_details attribute first (AgentResponse primary source)
        if hasattr(response_obj, 'usage_details'):
            usage = response_obj.usage_details
            if usage and isinstance(usage, dict):
                # Map Azure field names to standard names
                # Azure uses: input_token_count, output_token_count, total_token_count
                # Standard uses: prompt_tokens, completion_tokens, total_tokens
                usage_info['prompt_tokens'] = usage.get('input_token_count', 0) or usage.get('prompt_tokens', 0)
                usage_info['completion_tokens'] = usage.get('output_token_count', 0) or usage.get('completion_tokens', 0)
                usage_info['total_tokens'] = usage.get('total_token_count', 0) or usage.get('total_tokens', 0)
                
                # If we got actual values, return them
                if usage_info.get('total_tokens', 0) > 0:
                    return usage_info
        
        # Try direct usage attribute next (standard OpenAI format)
        if not usage_info and hasattr(response_obj, 'usage'):
            usage = response_obj.usage
            if usage:
                if isinstance(usage, dict):
                    usage_info.update(usage)
                else:
                    usage_info['prompt_tokens'] = getattr(usage, 'prompt_tokens', 0)
                    usage_info['completion_tokens'] = getattr(usage, 'completion_tokens', 0)
                    usage_info['total_tokens'] = getattr(usage, 'total_tokens', 0)
        
        # Try response string content (may contain usage JSON)
        if not usage_info:
            response_str = str(response_obj)
            if '"total_tokens"' in response_str or "'total_tokens'" in response_str:
                try:
                    import re
                    usage_match = re.search(r'"total_tokens"\s*:\s*(\d+)', response_str)
                    if usage_match:
                        total = int(usage_match.group(1))
                        prompt_match = re.search(r'"prompt_tokens"\s*:\s*(\d+)', response_str)
                        comp_match = re.search(r'"completion_tokens"\s*:\s*(\d+)', response_str)
                        usage_info['total_tokens'] = total
                        usage_info['prompt_tokens'] = int(prompt_match.group(1)) if prompt_match else 0
                        usage_info['completion_tokens'] = int(comp_match.group(1)) if comp_match else 0
                except Exception:
                    pass
        
        # Try nested message attributes (Azure SDK may embed it in message)
        if not usage_info and hasattr(response_obj, 'messages'):
            messages = response_obj.messages
            if messages and len(messages) > 0:
                msg = messages[-1]
                if hasattr(msg, 'usage_details'):
                    usage = msg.usage_details
                    if usage and isinstance(usage, dict):
                        # Map Azure field names
                        usage_info['prompt_tokens'] = usage.get('input_token_count', 0) or usage.get('prompt_tokens', 0)
                        usage_info['completion_tokens'] = usage.get('output_token_count', 0) or usage.get('completion_tokens', 0)
                        usage_info['total_tokens'] = usage.get('total_token_count', 0) or usage.get('total_tokens', 0)
    except Exception as e:
        pass
    
    # Ensure we have defaults if nothing was found
    result = {
        'prompt_tokens': usage_info.get('prompt_tokens', 0),
        'completion_tokens': usage_info.get('completion_tokens', 0),
        'total_tokens': usage_info.get('total_tokens', 0)
    }
    
    # Update global tracker if we found usage
    if result.get('total_tokens', 0) > 0:
        last_token_usage = result.copy()
    
    return result


def _build_demo_trace(
    question: str,
    active_persona: str,
    mode: str,
    citations: list,
    source: str | None,
    matched: str | None,
    transport: str,
    token_usage: dict | None = None,
) -> dict:
    """Build a demo-friendly trace payload for UI flyout."""
    if token_usage is None:
        token_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    
    files_used = []
    seen = set()
    for c in citations:
        kind = (c or {}).get("kind", "")
        f = _fixture_for_kind(kind)
        if f not in seen:
            seen.add(f)
            files_used.append(f)

    steps = [
        f"Received question over REST: {question[:120]}",
        f"Applied active persona: {active_persona}",
        f"Selected transport mode: {transport}",
        f"Execution path: {mode}",
    ]

    if matched:
        steps.append(f"Golden answer matched: {matched}")
    elif source:
        steps.append(f"Answer source mode: {source}")

    if citations:
        steps.append(f"Resolved citations: {len(citations)}")
    else:
        steps.append("No citations resolved for this response")
    
    # Add token usage to steps if in hybrid/LLM mode
    if mode == "agent+mcp" and token_usage.get('total_tokens', 0) > 0:
        total = token_usage.get('total_tokens', 0)
        prompt = token_usage.get('prompt_tokens', 0)
        completion = token_usage.get('completion_tokens', 0)
        steps.append(f"Token consumption: {total} total ({prompt} prompt + {completion} completion)")

    return {
        "transport": transport,
        "mode": mode,
        "active_persona": active_persona,
        "source": source,
        "matched": matched,
        "files_used": files_used,
        "steps": steps,
        "token_usage": token_usage,
    }

def _is_allowed_origin(origin: str | None) -> bool:
    """Allow local-dev browser origins (Live Server / Flask) on any localhost port."""
    if not origin:
        return False

    try:
        parsed = urlparse(origin)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    return parsed.hostname in {"127.0.0.1", "localhost"}


def _get_required_env(name: str) -> str:
    """Return a required env var value or raise a helpful error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _resolve_mcp_command(raw_command: str) -> str:
    """Resolve MCP command path and fail-safe to current interpreter if moved."""
    cmd = (raw_command or "").strip()
    if not cmd:
        raise ValueError("Missing required environment variable: WORKIQ_MCP_COMMAND")

    # Keep non-path commands (e.g., npx) unchanged.
    if not any(sep in cmd for sep in ("\\", "/", ":")):
        return cmd

    p = Path(cmd)
    if p.exists():
        return str(p)

    # If configured path is stale after folder moves, use current venv interpreter.
    return sys.executable


def _resolve_scenario_path(raw_scenario: str) -> Path:
    """Resolve scenario path as absolute, relative to repo root, or relative to simulator/."""
    p = Path(raw_scenario)
    if p.is_absolute():
        return p

    repo_root = Path(__file__).resolve().parent
    from_repo = repo_root / p
    if from_repo.exists():
        return from_repo

    return repo_root / "simulator" / p


def _load_personas_for_scenario(scenario_path: Path) -> list[dict]:
    """Load persona metadata from scenario personas.json if present."""
    personas_file = scenario_path / "personas.json"
    if not personas_file.exists():
        return []

    try:
        with open(personas_file, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        personas = payload.get("personas", []) if isinstance(payload, dict) else []
        return [p for p in personas if isinstance(p, dict) and p.get("id")]
    except Exception:
        return []


def init_agent():
    """Initialize the agent on app startup."""
    global agent, mcp_tool, sim_engine, sim_scenario, sim_persona, simulator_only
    global model_client, mcp_command_cfg, mcp_args_cfg, available_personas
    try:
        endpoint = os.getenv("WORKIQ_AZURE_ENDPOINT", "").strip()
        # Treat template placeholder as effectively unset.
        if "YOUR-RESOURCE" in endpoint.upper():
            endpoint = ""
        # Force simulator-only mode only if no valid LLM endpoint is configured.
        # If endpoint is provided, use LLM + simulator (simulator data feeds LLM for synthesis).
        force_simulator_only = not bool(endpoint)
        raw_scenario = os.getenv("WORKIQ_SIM_SCENARIO", r"scenarios\c2-contoso")
        scenario_path = _resolve_scenario_path(raw_scenario)
        available_personas = _load_personas_for_scenario(scenario_path)
        sim_persona = os.getenv("WORKIQ_SIM_PERSONA", "").strip() or "all"

        # Always load simulator engine for citation resolution and reference queries
        # (even in hybrid mode, we use it for looking up citation metadata)
        simulator_dir = Path(__file__).resolve().parent / "simulator"
        if str(simulator_dir) not in sys.path:
            sys.path.insert(0, str(simulator_dir))

        import engine as sim_engine_module  # type: ignore

        sim_scenario = sim_engine_module.load_scenario(str(scenario_path))
        sim_engine = sim_engine_module

        # Simulator-only mode: if no Azure endpoint is configured, answer directly from
        # simulator engine (same behavior family as simulator/demo.py).
        if force_simulator_only or not endpoint:
            simulator_only = True

            # Keep non-None sentinel for status checks.
            agent = object()
            mcp_tool = None
            model_client = None
            return True

        # Hybrid mode: Setup Azure OpenAI client (simulator engine loaded above for citation resolution)
        model = os.getenv("WORKIQ_MODEL", "gpt-5-mini")
        api_version = os.getenv("WORKIQ_AZURE_API_VERSION", "2024-08-01-preview")

        model_client = OpenAIChatCompletionClient(
            model=model,
            credential=DefaultAzureCredential(),
            azure_endpoint=endpoint,
            api_version=api_version,
        )

        # Setup MCP stdio tool for Work IQ
        mcp_command_cfg = _resolve_mcp_command(_get_required_env("WORKIQ_MCP_COMMAND"))
        mcp_args_cfg = shlex.split(os.getenv("WORKIQ_MCP_ARGS", ""), posix=False)
        mcp_tool = object()

        # Create agent
        agent = object()
        simulator_only = False
        
        # Initialize connector framework with MS Graph
        _init_connectors()
        
        return True
    except Exception as e:
        print(f"Failed to initialize agent: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def _init_connectors():
    """Initialize data connectors for multi-source queries."""
    try:
        manager = get_connector_manager()
        
        # Always register MS Graph connector
        endpoint = os.getenv("WORKIQ_AZURE_ENDPOINT", "").strip()
        if endpoint and "YOUR-RESOURCE" not in endpoint.upper():
            msgraph_config = ConnectorConfig(
                connector_id="msgraph_primary",
                connector_type=ConnectorType.MSGRAPH,
                enabled=True,
                auth_config={
                    "tenant_id": os.getenv("WORKIQ_AZURE_TENANT", ""),
                    "client_id": os.getenv("WORKIQ_AZURE_CLIENT_ID", ""),
                    "client_secret": os.getenv("WORKIQ_AZURE_CLIENT_SECRET", ""),
                }
            )
            msgraph = MSGraphConnector(msgraph_config)
            manager.register_connector(msgraph)
        
        # Load additional connectors from config if present
        config_path = Path(__file__).resolve().parent / "connectors" / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Expand environment variables in config
                config_json = json.dumps(config_data)
                for key, value in os.environ.items():
                    config_json = config_json.replace(f"${{{key}}}", value)
                config_data = json.loads(config_json)
                
                # Register configured connectors
                for connector_config in config_data.get("connectors", []):
                    if not connector_config.get("enabled", True):
                        continue
                    
                    conn_type = connector_config.get("type")
                    conn_id = connector_config.get("id")
                    
                    # Create appropriate connector based on type
                    if conn_type == "msgraph":
                        config = ConnectorConfig(
                            connector_id=conn_id,
                            connector_type=ConnectorType.MSGRAPH,
                            enabled=True,
                            auth_config=connector_config.get("auth")
                        )
                        manager.register_connector(MSGraphConnector(config))
                    elif conn_type == "custom_api":
                        config = ConnectorConfig(
                            connector_id=conn_id,
                            connector_type=ConnectorType.CUSTOM_API,
                            enabled=True,
                            auth_config=connector_config.get("auth"),
                            custom_config=connector_config.get("config")
                        )
                        manager.register_connector(CustomAPIConnector(config))
                    # Add other connector types as needed
                    
            except Exception as e:
                print(f"Warning: Could not load connector config: {e}", file=sys.stderr)
        
        print(f"[OK] Initialized {len(manager.list_connectors())} connectors", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Connector initialization failed: {e}", file=sys.stderr)


@app.before_request
def before_request():
    """Initialize session if needed."""
    if "conversation_id" not in session:
        session["conversation_id"] = str(datetime.now().timestamp())

    if "persona_id" not in session:
        session["persona_id"] = sim_persona or "all"


@app.after_request
def add_cors_headers(response):
    """Allow local browser UIs (e.g., Live Server) to call Flask API routes."""
    origin = request.headers.get("Origin")
    if _is_allowed_origin(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.route("/")
def index():
    """Serve the main chat interface directly (bypass Jinja2 to avoid truncation)."""
    html_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
    return send_file(html_path, mimetype='text/html')


@app.route("/flyout-panel", methods=["GET"])
def flyout_panel():
    """Serve the side panel content (loaded dynamically)."""
    panel_path = os.path.join(os.path.dirname(__file__), 'templates', 'flyout-panel.html')
    return send_file(panel_path, mimetype='text/html')


@app.route("/api/personas", methods=["GET", "OPTIONS"])
def get_personas():
    """Return available simulator personas and the active selection."""
    if request.method == "OPTIONS":
        return ("", 204)

    personas = [
        {
            "id": p.get("id"),
            "label": p.get("label") or p.get("id"),
            "role": p.get("role") or "",
        }
        for p in available_personas
    ]

    return jsonify({
        "success": True,
        "personas": personas,
        "active_persona": session.get("persona_id", sim_persona or "all")
    })


@app.route("/api/persona", methods=["POST", "OPTIONS"])
def set_persona():
    """Set active simulator persona for this browser session."""
    if request.method == "OPTIONS":
        return ("", 204)

    data = request.get_json(silent=True) or {}
    requested = str(data.get("persona", "")).strip()
    if not requested:
        return jsonify({"success": False, "error": "Missing persona"}), 400

    valid_personas = {"all"} | {p.get("id") for p in available_personas if p.get("id")}
    if requested not in valid_personas:
        return jsonify({
            "success": False,
            "error": f"Unknown persona '{requested}'",
            "valid": sorted(valid_personas)
        }), 400

    session["persona_id"] = requested
    return jsonify({"success": True, "active_persona": requested})


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    """Handle chat messages via API."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        data = request.get_json(silent=True) or {}
        user_message = data.get("message", "").strip()
        transport_mode = str(data.get("transport", "MCP")).strip().upper() or "MCP"
        data_filters = data.get("data_filters")  # Optional data duration filters

        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        if not agent:
            return jsonify({"error": "Agent not initialized"}), 500

        use_simulator_only = simulator_only or _env_truthy("WORKIQ_SIMULATOR_ONLY")

        if use_simulator_only:
            # If app initialized in non-simulator mode but env now requires simulator-only,
            # lazily prepare simulator engine for this request.
            global sim_engine, sim_scenario
            if sim_engine is None or sim_scenario is None:
                raw_scenario = os.getenv("WORKIQ_SIM_SCENARIO", r"scenarios\c2-contoso")
                scenario_path = _resolve_scenario_path(raw_scenario)
                simulator_dir = Path(__file__).resolve().parent / "simulator"
                if str(simulator_dir) not in sys.path:
                    sys.path.insert(0, str(simulator_dir))
                import engine as sim_engine_module  # type: ignore
                sim_scenario = sim_engine_module.load_scenario(str(scenario_path))
                sim_engine = sim_engine_module

            active_persona = session.get("persona_id", sim_persona or "all")
            persona_id = None if (active_persona or "").lower() == "all" else active_persona
            result = sim_engine.ask(sim_scenario, user_message, persona_id=persona_id, data_filters=data_filters)
            result = _maybe_enforce_source_intent(sim_scenario, sim_engine, user_message, persona_id, result)
            citations = result.get("citations", [])
            trace = _build_demo_trace(
                question=user_message,
                active_persona=active_persona,
                mode="simulator-only",
                citations=citations,
                source=result.get("source"),
                matched=result.get("matched"),
                transport=transport_mode,
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            )
            return jsonify({
                "success": True,
                "response": result.get("response", ""),
                "citations": citations,
                "source": result.get("source"),
                "matched": result.get("matched"),
                "trace": trace,
                "active_persona": active_persona,
                "timestamp": datetime.now().isoformat()
            })

        if not model_client or not mcp_command_cfg:
            return jsonify({"error": "MCP tool not initialized"}), 500

        active_persona = session.get("persona_id", sim_persona or "all")
        scenario = os.getenv("WORKIQ_SIM_SCENARIO", r"scenarios\c2-contoso")

        request_tool = MCPStdioTool(
            name="workiq-mcp",
            command=mcp_command_cfg,
            args=mcp_args_cfg,
            env={
                **os.environ,
                "WORKIQ_SIM_PERSONA": active_persona,
                "WORKIQ_SIM_SCENARIO": scenario,
            },
        )

        request_agent = Agent(
            client=model_client,
            name="WorkIQAgent",
            instructions=AGENT_INSTRUCTIONS,
            tools=[request_tool],
        )

        # Run the async agent call from the sync Flask handler
        async def run_agent():
            async with request_tool:
                response = await request_agent.run(user_message)
                return response

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response = loop.run_until_complete(run_agent())

        # Extract the actual response text from AgentResponse object
        response_text = str(response) if response else ""
        
        # Extract token usage information from response
        token_usage = _extract_token_usage(response)
        
        # If still no tokens found, estimate based on response length (rough approximation)
        if token_usage.get('total_tokens', 0) == 0 and response_text:
            # Rough estimation: ~4 chars per token for English text
            estimated_completion_tokens = len(response_text) // 4
            estimated_prompt_tokens = len(user_message) // 4
            token_usage = {
                'prompt_tokens': max(1, estimated_prompt_tokens),
                'completion_tokens': max(1, estimated_completion_tokens),
                'total_tokens': max(1, estimated_prompt_tokens + estimated_completion_tokens)
            }
        
        # Try to extract citations from the response
        citations = _extract_citations(response)
        
        # If no citations found from direct extraction, try parsing the response text
        # for JSON tool outputs (ask_work_iq returns JSON with citations)
        if not citations and response_text:
            try:
                # Look for JSON blocks in the response that might contain citations
                import re
                json_blocks = re.findall(r'\{[^{}]*?"citations"[^{}]*?\}', response_text, re.DOTALL)
                for block_str in json_blocks:
                    try:
                        block_data = json.loads(block_str)
                        if isinstance(block_data.get("citations"), list):
                            citations = block_data["citations"]
                            break
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass
        
        # If still no citations, try to extract citation IDs from response text (EML-003, MTG-001, etc.)
        # and resolve them through the simulator if available
        if not citations and response_text and sim_engine and sim_scenario:
            try:
                citation_ids = _extract_citation_ids_from_text(response_text)
                if citation_ids:
                    # Attempt to resolve these IDs through the simulator
                    resolved, trimmed = sim_engine.resolve_citations(sim_scenario, citation_ids, 
                                                                     persona_id=None if (active_persona or "").lower() == "all" else active_persona)
                    citations = resolved
            except Exception:
                pass
        
        trace = _build_demo_trace(
            question=user_message,
            active_persona=active_persona,
            mode="agent+mcp",
            citations=citations,
            source=None,
            matched=None,
            transport=transport_mode,
            token_usage=token_usage,
        )

        return jsonify({
            "success": True,
            "response": response_text,
            "citations": citations,
            "trace": trace,
            "active_persona": active_persona,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Error in chat endpoint: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Error processing message: {str(e)}"
        }), 500


@app.route("/api/clear", methods=["POST", "OPTIONS"])
def clear_history():
    """Clear the conversation history."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        # The agent maintains its own conversation history
        return jsonify({"success": True, "message": "Ready for new conversation"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/status", methods=["GET"])
def status():
    """Get agent status."""
    if agent and (simulator_only or _env_truthy("WORKIQ_SIMULATOR_ONLY")):
        configured_persona = os.getenv("WORKIQ_SIM_PERSONA", "quality_engineer")
        configured_scenario = os.getenv("WORKIQ_SIM_SCENARIO", r"scenarios\c2-contoso")
        active_persona = session.get("persona_id", sim_persona or configured_persona)
        return jsonify({
            "status": "ready",
            "mode": "simulator-only",
            "model": "none",
            "endpoint": "none",
            "mcp_server": "not-used",
            "persona": configured_persona,
            "active_persona": active_persona,
            "scenario": configured_scenario
        })

    if agent and mcp_tool:
        configured_endpoint = os.getenv("WORKIQ_AZURE_ENDPOINT", "")
        configured_model = os.getenv("WORKIQ_MODEL", "gpt-5-mini")
        configured_persona = os.getenv("WORKIQ_SIM_PERSONA", "quality_engineer")
        configured_scenario = os.getenv("WORKIQ_SIM_SCENARIO", r"scenarios\c2-contoso")

        return jsonify({
            "status": "ready",
            "model": configured_model,
            "endpoint": configured_endpoint,
            "mcp_server": "Work IQ Simulator",
            "persona": configured_persona,
            "scenario": configured_scenario
        })
    else:
        return jsonify({
            "status": "not_initialized",
            "error": "Agent not initialized"
        }), 500


# ===== Data Connector Endpoints =====

@app.route("/api/connectors", methods=["GET", "OPTIONS"])
def list_connectors():
    """List all available data connectors."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)
        
        manager = get_connector_manager()
        connectors = manager.list_connectors(include_disabled=request.args.get("include_disabled", "false").lower() == "true")
        
        return jsonify({
            "success": True,
            "connectors": connectors,
            "total": len(connectors)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/connectors/<connector_id>/status", methods=["GET", "OPTIONS"])
def connector_status(connector_id):
    """Get status of a specific connector."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)
        
        manager = get_connector_manager()
        connector = manager.get_connector(connector_id)
        
        if not connector:
            return jsonify({"success": False, "error": f"Connector not found: {connector_id}"}), 404
        
        return jsonify({
            "success": True,
            "status": connector.health_check()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/connectors/<connector_id>/authenticate", methods=["POST", "OPTIONS"])
def authenticate_connector(connector_id):
    """Authenticate a specific connector."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)
        
        manager = get_connector_manager()
        data = request.get_json() or {}
        credentials = data.get("credentials")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(manager.authenticate_connector(connector_id, credentials))
        
        return jsonify({
            "success": result,
            "connector_id": connector_id,
            "authenticated": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/connectors/<connector_id>/resources", methods=["GET", "OPTIONS"])
def get_connector_resources(connector_id):
    """Get supported resources for a connector."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)
        
        manager = get_connector_manager()
        connector = manager.get_connector(connector_id)
        
        if not connector:
            return jsonify({"success": False, "error": f"Connector not found: {connector_id}"}), 404
        
        return jsonify({
            "success": True,
            "connector_id": connector_id,
            "connector_name": connector.connector_name,
            "resources": connector.supported_resources
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/connectors/fetch", methods=["POST", "OPTIONS"])
def fetch_from_connectors():
    """Fetch resources from one or more connectors."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)
        
        data = request.get_json() or {}
        resource_type = data.get("resource_type")
        filters = data.get("filters")
        connector_ids = data.get("connector_ids")  # If None, uses all enabled
        
        if not resource_type:
            return jsonify({"success": False, "error": "resource_type required"}), 400
        
        manager = get_connector_manager()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        responses = loop.run_until_complete(
            manager.fetch_resource_from_all(
                resource_type=resource_type,
                connector_ids=connector_ids,
                filters=filters,
                skip=data.get("skip", 0),
                top=data.get("top", 100)
            )
        )
        
        return jsonify({
            "success": True,
            "resource_type": resource_type,
            "results": [r.to_dict() for r in responses],
            "total_sources": len(responses)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/connectors/search", methods=["POST", "OPTIONS"])
def search_connectors():
    """Search across multiple connectors."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)
        
        data = request.get_json() or {}
        query = data.get("query")
        resource_types = data.get("resource_types")
        connector_ids = data.get("connector_ids")  # If None, uses all enabled
        
        if not query:
            return jsonify({"success": False, "error": "query required"}), 400
        
        manager = get_connector_manager()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        responses = loop.run_until_complete(
            manager.search(
                query=query,
                resource_types=resource_types,
                connector_ids=connector_ids,
                skip=data.get("skip", 0),
                top=data.get("top", 50)
            )
        )
        
        return jsonify({
            "success": True,
            "query": query,
            "results": [r.to_dict() for r in responses],
            "total_sources": len(responses)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/connectors/create-custom", methods=["POST", "OPTIONS"])
def create_custom_connector():
    """Create a new custom connector."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)
        
        data = request.get_json() or {}
        connector_name = data.get("connector_name", "").strip()
        api_url = data.get("api_url", "").strip()
        auth_type = data.get("auth_type", "api_key").lower()
        description = data.get("description", "").strip()
        
        # Validation
        if not connector_name:
            return jsonify({"success": False, "error": "connector_name is required"}), 400
        
        if not api_url:
            return jsonify({"success": False, "error": "api_url is required"}), 400
        
        if auth_type not in ["api_key", "bearer_token", "oauth2", "basic_auth", "service_account", "aws_iam"]:
            return jsonify({"success": False, "error": f"Invalid auth_type: {auth_type}"}), 400
        
        # Create connector ID from name (slugify)
        connector_id = connector_name.lower().replace(" ", "_").replace("-", "_")
        connector_id = "".join(c for c in connector_id if c.isalnum() or c == "_")
        
        # Create configuration
        config = ConnectorConfig(
            connector_id=connector_id,
            connector_type=ConnectorType.CUSTOM_API,
            auth_config={"type": auth_type},
            custom_config={"base_url": api_url, "description": description}
        )
        
        # Register with manager
        manager = get_connector_manager()
        
        # Create and register custom connector
        custom_connector = CustomAPIConnector(config=config)
        manager.register_connector(custom_connector)
        
        return jsonify({
            "success": True,
            "connector_id": connector_id,
            "connector_name": connector_name,
            "message": f"Custom connector '{connector_name}' created successfully"
        }), 201
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


# ===== Panel Orchestrator Endpoints =====

@app.route("/api/agent/orchestrate", methods=["POST", "OPTIONS"])
def orchestrate_agents():
    """Orchestrate all panel agents - called on page load."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        if not sim_engine or not sim_scenario:
            return jsonify({"success": False, "error": "Simulator not initialized"}), 500

        active_persona = session.get("persona_id", sim_persona or "all")
        persona_id = None if (active_persona or "").lower() == "all" else active_persona

        # Import orchestrator
        from simulator.agents.orchestrator import PanelOrchestrator
        
        # Run orchestrator (sync mode, agents will be called as threads)
        result = asyncio.run(PanelOrchestrator.orchestrate(
            scenario=sim_scenario,
            persona_id=persona_id,
            response_count=0,
            citations=[],
            conversation_history=[],
            last_response=None,
            timeout=5.0
        ))

        return jsonify(result)

    except Exception as e:
        print(f"[ORCHESTRATOR] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Orchestrator error: {str(e)}",
            "suggestions": [],
            "timeline": [],
            "nextsteps": [],
            "progress": {}
        }), 500


@app.route("/api/agent/timeline", methods=["POST", "OPTIONS"])
def agent_timeline():
    """Generate timeline after messages are processed."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        if not sim_engine or not sim_scenario:
            return jsonify({"success": False, "error": "Simulator not initialized"}), 500

        data = request.get_json(silent=True) or {}
        active_persona = session.get("persona_id", sim_persona or "all")
        persona_id = None if (active_persona or "").lower() == "all" else active_persona

        from simulator.agents.timeline_agent import TimelineAgent

        timeline = TimelineAgent.generate(
            scenario=sim_scenario,
            persona_id=persona_id,
            conversation_history=data.get("conversation_history", []),
            citations=data.get("citations", [])
        )

        return jsonify({
            "success": True,
            "timeline": timeline
        })

    except Exception as e:
        print(f"[TIMELINE_AGENT] Error: {e}", file=sys.stderr)
        return jsonify({"success": False, "error": str(e), "timeline": []}), 500


@app.route("/api/agent/nextsteps", methods=["POST", "OPTIONS"])
def agent_nextsteps():
    """Generate next steps after a response."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        if not sim_engine or not sim_scenario:
            return jsonify({"success": False, "error": "Simulator not initialized"}), 500

        data = request.get_json(silent=True) or {}
        active_persona = session.get("persona_id", sim_persona or "all")
        persona_id = None if (active_persona or "").lower() == "all" else active_persona

        from simulator.agents.nextsteps_agent import NextStepsAgent

        nextsteps = NextStepsAgent.generate(
            scenario=sim_scenario,
            persona_id=persona_id,
            last_response=data.get("last_response"),
            conversation_history=data.get("conversation_history", [])
        )

        return jsonify({
            "success": True,
            "nextsteps": nextsteps
        })

    except Exception as e:
        print(f"[NEXTSTEPS_AGENT] Error: {e}", file=sys.stderr)
        return jsonify({"success": False, "error": str(e), "nextsteps": []}), 500


@app.route("/api/agent/progress-trend", methods=["POST", "OPTIONS"])
def agent_progress_trend():
    """Generate 7-day trend data for progress visualization."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        if not sim_engine or not sim_scenario:
            return jsonify({"success": False, "error": "Simulator not initialized", "trend": []}), 500

        # Calculate trend based on available data
        # For each of the last 7 days, count relevant items (emails, messages, etc.)
        from datetime import datetime, timedelta
        
        trend_data = []
        trend_values = []
        today = datetime.now()
        
        # Generate 7-day trend
        for day_offset in range(6, -1, -1):
            date = today - timedelta(days=day_offset)
            date_str = date.strftime('%Y-%m-%d')
            
            # Count items for this day from available data sources
            # This is a simulation - counting based on available data in scenario
            count = 0
            
            # Count emails, meetings, chats, and other items for this date
            try:
                emails = sim_engine.get_emails() or []
                count += len([e for e in emails if e.get('date', '').startswith(date_str)])
                
                meetings = sim_engine.get_meetings() or []
                count += len([m for m in meetings if m.get('date', '').startswith(date_str)])
                
                chats = sim_engine.get_chats() or []
                count += len([c for c in chats if c.get('date', '').startswith(date_str)])
            except:
                pass
            
            trend_values.append(max(count, 0))
            trend_data.append(date_str)
        
        # Determine trend direction
        if len(trend_values) >= 2:
            first_half_avg = sum(trend_values[:3]) / 3 if len(trend_values) >= 3 else trend_values[0]
            second_half_avg = sum(trend_values[-3:]) / 3 if len(trend_values) >= 3 else trend_values[-1]
            
            if second_half_avg > first_half_avg * 1.1:
                direction = 'improving'
                desc = '↑ Trending up - Improved activity'
            elif second_half_avg < first_half_avg * 0.9:
                direction = 'declining'
                desc = '↓ Trending down - Decreased activity'
            else:
                direction = 'stable'
                desc = '→ Stable - Consistent activity'
        else:
            direction = 'stable'
            desc = 'Insufficient data'
        
        return jsonify({
            "success": True,
            "trend": trend_values,
            "trendDirection": direction,
            "trendDescription": desc,
            "dates": trend_data
        })

    except Exception as e:
        print(f"[PROGRESS_TREND] Error: {e}", file=sys.stderr)
        return jsonify({
            "success": False,
            "error": str(e),
            "trend": [],
            "trendDirection": "stable",
            "trendDescription": "Error loading trend"
        }), 500


@app.route("/api/feature-acl", methods=["GET", "OPTIONS"])
def get_feature_acl():
    """Return feature access control list for current persona."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        from simulator.agents.acl_manager import FeatureACL

        active_persona = session.get("persona_id", sim_persona or "all")
        
        # Get all allowed features for this persona
        allowed_features = FeatureACL.get_allowed_features(active_persona)
        
        # Return as dictionary for easy lookup in frontend
        acl_dict = {feature: FeatureACL.can_access_feature(feature, active_persona) 
                    for feature in FeatureACL.FEATURE_ACCESS.keys()}

        return jsonify({
            "success": True,
            "persona_id": active_persona,
            "allowed_features": allowed_features,
            "acl": acl_dict
        })

    except Exception as e:
        print(f"[FEATURE_ACL] Error: {e}", file=sys.stderr)
        return jsonify({"success": False, "error": str(e), "acl": {}}), 500


@app.route("/api/agent/executive-brief", methods=["POST", "OPTIONS"])
def agent_executive_brief():
    """Generate decision-ready executive briefs with status, risks, blockers, and next actions."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        if not sim_engine or not sim_scenario:
            return jsonify({"success": False, "error": "Simulator not initialized", "brief": {}}), 500

        # Check if persona has access to this feature
        from simulator.agents.acl_manager import FeatureACL
        
        active_persona = session.get("persona_id", sim_persona or "all")
        if not FeatureACL.can_access_feature("executive_brief", active_persona):
            return jsonify({"success": False, "error": "Access denied - insufficient permissions", "brief": {}}), 403

        data = request.get_json(silent=True) or {}
        persona_id = None if (active_persona or "").lower() == "all" else active_persona

        from simulator.agents.executive_brief_agent import ExecutiveBriefAgent

        brief = ExecutiveBriefAgent.generate(
            scenario=sim_scenario,
            persona_id=persona_id,
            last_response=data.get("last_response"),
            conversation_history=data.get("conversation_history", [])
        )

        return jsonify({
            "success": True,
            "brief": brief
        })

    except Exception as e:
        print(f"[EXECUTIVE_BRIEF_AGENT] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "brief": {}}), 500


@app.route("/api/agent/action-recommendations", methods=["POST", "OPTIONS"])
def agent_action_recommendations():
    """Generate action recommendations with owners, due dates, and priorities."""
    try:
        if request.method == "OPTIONS":
            return ("", 204)

        if not sim_engine or not sim_scenario:
            return jsonify({"success": False, "error": "Simulator not initialized", "recommendations": {}}), 500

        # Check if persona has access to this feature
        from simulator.agents.acl_manager import FeatureACL
        
        active_persona = session.get("persona_id", sim_persona or "all")
        if not FeatureACL.can_access_feature("action_recommendations", active_persona):
            return jsonify({"success": False, "error": "Access denied - insufficient permissions", "recommendations": {}}), 403

        data = request.get_json(silent=True) or {}
        persona_id = None if (active_persona or "").lower() == "all" else active_persona

        from simulator.agents.action_recommendation_agent import ActionRecommendationAgent

        recommendations = ActionRecommendationAgent.generate(
            scenario=sim_scenario,
            persona_id=persona_id,
            last_response=data.get("last_response"),
            conversation_history=data.get("conversation_history", [])
        )

        return jsonify({
            "success": True,
            "recommendations": recommendations
        })

    except Exception as e:
        print(f"[ACTION_RECOMMENDATION_AGENT] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "recommendations": {}}), 500


@app.route("/api/agent/scenario-timeline", methods=["POST", "OPTIONS"])
def scenario_timeline():
    """Generate scenario-specific event timeline reconstruction."""
    if request.method == "OPTIONS":
        return "", 204
    
    try:
        from simulator.agents.scenario_timeline_agent import ScenarioTimelineAgent
        from simulator.agents.acl_manager import FeatureACL
        
        # Get active persona
        active_persona = session.get("persona_id", "all")
        
        # Check ACL
        if not FeatureACL.can_access_feature("scenario_timeline", active_persona):
            return jsonify({"success": False, "error": "Access restricted for your role"}), 403
        
        data = request.get_json() or {}
        
        timeline = ScenarioTimelineAgent.generate(
            scenario=sim_scenario,
            persona_id=active_persona,
            last_response=data.get("last_response"),
            conversation_history=data.get("conversation_history", [])
        )

        return jsonify({
            "success": True,
            "timeline": timeline
        })

    except Exception as e:
        print(f"[SCENARIO_TIMELINE_AGENT] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "timeline": {}}), 500


@app.route("/api/agent/whatif-simulation", methods=["POST", "OPTIONS"])
def whatif_simulation():
    """Generate what-if scenario simulations with impact assessment."""
    if request.method == "OPTIONS":
        return "", 204
    
    try:
        from simulator.agents.whatif_simulation_agent import WhatIfSimulationAgent
        from simulator.agents.acl_manager import FeatureACL
        
        # Get active persona
        active_persona = session.get("persona_id", "all")
        
        # Check ACL
        if not FeatureACL.can_access_feature("whatif_simulation", active_persona):
            return jsonify({"success": False, "error": "Access restricted for your role"}), 403
        
        data = request.get_json() or {}
        
        simulation = WhatIfSimulationAgent.generate(
            scenario=sim_scenario,
            persona_id=active_persona,
            last_response=data.get("last_response"),
            conversation_history=data.get("conversation_history", [])
        )

        return jsonify({
            "success": True,
            "simulation": simulation
        })

    except Exception as e:
        print(f"[WHATIF_SIMULATION_AGENT] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "simulation": {}}), 500


@app.route("/api/agent/pre-mortem-generator", methods=["POST", "OPTIONS"])
def pre_mortem_generator():
    """Generate pre-mortem analysis for active milestones with preventive actions."""
    if request.method == "OPTIONS":
        return "", 204

    try:
        from simulator.agents.premortem_generator_agent import PreMortemGeneratorAgent
        from simulator.agents.acl_manager import FeatureACL

        if not sim_scenario:
            return jsonify({"success": False, "error": "Simulator not initialized", "premortem": {}}), 500

        active_persona = session.get("persona_id", "all")

        if not FeatureACL.can_access_feature("premortem_generator", active_persona):
            return jsonify({"success": False, "error": "Access restricted for your role"}), 403

        data = request.get_json(silent=True) or {}

        premortem = PreMortemGeneratorAgent.generate(
            scenario=sim_scenario,
            persona_id=active_persona,
            last_response=data.get("last_response"),
            conversation_history=data.get("conversation_history", []),
        )

        return jsonify({
            "success": True,
            "premortem": premortem,
        })

    except Exception as e:
        print(f"[PREMORTEM_GENERATOR_AGENT] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "premortem": {}}), 500


@app.route("/api/agent/progress-tracking", methods=["POST", "OPTIONS"])
def progress_tracking():
    """Generate progress tracking metrics with 7-day trend."""
    if request.method == "OPTIONS":
        return "", 204
    
    try:
        from simulator.agents.progress_tracking_agent import ProgressTrackingAgent
        from simulator.agents.acl_manager import FeatureACL
        
        # Get active persona
        active_persona = session.get("persona_id", "all")
        
        # Check ACL
        if not FeatureACL.can_access_feature("progress_tracking", active_persona):
            return jsonify({"success": False, "error": "Access restricted for your role"}), 403
        
        data = request.get_json() or {}
        
        progress = ProgressTrackingAgent.generate(
            scenario=sim_scenario,
            persona_id=active_persona,
            last_response=data.get("last_response"),
            conversation_history=data.get("conversation_history", [])
        )

        return jsonify({
            "success": True,
            "progress": progress
        })

    except Exception as e:
        print(f"[PROGRESS_TRACKING_AGENT] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "progress": {}}), 500


@app.route("/api/agent/interactive-dashboard", methods=["POST", "OPTIONS"])
def interactive_dashboard():
    """Generate interactive dashboard with aggregated metrics."""
    if request.method == "OPTIONS":
        return "", 204
    
    try:
        from simulator.agents.interactive_dashboard_agent import InteractiveDashboardAgent
        from simulator.agents.acl_manager import FeatureACL
        
        # Get active persona
        active_persona = session.get("persona_id", "all")
        
        # Check ACL
        if not FeatureACL.can_access_feature("interactive_dashboard", active_persona):
            return jsonify({"success": False, "error": "Access restricted for your role"}), 403
        
        data = request.get_json() or {}
        
        dashboard = InteractiveDashboardAgent.generate(
            scenario=sim_scenario,
            persona_id=active_persona,
            last_response=data.get("last_response"),
            conversation_history=data.get("conversation_history", [])
        )

        return jsonify({
            "success": True,
            "dashboard": dashboard
        })

    except Exception as e:
        print(f"[INTERACTIVE_DASHBOARD_AGENT] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "dashboard": {}}), 500


def main():
    """Main entry point."""
    print("[*] Initializing Work IQ Agent Web UI...")

    port = int(os.getenv("WORKIQ_PORT", "5000"))

    if not init_agent():
        print("\n[ERROR] Failed to initialize agent. Please check your configuration.", file=sys.stderr)
        print("\nRequired environment variables:")
        print("  - For full agent+MCP mode: WORKIQ_AZURE_ENDPOINT, WORKIQ_MCP_COMMAND, WORKIQ_MCP_ARGS")
        print("  - For simulator-only mode: WORKIQ_SIM_SCENARIO (optional), WORKIQ_SIM_PERSONA (optional)")
        sys.exit(1)

    print("[OK] Agent initialized!")
    print("\n[SERVER] Starting Web Server...")
    print(f"   Open your browser and go to: http://localhost:{port}")
    print("   Press CTRL+C to stop the server\n")

    # Run the Flask app
    app.run(
        host="127.0.0.1",
        port=port,
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":
    main()
