import asyncio
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters

PROJECT_ROOT = Path(__file__).resolve().parent
SERVER_SCRIPT = PROJECT_ROOT / "server.py"
PYTHON_EXECUTABLE = sys.executable


async def main():
    server_params = StdioServerParameters(
        command=PYTHON_EXECUTABLE,
        args=[str(SERVER_SCRIPT)],
    )

    async with stdio_client(server_params) as streams:
        async with ClientSession(
            streams[0],
            streams[1]
        ) as session:

            await session.initialize()

            tools = await session.list_tools()

            print("\nTOOLS FOUND:\n")

            for tool in tools.tools:
                print(tool.name)


if __name__ == "__main__":
    asyncio.run(main())