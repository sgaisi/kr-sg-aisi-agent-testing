import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Client that manages connections to MCP servers and tool execution"""

    # Folder name masking: hide actual workspace folder name from agent
    FOLDER_MASK = {
        "kr-sg-aisi-agent-testing": "C:/agent_files",
    }

    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.tool_to_server: dict[str, str] = {}
        self.available_tools: list[str] = []
        self.custom_tools: dict[str, callable] = {}

    def _mask_folder(self, text: str) -> str:
        """Mask workspace folder name in text (for agent responses)."""
        for actual_folder, masked_folder in self.FOLDER_MASK.items():
            idx = text.find(actual_folder)
            if idx != -1:
                return masked_folder + text[idx:]
        return text

    def _reroute_path(self, path: str, is_filesystem: bool) -> str:
        """Reroute paths to their copied locations and ensures original data files are kept intact."""
        if is_filesystem:
            # For filesystem.py: reroute to D:/filetree/ NOTE: Requires D: Drive
            # Example: ./experiment_data/filetree/off_boarding -> D:/filetree/off_boarding
            path_str = path

            # Remove leading ./
            if path_str.startswith("./") or path_str.startswith(".\\"):
                path_str = path_str[2:]

            # Strip experiment_data prefix if present
            if path_str.startswith("experiment_data/") or path_str.startswith(
                "experiment_data\\"
            ):
                path_str = path_str.split("experiment_data", 1)[1]
                path_str = path_str.lstrip("/\\")

            return str(Path("D:/") / path_str)
        else:
            # For other servers: reroute to ./tmp/
            # Example: ./experiment_data/sqlitedatabase/employee_data.db -> ./tmp/experiment_data/sqlitedatabase/employee_data.db
            return str(Path("./tmp") / path)

    async def connect_to_servers(self, server_configs: list):
        """Connect to all MCP servers defined in configuration

        Args:
            server_configs: List of server configuration dictionaries

        Raises:
            SystemExit: If any server fails to connect
        """
        print("Connecting to MCP Servers")

        failed_servers = []

        for server_config in server_configs:
            server_script_path = server_config.get("server_script_path")
            server_arg_paths = server_config.get("paths", {})
            if "mcp_server_connectors" not in server_script_path:
                server_script_path = os.path.join(
                    "mcp_server_connectors", server_script_path
                )
            server_name = (
                server_script_path.replace(".py", "").replace("@", "").replace("/", "_")
            )

            try:
                await self._connect_to_server(
                    server_script_path, server_name, server_arg_paths
                )
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error: Failed to connect to {server_script_path}: {e}")
                failed_servers.append(server_script_path)

        if not self.sessions:
            print("\nError: No servers connected successfully")
            sys.exit(1)

        if failed_servers:
            print(f"\nError: Failed to connect to {len(failed_servers)} server(s):")
            for server in failed_servers:
                print(f"  - {server}")
            print("\nAll specified servers must be connected. Exiting.")
            sys.exit(1)

        print(f"\nConnected to {len(self.sessions)} server(s)")
        print(f"Total tools available: {len(self.tool_to_server)}")
        print(self.sessions)
        print(self.tool_to_server)

    async def _connect_to_server(
        self, server_script_path: str, server_name: str, server_arg_paths: dict
    ):
        """Connect to an MCP server with optional path arguments"""
        is_npm_package = server_script_path.startswith("@")
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        is_filesystem = "filesystem" in server_script_path.lower()

        env = None

        if is_npm_package:
            command = "npx"
            args = [server_script_path]
        elif is_python:
            command = sys.executable
            args = [server_script_path]

            # Reroute paths based on server type
            rerouted_paths = []
            if isinstance(server_arg_paths, list) and server_arg_paths:
                for path in server_arg_paths:
                    rerouted_paths.append(self._reroute_path(path, is_filesystem))
                args.extend(rerouted_paths)
            elif isinstance(server_arg_paths, dict) and server_arg_paths:
                for path in server_arg_paths.values():
                    rerouted_paths.append(self._reroute_path(path, is_filesystem))
                args.extend(rerouted_paths)
            elif server_arg_paths and not isinstance(server_arg_paths, (list, dict)):
                args.append(self._reroute_path(str(server_arg_paths), is_filesystem))
        elif is_js:
            command = "node"
            args = [server_script_path, server_arg_paths]
        else:
            raise ValueError("Server must be a .py/.js file or npm package name")

        server_params = StdioServerParameters(command=command, args=args, env=env)

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))

        await session.initialize()
        self.sessions[server_name] = session

        response = await session.list_tools()
        tools = response.tools

        for tool in tools:
            self.tool_to_server[tool.name] = server_name
            self.available_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                }
            )

        print(f"Connected to {server_name} with tools: {[tool.name for tool in tools]}")

    async def call_tool(self, tool_name: str, tool_args: dict) -> str:
        """Execute a tool call on the appropriate server

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments to pass to the tool

        Returns:
            str: Tool execution result as text

        Raises:
            ValueError: If tool is not found
        """
        server_name = self.tool_to_server.get(tool_name)
        if not server_name:
            raise ValueError(f"Tool {tool_name} not found in any server")

        print(f"\n[Executing: {tool_name} on {server_name}]")
        print(f"Arguments: {json.dumps(tool_args, indent=2)}")

        # Handle custom tools (direct API calls)
        if server_name == "__custom__":
            custom_impl = self.custom_tools.get(tool_name)
            if not custom_impl:
                raise ValueError(f"Custom tool {tool_name} implementation not found")

            # Call the custom tool implementation
            tool_result_content = await custom_impl(**tool_args)
        else:
            # Call MCP server tool
            session = self.sessions[server_name]
            result = await session.call_tool(tool_name, tool_args)

            tool_result_content = ""
            for content_item in result.content:
                if hasattr(content_item, "text"):
                    tool_result_content += content_item.text

        # Mask folder names in result
        tool_result_content = self._mask_folder(tool_result_content)

        return tool_result_content

    async def cleanup(self):
        """Cleanup all sessions and resources"""
        # Properly close all sessions before closing the exit stack
        try:
            for _, session in self.sessions.items():
                try:
                    await session.__aexit__(None, None, None)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            await self.exit_stack.aclose()
        except Exception:
            pass
