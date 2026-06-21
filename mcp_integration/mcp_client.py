import time
from typing import Any, Dict


class MCPClient:
    """Lightweight MCP client wrapper with simple mocked tool behavior.

    If an actual MCP session/wrapper is available in the environment, replace
    the internals to call real tools. This implementation provides deterministic
    demo outputs for the Streamlit prototype.
    """

    def __init__(self):
        pass

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate network/tool latency
        time.sleep(0.4)

        if tool_name == "get_application_by_company":
            company = arguments.get("company")
            # return a fake application list
            return {"applications": [{"id": 8, "company": company, "role": "Engineer"}]}

        if tool_name == "delete_application":
            app_id = arguments.get("id") or arguments.get("application_id")
            return {"deleted": True, "id": app_id}

        if tool_name == "list_applications":
            return {"applications": [{"id": 1, "company": "OpenAI"}, {"id": 2, "company": "Vercel"}]}

        # generic echo
        return {"result": {"tool": tool_name, "args": arguments}}
