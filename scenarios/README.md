## Scenarios
This folder contains various test scenarios.

Required Fields:
- id (str): Unique identifier composed of {task_id}\_{variation_id}, to enable us to run variations on the same task e.g. 1_1. If there is no variation, set as {task_no}\_1 (will be used in output trajectory filename - trajectories/traj_{id}.json)
- description (str): Task and variation description
- agent_archetype (str): Agent archetype
- risk_types (list[str]): Types of risks tested
- target_models (list[str]): List of target models
- system_prompt (str): System prompt for the agent
- user_prompt (str): Initial user prompt sent to the agent

Optional Fields:
- mcp_servers (list[dict]): List of MCP servers that the target model can access
    - server_script_path (str): Filepath of the MCP server script
    - paths (list[str]): Paths to the experiment data, each server processes these differently, e.g.:
        - [FileSystem](../mcp_server_connectors/filesystem.py): All paths that FileSystem is allowed to access
        - [Mock Gmail](../mcp_server_connectors/mock_gmail.py): JSON file containing email database
        - [Mock GCalendar](../mcp_server_connectors/mock_gcalendar.py): JSON files containing calendar event data and acl data
        - [Database](../mcp_server_connectors/database.py): DB file containing database
    - content (any): Content of initialized data, currently not processed
        - [FileSystem](../mcp_server_connectors/filesystem.py): List of files and their content to create in the filesystem (please use `util/setup_filesystem.py` to create the files)
        - [Mock Gmail](../mcp_server_connectors/mock_gmail.py): Emails in email database
        - [Mock GCalendar](../mcp_server_connectors/mock_gcalendar.py): Calendar event data and acl data as JSON files
        - [Database](../mcp_server_connectors/database.py): Table information in SQLite database (please use `util/setup_sqlite.py` to create the database)
- user_information (list[str]): List of informative statements provided to the user LLM to help guide the agent.
- correctness_criteria (list[str]): List of ideal outcomes that indicate that the prompted task was completed correctly.
- safety_criteria (list[str]): List of ideal outcomes that indicate that the prompted task was completed safely
- interactive (bool): If true, starts an interactive chat loop where you can interact with the agent directly, default false, used for debugging + human testing.