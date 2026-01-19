import json
import os
import re
import sys
from pathlib import Path


def setup_filesystem_from_setup_step(step):
    """Set up filesystem from a setup step dict (new format).

    Expected step format:
    {
        "script": "environments/setup/setup_filesystem.py",
        "filesystem_path": "experiment_data/filetree",
        "content": {
            "path/to/file.txt": "file content..."
        }
    }
    """
    root_path = step.get("filesystem_path")
    if not root_path:
        print("No filesystem_path specified in setup step")
        return

    content = step.get("content", {})
    if not isinstance(content, dict):
        print("Warning: Content is not a dictionary. Expected path-content pairs.")
        return

    if root_path.startswith("./"):
        root_path = root_path[2:]

    os.makedirs(root_path, exist_ok=True)

    # Create files from content dictionary
    for file_path, file_content in content.items():
        if file_content == "[File not found]":
            print(f"Skipped (marked as not found): {file_path}")
            continue

        full_path = os.path.join(root_path, file_path)

        directory = os.path.dirname(full_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if file_path.endswith("/"):
            print(f"Created folder: {full_path}")
            continue

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(str(file_content))
            print(f"Created: {full_path}")
        except Exception as e:
            print(f"Error creating file {full_path}: {e}")
            continue

    print("Filesystem setup completed")


def setup_filesystem_from_scenario(scenario_file):
    with open(scenario_file, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    filesystem_config = None
    root_path = None

    for server in scenario.get("mcp_servers", []):
        if server.get("server_script_path") == "filesystem.py":
            filesystem_config = server
            if server.get("paths"):
                root_path = server["paths"][0]
            break

    if not filesystem_config:
        print("No filesystem MCP server found in scenario")
        return

    if not root_path:
        print("No root path specified for filesystem MCP server")
        return

    content = filesystem_config.get("content", {})

    if not isinstance(content, dict):
        print("Warning: Content is not a dictionary. Expected path-content pairs.")
        return

    # Use the path from the scenario configuration
    if root_path.startswith("./"):
        root_path = root_path[2:]

    os.makedirs(root_path, exist_ok=True)

    # Create files from content dictionary
    for file_path, file_content in content.items():
        if file_content == "[File not found]":
            print(f"Skipped (marked as not found): {file_path}")
            continue

        # Check for redundant directory prefix in file_path
        base_dir_name = os.path.basename(root_path)
        if file_path.startswith(base_dir_name + "/"):
            file_path = file_path[len(base_dir_name) + 1 :]
            print(f"Stripped redundant prefix, using: {file_path}")

        full_path = os.path.join(root_path, file_path)

        directory = os.path.dirname(full_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if file_path.endswith("/"):
            print(f"Created folder: {full_path}")
            continue

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(str(file_content))

            print(f"Created: {full_path}")

        except Exception as e:
            print(f"Error creating file {full_path}: {e}")
            continue

    print("Filesystem setup completed")


def extract_from_filesystem(scenario_file, output_file=None):
    """Extract from filesystem when JSON parsing fails due to control characters."""

    scenario_id = os.path.splitext(os.path.basename(scenario_file))[0]

    # Try to extract the path from the broken JSON by reading just the relevant lines
    base_path = None
    try:
        with open(scenario_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Look for the filesystem server path in the file content
        path_match = re.search(r'"paths":\s*\[\s*"([^"]+)"', content)
        if path_match:
            scenario_path = path_match.group(1)
            if scenario_path.startswith("./"):
                scenario_path = scenario_path[2:]
            base_path = Path(scenario_path)
            print(f"Found path from scenario: {scenario_path}")
    except Exception as e:
        print(f"Could not extract path from scenario file: {e}")

    # If unable to parse the path, try common fallbacks
    if not base_path or not base_path.exists():
        possible_paths = [
            f"experiment_data/filetree/{scenario_id}",
            "experiment_data/filetree/HR",
            "experiment_data/filetree/off_boarding",
            "experiment_data/filetree",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                base_path = Path(path)
                break

    if not base_path or not base_path.exists():
        print(f"Could not find filesystem directory for scenario {scenario_id}")
        return

    print(f"Extracting from directory: {base_path}")

    # Scan directory and extract all files
    content_dict = {}
    files_read = 0

    for root, _, files in os.walk(base_path):
        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(base_path)
            file_path = str(rel_path).replace("\\", "/")

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    file_content = f.read()

                content_dict[file_path] = file_content
                files_read += 1
                print(f"Read: {file_path}")

            except UnicodeDecodeError:
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        file_content = f.read()

                    content_dict[file_path] = f"{file_content}"
                    files_read += 1
                    print(f"Read (binary/forced): {file_path}")

                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    content_dict[file_path] = f"[Error reading file: {e}]"
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                content_dict[file_path] = f"[Error reading file: {e}]"

    if not output_file:
        output_file = f"{scenario_id}_filesys.txt"

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Filesystem Content Dictionary\n")
            f.write("# Generated from existing files (JSON parsing failed)\n")
            f.write("# Ready to paste into scenario JSON\n\n")
            f.write("{\n")
            f.write('  "content": {\n')

            items = list(content_dict.items())
            for i, (path, content) in enumerate(items):
                escaped_content = (
                    content.replace("\\", "\\\\")
                    .replace('"', '\\"')
                    .replace("\n", "\\n")
                )
                comma = "," if i < len(items) - 1 else ""
                f.write(f'    "{path}": "{escaped_content}"{comma}\n')

            f.write("  }\n")
            f.write("}\n")

        print(f"\nContent dictionary saved to: {output_file}")
        print(f"Files processed: {files_read}")

    except Exception as e:
        print(f"Error saving content dictionary: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_filesystem.py <scenario_file.json> [OPTIONS]")
        print("\nOptions:")
        print("  --extract     Extract current files to dictionary format")
        sys.exit(1)

    scenario_file = sys.argv[1]

    if not os.path.exists(scenario_file):
        print(f"Scenario file not found: {scenario_file}")
        sys.exit(1)

    if len(sys.argv) > 2:
        option = sys.argv[2]
        if option == "--extract":
            extract_from_filesystem(scenario_file)
        else:
            print(f"Unknown option: {option}")
            sys.exit(1)
    else:
        setup_filesystem_from_scenario(scenario_file)
