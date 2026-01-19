import json
import sys
import os
import shutil
from pathlib import Path


def remove_scenario_files(scenario_path: str):
    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    print(f"Removing files for scenario: {scenario.get('id', 'unknown')}")
    print(f"Description: {scenario.get('description', 'N/A')}\n")

    mcp_servers = scenario.get("mcp_servers", [])

    for server in mcp_servers:
        server_script = server.get("server_script_path", "")
        paths = server.get("paths", [])

        is_filesystem = "filesystem" in server_script.lower()

        for path in paths:
            source_path = Path(path)

            if is_filesystem:
                # For filesystem.py: remove from D:/filetree/
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
                # For other servers: remove from ./tmp/
                dest_path = Path("./tmp") / source_path

            if dest_path.exists():
                if dest_path.is_file():
                    dest_path.unlink()
                    print(f"Removed file: {dest_path}")
                elif dest_path.is_dir():
                    shutil.rmtree(dest_path)
                    print(f"Removed directory: {dest_path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python remove_scenario_files.py <scenario_file>")
        sys.exit(1)

    scenario_path = sys.argv[1]

    if not os.path.exists(scenario_path):
        print(f"Error: Scenario file '{scenario_path}' not found.")
        sys.exit(1)

    remove_scenario_files(scenario_path)
    print("\nScenario files removed successfully!")


if __name__ == "__main__":
    main()
