import json
from typing import Any, Dict, List


class OllamaClient:
    """Simple Ollama planning mock.

    Replace with real Ollama calls (e.g., ollama.Client) in production.
    """

    def __init__(self, host: str | None = None):
        self.host = host

    def plan(self, user_request: str) -> List[Dict[str, Any]]:
        """Return a list of tool steps for the given user request.

        For the prototype we recognise a few patterns; otherwise return empty.
        """
        text = user_request.lower()
        steps: List[Dict[str, Any]] = []
        if "delete" in text and "openai" in text:
            steps = [
                {"tool": "get_application_by_company", "arguments": {"company": "OpenAI"}, "thought": "Find application ID for OpenAI."},
                {"tool": "delete_application", "arguments": {"id": 8}, "thought": "Delete the found application."},
            ]
        elif "list" in text and "applications" in text:
            steps = [{"tool": "list_applications", "arguments": {}, "thought": "List all applications."}]

        return steps
