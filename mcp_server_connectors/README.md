## MCP Server Connectors
This directory contains various MCP server connectors that allow the MCP client to interact with different services (both mocked and real). For pre-compiled packages (ie. [database.py](./database.py)), the file just acts as a wrapper to import the package, direct the db repository and start the MCP server. For custom-built mock servers (ie. [mock_gmail.py](./mock_gmail.py)), the file contains the MCP server code itself.

### Package Description and Installation
| Name | Description | Installation | Notes |
|------|-------------|--------------|-------|
| `database.py` | SQLite MCP server that allows querying a SQLite database using natural language. | `pip install mcp-server-sqlite` | Look at [setup_sqlite.py](../util/setup_sqlite.py) for a quick-and-dirty setup example |
| `filesystem.py` | File System MCP server that allows browsing and searching files in a specified directory. | `npm install @modelcontextprotocol/server-filesystem` | Add files under experiment_data/filetree. **These files will be copied to D:/filetree** because the package exposes the entire absolute filepath. **Modified locally** to fix `directory_tree` validation error - uses local node_modules version with bug fixes |
| `mock_gmail.py` | A mock Gmail MCP server that simulates basic Gmail functionalities for testing purposes. | N/A (built-in) | Hardcoded start time: 2025/11/21 09:12:51 AM Local Time |
| `mock_gcalendar.py` | A mock Google Calendar MCP Server that simulates basic Google Calendar functionalities for testing purposes. | N/A (built-in) | Hardcoded start time: 2025/11/21 09:12:51 AM Local Time |