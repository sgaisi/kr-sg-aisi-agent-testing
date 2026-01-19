import json
import sys
import os
import glob

from setup_filesystem import setup_filesystem_from_scenario
from setup_sqlite import setup_database_from_scenario
from setup_gmail import setup_mock_gmail_from_scenario
from setup_gcal import setup_mock_gcal_from_scenario


def setup_scenario(scenario_file):
    """Set up all experiment data for a single scenario file."""
    print(f"Setting up scenario: {scenario_file}")

    try:
        with open(scenario_file, "r", encoding="utf-8") as f:
            scenario = json.load(f)
    except Exception as e:
        print(f"Error loading scenario file: {e}")
        return False

    servers_found = []

    for server in scenario.get("mcp_servers", []):
        script_path = server.get("server_script_path", "")
        servers_found.append(script_path)

    if "filesystem.py" in servers_found:
        print("\n--- Setting up Filesystem ---")
        try:
            setup_filesystem_from_scenario(scenario_file)
        except Exception as e:
            print(f"Error setting up filesystem: {e}")

    if "database.py" in servers_found:
        print("\n--- Setting up SQLite Database ---")
        try:
            setup_database_from_scenario(scenario_file)
        except Exception as e:
            print(f"Error setting up database: {e}")

    if "mock_gmail.py" in servers_found:
        print("\n--- Setting up Mock Gmail ---")
        try:
            setup_mock_gmail_from_scenario(scenario_file)
        except Exception as e:
            print(f"Error setting up mock gmail: {e}")

    if "mock_gcalendar.py" in servers_found:
        print("\n--- Setting up Mock Google Calendar ---")
        try:
            setup_mock_gcal_from_scenario(scenario_file)
        except Exception as e:
            print(f"Error setting up mock gcal: {e}")

    print(f"\nCompleted setup for: {scenario_file}")
    return True


def setup_all_scenarios(scenarios_dir="scenarios"):
    """Set up all experiment data for all scenario files in the directory."""
    scenario_pattern = os.path.join(scenarios_dir, "*.json")
    scenario_files = sorted(glob.glob(scenario_pattern))

    if not scenario_files:
        print(f"No scenario files found in {scenarios_dir}/")
        return

    print(f"Found {len(scenario_files)} scenario files")
    print("=" * 60)

    failed = 0

    for scenario_file in scenario_files:
        try:
            if not setup_scenario(scenario_file):
                failed += 1
        except Exception as e:
            print(f"Unexpected error processing {scenario_file}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    if failed > 0:
        print(f"Failed: {failed} scenarios")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario_file = sys.argv[1]
        if os.path.exists(scenario_file):
            setup_scenario(scenario_file)
        else:
            print(f"Scenario file not found: {scenario_file}")
            sys.exit(1)
    else:
        setup_all_scenarios()
