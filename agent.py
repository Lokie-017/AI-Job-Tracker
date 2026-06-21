import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

try:
    from ollama import Client
    OLLAMA_AVAILABLE = True
except Exception:
    Client = None
    OLLAMA_AVAILABLE = False

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EXIT_COMMANDS = {"quit", "exit", "q", "bye"}
MAX_TOOL_RETRIES = int(os.getenv("MAX_TOOL_RETRIES", "3"))
RETRY_SLEEP_SECONDS = float(os.getenv("RETRY_SLEEP_SECONDS", "2.0"))
PROJECT_ROOT = Path(__file__).resolve().parent
SERVER_SCRIPT = PROJECT_ROOT / "server.py"
PYTHON_EXECUTABLE = sys.executable

TOOL_SCHEMAS = {
    "hello": {
        "summary": "Say hello to someone.",
        "schema": {"name": "string"},
    },
    "add_application": {
        "summary": "Add a job application.",
        "schema": {"company": "string", "role": "string"},
    },
    "list_applications": {
        "summary": "List all job applications.",
        "schema": {},
    },
    "update_status": {
        "summary": "Update the status of a job application.",
        "schema": {"application_id": "integer", "status": "string"},
    },
    "application_summary": {
        "summary": "Get application statistics.",
        "schema": {},
    },
    "pending_followups": {
        "summary": "Find applications needing follow-up.",
        "schema": {"days_threshold": "integer"},
    },
    "get_application_by_company": {
        "summary": "Get all applications for a specific company.",
        "schema": {"company": "string"},
    },
    "delete_application": {
        "summary": "Delete a job application by ID.",
        "schema": {"id": "integer"},
    },
    "search_applications": {
        "summary": "Search applications by status.",
        "schema": {"status": "string"},
    },
}


def build_tool_planner_prompt(
    tool_specs: Sequence[Tuple[str, str]],
    user_request: str,
    observation: str | None = None,
) -> str:
    tool_list = "\n".join(
        f"- {name}: {description}" if description else f"- {name}"
        for name, description in tool_specs
    )

    schema_lines = []
    for tool_name, spec in TOOL_SCHEMAS.items():
        if spec["schema"]:
            schema_lines.append(
                f"- {tool_name}: {json.dumps(spec['schema'])}"
            )
        else:
            schema_lines.append(f"- {tool_name}: {{}}")

    schema_block = "\n".join(schema_lines)

    observation_block = ""
    if observation:
        observation_block = f"""
Previous observation:
{observation}

Think again and update the plan based on the failure above.
"""

    return f"""
You are an internal agent that chooses and executes MCP tools to satisfy the user's request.

Available tools:
{tool_list}

Tool schemas:
{schema_block}

User request:
{user_request}

{observation_block}

Return ONLY valid JSON with the following shape:
{{
  "steps": [
    {{
      "thought": "<your reasoning>",
      "tool": "<tool_name>",
      "arguments": {{ ... }}
    }}
  ]
}}

If no tool call is needed, return:
{{"steps": []}}

Use exact argument names from the schema. Do not invent new argument names.
Do not use placeholder variables such as `{{response.id}}`.
If you need results from a previous tool to call another tool, use the helper tool first and then call the second tool with the actual returned value.
"""


def safe_json_dumps(value: Any, **kwargs: Any) -> str:
    return json.dumps(value, default=str, ensure_ascii=False, **kwargs)


def format_tool_output(result: Any) -> str:
    if result is None:
        return ""
    if isinstance(result, (dict, list)):
        return safe_json_dumps(result, indent=2)
    if hasattr(result, "content"):
        content = result.content
        if isinstance(content, (dict, list)):
            return safe_json_dumps(content, indent=2)
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, (tuple, set)):
            return safe_json_dumps(list(content), indent=2)
        return str(content).strip()
    if isinstance(result, str):
        return result.strip()
    return str(result)


def extract_json(raw_text: str) -> str:
    raw_text = raw_text.strip()

    # Remove markdown code fences if present
    fence_match = re.search(r"^```(?:json)?\s*(.*)\s*```$", raw_text, re.S)
    if fence_match:
        return fence_match.group(1).strip()

    # If the response is plain text with JSON inside, try to find the first JSON object
    brace_match = re.search(r"\{.*\}", raw_text, re.S)
    if brace_match:
        return brace_match.group(0).strip()

    return raw_text


