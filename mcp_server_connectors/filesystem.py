import sys
import os


def main():
    if len(sys.argv) < 2:
        print(
            "Error: No paths provided. Expected at least one directory path.",
            file=sys.stderr,
        )
        sys.exit(1)

    allowed_paths = sys.argv[1:]

    # Use node to use our locally installed/fixed version
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    local_filesystem_path = os.path.join(
        project_root,
        "node_modules",
        "@modelcontextprotocol",
        "server-filesystem",
        "dist",
        "index.js",
    )
    cmd = ["node", local_filesystem_path] + allowed_paths

    try:
        os.execvp("node", cmd)
    except Exception as e:
        print(f"Error running filesystem server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
