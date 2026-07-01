"""
Web UI for the Work IQ A2A Agent using Flask.
Provides a browser-based chat interface using A2A transport.
"""
import os
import asyncio
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework_a2a import A2AAgent

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-change-in-production")

# Global agent instance
agent = None
a2a_tool = None

def _get_required_env(name: str) -> str:
    """Return a required env var value or raise a helpful error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

def init_agent():
    """Initialize the agent on app startup."""
    global agent, a2a_tool
    try:
        # Setup Azure OpenAI client
        endpoint = _get_required_env("WORKIQ_AZURE_ENDPOINT")
        model = os.getenv("WORKIQ_MODEL", "gpt-5-mini")
        api_version = os.getenv("WORKIQ_AZURE_API_VERSION", "2024-08-01-preview")

        client = OpenAIChatCompletionClient(
            model=model,
            credential=DefaultAzureCredential(),
            azure_endpoint=endpoint,
            api_version=api_version,
        )

        # Setup A2A tool — connects to the running a2a_server.py
        a2a_url = os.getenv("WORKIQ_A2A_URL", "http://127.0.0.1:8920")
        a2a_agent = A2AAgent(url=a2a_url)
        a2a_tool = a2a_agent.as_tool(
            name="workiq-ask",
            description="Ask Work IQ a question about the Atlas payments incident. Returns a cited answer grounded in work context.",
        )

        # Create agent
        agent = Agent(
            client=client,
            name="AtlasIncidentAgent",
            instructions="""You are an on-call shift handover assistant for the Atlas payments Sev-1 incident.
Use the workiq-ask tool to retrieve incident context: bridge-call decisions, root cause,
mitigations, open actions, and customer-communications commitments.
Always include the citations returned by Work IQ in your response. Label the citations section as "Citations: " and list each citation on a new line in the format [CITATION-ID]: "Citation text".""",
            tools=[a2a_tool],
        )

        return True
    except Exception as e:
        print(f"Failed to initialize agent: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


@app.before_request
def before_request():
    """Initialize session if needed."""
    if "conversation_id" not in session:
        session["conversation_id"] = str(datetime.now().timestamp())


@app.route("/")
def index():
    """Serve the main chat interface."""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages via API."""
    try:
        data = request.json
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        if not agent or not a2a_tool:
            return jsonify({"error": "Agent not initialized"}), 500

        # Run the async agent call from the sync Flask handler
        async def run_agent():
            response = await agent.run(user_message)
            return response

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response = loop.run_until_complete(run_agent())

        # Extract the actual response text from AgentResponse object
        response_text = str(response) if response else ""

        return jsonify({
            "success": True,
            "response": response_text,
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


@app.route("/api/clear", methods=["POST"])
def clear_history():
    """Clear the conversation history."""
    try:
        return jsonify({"success": True, "message": "Ready for new conversation"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/status", methods=["GET"])
def status():
    """Get agent status."""
    if agent and a2a_tool:
        configured_endpoint = os.getenv("WORKIQ_AZURE_ENDPOINT", "")
        configured_model = os.getenv("WORKIQ_MODEL", "gpt-5-mini")
        a2a_url = os.getenv("WORKIQ_A2A_URL", "http://127.0.0.1:8920")

        return jsonify({
            "status": "ready",
            "model": configured_model,
            "endpoint": configured_endpoint,
            "a2a_server": a2a_url,
            "transport": "A2A"
        })
    else:
        return jsonify({
            "status": "not_initialized",
            "error": "Agent not initialized"
        }), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


def main():
    """Main entry point."""
    print("⏳ Initializing Work IQ A2A Agent Web UI...")

    port = int(os.getenv("WORKIQ_A2A_PORT", "5001"))

    if not init_agent():
        print("\n❌ Failed to initialize agent. Please check your configuration.", file=sys.stderr)
        print("\nRequired environment variables:")
        print("  - WORKIQ_AZURE_ENDPOINT")
        print("\nOptional (with defaults):")
        print("  - WORKIQ_MODEL (default: gpt-5-mini)")
        print("  - WORKIQ_A2A_URL (default: http://127.0.0.1:8920)")
        print("\nMake sure the A2A server is running:")
        print("  ..\\.venv\\Scripts\\python.exe simulator\\a2a_server.py")
        sys.exit(1)

    print(" Agent initialized!")
    print("\nStarting Web Server...")
    print(f" Open your browser and go to: http://localhost:{port}")
    print("  Press CTRL+C to stop the server\n")

    # Run the Flask app
    app.run(
        host="127.0.0.1",
        port=port,
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":
    main()