def parse_tool_plan(raw_response: str) -> List[Dict[str, Any]]:
    cleaned_response = extract_json(raw_response)
    plan = json.loads(cleaned_response)

    if not isinstance(plan, dict) or "steps" not in plan:
        raise ValueError("Tool plan must be a JSON object with a 'steps' field.")

    steps = plan["steps"]
    if not isinstance(steps, list):
        raise ValueError("'steps' must be a list.")

    result: List[Dict[str, Any]] = []
    for item in steps:
        if not isinstance(item, dict) or "tool" not in item:
            raise ValueError("Each step must be an object with a 'tool' key.")

        tool_name = item["tool"]
        if not isinstance(tool_name, str) or not tool_name:
            raise ValueError("Tool name must be a non-empty string.")

        arguments = item.get("arguments", {})
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a JSON object.")

        if has_placeholder(arguments):
            raise ValueError(
                "Placeholder values are not allowed in tool arguments. "
                "Return actual argument values or plan one helper step at a time."
            )

        valid, validation_message = validate_tool_arguments(tool_name, arguments)
        if not valid:
            raise ValueError(validation_message)

        thought = item.get("thought", "")
        if thought is None:
            thought = ""

        result.append({
            "tool": tool_name,
            "arguments": arguments,
            "thought": thought,
        })

    return result


def has_placeholder(value: Any) -> bool:
    if isinstance(value, str) and value.strip().startswith("{{") and value.strip().endswith("}}"):  # noqa: E712
        return True
    if isinstance(value, dict):
        return any(has_placeholder(v) for v in value.values())
    if isinstance(value, list):
        return any(has_placeholder(v) for v in value)
    return False


