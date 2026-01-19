import json
import sys
import os
import shutil
from pathlib import Path


def copy_scenario_files(scenario_path: str):
    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    print(f"Processing scenario: {scenario.get('id', 'unknown')}")
    print(f"Description: {scenario.get('description', 'N/A')}\n")

    mcp_servers = scenario.get("mcp_servers", [])

    for server in mcp_servers:
        server_script = server.get("server_script_path", "")
        paths = server.get("paths", [])

        is_filesystem = "filesystem" in server_script.lower()

        for path in paths:
            source_path = Path(path)

            if is_filesystem:
                # For filesystem.py: copy to D:/filetree/ and strip experiment_data
                # Example: ./experiment_data/filetree/off_boarding -> D:/filetree/off_boarding
                path_str = str(source_path)

                if path_str.startswith("./") or path_str.startswith(".\\"):
                    path_str = path_str[2:]

                if path_str.startswith("experiment_data/") or path_str.startswith(
                    "experiment_data\\"
                ):
                    path_str = path_str.split("experiment_data", 1)[1]
                    path_str = path_str.lstrip("/\\")

                dest_path = Path("D:/") / path_str

            else:
                # For other servers: copy to ./tmp/ preserving structure
                # Example: ./experiment_data/sqlitedatabase/employee_data.db -> ./tmp/experiment_data/sqlitedatabase/employee_data.db
                dest_path = Path("./tmp") / source_path

            if source_path.exists():
                if source_path.is_file():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    print(f"Copied: {source_path} -> {dest_path}")
                elif source_path.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                    print(f"Copied directory: {source_path} -> {dest_path}")
            else:
                print(f"Warning: Source path does not exist: {source_path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python copy_scenario_files.py <scenario_file>")
        sys.exit(1)

    scenario_path = sys.argv[1]

    if not os.path.exists(scenario_path):
        print(f"Error: Scenario file '{scenario_path}' not found.")
        sys.exit(1)

    copy_scenario_files(scenario_path)


if __name__ == "__main__":
    main()
