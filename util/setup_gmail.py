import json
import sys
import os


def setup_mock_gmail_from_scenario(scenario_file):
    with open(scenario_file, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    gmail_config = None

    for server in scenario.get("mcp_servers", []):
        if server.get("server_script_path") == "mock_gmail.py":
            gmail_config = server
            break

    if not gmail_config:
        print("No mock_gmail MCP server found in scenario")
        return

    content = gmail_config.get("content", [])

    if not isinstance(content, list):
        print("Warning: Content is not a list. Expected a list of email data.")
        return

    path = gmail_config.get("paths", [])[0]  # Only expects one path here

    if os.path.exists(path):
        os.remove(path)
        print(f"Deleted existing file: {path}")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    email_dict = content[0]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(email_dict, f, indent=2, ensure_ascii=False)

    print(f"Created mock gmail database: {path}")
    print(f"Emails configured: {len(email_dict)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_mock_gmail.py <scenario_file>")
        sys.exit(1)

    scenario_file = sys.argv[1]
    setup_mock_gmail_from_scenario(scenario_file)
