import json
import sys
import os


def setup_mock_gcal_from_scenario(scenario_file):
    with open(scenario_file, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    gcal_config = None

    for server in scenario.get("mcp_servers", []):
        if server.get("server_script_path") == "mock_gcalendar.py":
            gcal_config = server
            break

    if not gcal_config:
        print("No mock_gcalendar MCP server found in scenario")
        return

    content = gcal_config.get("content", [])

    if not isinstance(content, list):
        print("Warning: Content is not a list. Expected a list of calendar events.")
        return

    paths = gcal_config.get("paths", [])
    if len(paths) < 2:
        print("Warning: Expected two paths (events and acl). Found:", len(paths))
        return

    events_path = paths[0]  # First path is for events
    acl_path = paths[1]  # Second path is for ACL

    if os.path.exists(events_path):
        os.remove(events_path)
        print(f"Deleted existing file: {events_path}")

    if os.path.exists(acl_path):
        os.remove(acl_path)
        print(f"Deleted existing file: {acl_path}")

    os.makedirs(os.path.dirname(events_path), exist_ok=True)
    os.makedirs(os.path.dirname(acl_path), exist_ok=True)

    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)

    print(f"Created mock gcal events database: {events_path}")
    print(f"Events configured: {len(content)}")

    acl_content = gcal_config.get("acl_content", {"primary": []})

    with open(acl_path, "w", encoding="utf-8") as f:
        json.dump(acl_content, f, indent=2, ensure_ascii=False)

    print(f"Created mock gcal ACL database: {acl_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_gcal.py <scenario_file>")
        sys.exit(1)

    scenario_file = sys.argv[1]
    setup_mock_gcal_from_scenario(scenario_file)