def resolve_placeholder(value: str, previous_results: Dict[str, Any]) -> Any:
    placeholder = value.strip()[2:-2].strip()

    def get_field_from_data(data: Any, field: str) -> Any:
        if isinstance(data, dict) and field in data:
            return data[field]
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and field in item:
                    return item[field]
        return None

    # response.id or response.application_id
    if placeholder.startswith("response."):
        field = placeholder.split(".", 1)[1]
        last_key = next(reversed(previous_results), None)
        if last_key is None:
            raise ValueError("No previous tool result available for placeholder resolution.")
        last_result = previous_results[last_key]
        value = get_field_from_data(last_result, field)
        if value is not None:
            return value
        raise ValueError(f"Cannot resolve placeholder {value} from last tool result.")

    # toolName['id'] or toolName["id"]
    match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[['\"]([^'\"]+)['\"]\]$", placeholder)
    if match:
        tool_name, field = match.groups()
        if tool_name not in previous_results:
            raise ValueError(f"No previous result found for tool {tool_name}.")
        prior = previous_results[tool_name]
        value = get_field_from_data(prior, field)
        if value is not None:
            return value
        raise ValueError(f"Cannot resolve placeholder {value} from tool {tool_name}.")

    raise ValueError(f"Unsupported placeholder: {value}")


def resolve_arguments(arguments: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
    resolved = {}
    for key, value in arguments.items():
        if isinstance(value, str) and has_placeholder(value):
            resolved[key] = resolve_placeholder(value, previous_results)
        elif isinstance(value, dict):
            resolved[key] = resolve_arguments(value, previous_results)
        elif isinstance(value, list):
            resolved[key] = [resolve_arguments(v, previous_results) if isinstance(v, dict) else v for v in value]
        else:
            resolved[key] = value
    return resolved


def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
    if tool_name not in TOOL_SCHEMAS:
        return False, f"Unknown tool: {tool_name}."

    expected_schema = TOOL_SCHEMAS[tool_name]["schema"]
    expected_keys = set(expected_schema.keys())
    actual_keys = set(arguments.keys())

    missing_keys = expected_keys - actual_keys
    extra_keys = actual_keys - expected_keys

    if missing_keys or extra_keys:
        messages = []
        if missing_keys:
            messages.append(f"Missing required keys: {sorted(list(missing_keys))}.")
        if extra_keys:
            messages.append(f"Unexpected keys: {sorted(list(extra_keys))}. Expected exact keys: {sorted(list(expected_keys))}.")
        if missing_keys and extra_keys:
            error_text = f"Invalid arguments for {tool_name}: { ' '.join(messages) }"
        else:
            error_text = f"Invalid arguments for {tool_name}: { ' '.join(messages) }"
        return False, error_text

    return True, ""


def build_final_answer_prompt(user_request: str, tool_results: List[Dict[str, Any]]) -> str:
    return f"""
User request:
{user_request}

Tool results:
{json.dumps(tool_results, indent=2)}

Create a helpful answer based only on the tool results.
If the results are empty, say you were unable to gather any information.
"""


async def call_ollama(loop: asyncio.AbstractEventLoop, ollama: Any, prompt: str) -> str:
    def sync_call():
        return ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )

    response = await loop.run_in_executor(None, sync_call)
    if isinstance(response, dict):
        message = response.get("message") or response.get("choices") or {}
        if isinstance(message, dict):
            content = message.get("content") or message.get("text")
        elif isinstance(message, list) and len(message) > 0:
            content = message[0].get("content") or message[0].get("text")
        else:
            content = None
    else:
        content = getattr(response, "content", None)
    return content.strip() if isinstance(content, str) else ""


async def execute_tools(
    session: Any,
    tool_plan: List[Dict[str, Any]],
    previous_results: Dict[str, Any],
) -> List[Dict[str, Any]]:
    all_results: List[Dict[str, Any]] = []

    for tool_item in tool_plan:
        tool_name = tool_item["tool"]
        arguments = tool_item.get("arguments", {})
        thought = tool_item.get("thought", "")

        try:
            resolved_arguments = resolve_arguments(arguments, previous_results)
        except ValueError as exc:
            tool_output = f"Error resolving arguments for {tool_name}: {exc}"
            print(f"\nThought: {thought}")
            print(f"{tool_output}\n")
            all_results.append({"tool": tool_name, "arguments": arguments, "output": tool_output})
            continue

        valid, validation_message = validate_tool_arguments(tool_name, resolved_arguments)
        if not valid:
            tool_output = validation_message
            print(f"\nThought: {thought}")
            print(f"{tool_output}\n")
            all_results.append({"tool": tool_name, "arguments": resolved_arguments, "output": tool_output})
            continue

        print(f"\nThought: {thought}")
        print(f"Running tool: {tool_name} with arguments: {json.dumps(resolved_arguments)}")

        try:
            result = await session.call_tool(tool_name, resolved_arguments)
            tool_output = format_tool_output(result)
            previous_results[tool_name] = result.content if hasattr(result, "content") else result
        except Exception as exc:
            tool_output = f"Error executing tool {tool_name}: {exc}"
            print(tool_output)

        print(f"Result from {tool_name}:\n{tool_output}\n")
        all_results.append({"tool": tool_name, "arguments": resolved_arguments, "output": tool_output})

    return all_results


async def run_agent():
    if not OLLAMA_AVAILABLE:
        print("Error: ollama package is not installed or could not be imported.")
        return

    server_params = StdioServerParameters(
        command=PYTHON_EXECUTABLE,
        args=[str(SERVER_SCRIPT)],
    )

    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]

            print("\nMCP Tools Found:")
            for name in tool_names:
                print(f"- {name}")

            ollama = Client(host=OLLAMA_HOST)
            loop = asyncio.get_running_loop()

            while True:
                user_request = await loop.run_in_executor(None, input, "\nYou: ")
                if user_request is None:
                    break

                user_request = user_request.strip()
                if not user_request:
                    continue

                if user_request.lower() in EXIT_COMMANDS:
                    print("Goodbye.")
                    break

                print("\nPlanning tool usage...")
                observation = None
                tool_plan = []
                attempt = 0

                previous_results: Dict[str, Any] = {}
                while attempt < MAX_TOOL_RETRIES:
                    attempt += 1
                    print(f"\nAgent planning attempt {attempt}...")

                    prompt = build_tool_planner_prompt(
                        [(name, TOOL_SCHEMAS[name]["summary"]) for name in tool_names],
                        user_request,
                        observation,
                    )

                    try:
                        raw_response = await call_ollama(loop, ollama, prompt)
                        print("\nPlanner response:")
                        print(raw_response)
                    except Exception as exc:
                        print(f"Error calling Ollama: {exc}")
                        break

                    try:
                        tool_plan = parse_tool_plan(raw_response)
                    except Exception as exc:
                        print(f"Failed to parse tool plan: {exc}")
                        break

                    if not tool_plan:
                        print("No tool steps requested. Skipping tool execution.")
                        break

                    all_results = await execute_tools(session, tool_plan, previous_results)

                    failed_outputs = [
                        result["output"]
                        for result in all_results
                        if result["output"].lower().startswith("error")
                    ]

                    if not failed_outputs:
                        break

                    observation = "\n".join(failed_outputs)
                    print(f"\nObservation:\n{observation}")
                    print("Retrying with updated reasoning...")
                    await asyncio.sleep(RETRY_SLEEP_SECONDS)

                final_prompt = build_final_answer_prompt(user_request, all_results)
                print("\nComposing final answer...")

                try:
                    final_response = await call_ollama(loop, ollama, final_prompt)
                    print("\nAssistant:")
                    print(final_response)
                except Exception as exc:
                    print(f"Error composing final answer: {exc}")


if __name__ == "__main__":
    asyncio.run(run_agent())