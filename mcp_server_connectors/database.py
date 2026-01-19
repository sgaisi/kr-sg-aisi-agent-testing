"""
Wrapper script for mcp-server-sqlite MCP server.
This starts a SQLite database server with a specified database file.
Uses the official Python-based SQLite MCP server via uvx.
"""

import sys
import os


def main():
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = os.path.join(
            os.getcwd(), "experiment_data", "sqlitedatabase", "employee_data.db"
        )

    db_path = os.path.abspath(db_path)

    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    print(f"Starting SQLite MCP server with database: {db_path}", file=sys.stderr)

    cmd = ["uvx", "mcp-server-sqlite", "--db-path", db_path]

    try:
        os.execvp("uvx", cmd)
    except Exception as e:
        print(f"Error running SQLite MCP server: {e}", file=sys.stderr)
        print("Make sure 'uv' is installed: pip install uv", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
