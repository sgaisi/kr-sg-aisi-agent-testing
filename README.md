# KR-SG AISI Bilateral Agent Testing

This is a bilateral testing framework for evaluating AI agent safety and correctness across multiple scenarios. The system simulates realistic workplace environments where AI agents interact with sensitive data through various tools (email, databases, filesystems, calendars) to test for data leakage, improper policy compliance, and other safety issues.

The framework uses Model Context Protocol (MCP) servers to provide controlled access to different data sources and services. Each test scenario defines specific tasks for agents to complete while measuring both task performance and safety compliance.

## Quick Start

0. Set up a virtual environment (Optional)
```bash
# Windows
py -3.11 -m venv venv
venv\Scripts\activate
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your .env file with API keys:

```
OPENAI_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
```

- AWS Bedrock should be set up via AWS CLI/config

3. Set up the model manager:

```bash
python util/get_models.py
```

> [!NOTE]
> This generates `util/all_models.json` which contains available models for testing. Rather than hardcoding model lists, the system dynamically loads models from this file. If you cannot see a model you expect, it means that the model is not currently available via the configured API keys or the API keys are missing.

4. Install MCP Servers

```bash
npm install @modelcontextprotocol/server-filesystem
pip install mcp-server-sqlite
```

5. Configure AI models
- Add the Agent model to be tested here: `scenarios/1_1.py line 7`
```json
  "target_models": [""],
```

- Add the User LLM model here: `user_llm.py line 79`

```python
            model="",  # NOTE: Add User LLM model here
```

- Add the Judge LLM model here: `scenario_judge.py line 432`
```python
            model="",  # NOTE: Add judge model here
```

> [!TIP]
> Refer to the generated `util/all_models.json` for the exact model name

6. Run a test scenario:

```bash
python scenario_runner.py scenarios/1_1.json
```

Trajectories will be generated in the `trajectories` folder.

7. Judge the results:

Then run the command below:
```bash
python scenario_judge.py scenarios/1_1.json
```

Judgements will be generated in the `judgement_results` folder.

## Experiment Pipeline

### Scenario Configuration

All scenarios are defined in the `scenarios/` folder as JSON files. Each scenario specifies:

- The task to be performed
- The MCP servers available and their initial data
- The target AI models to test

> [!IMPORTANT]
> Please run `python util/setup.py <scenario_file.json>` after modifying a scenario file to ensure the MCP servers have the updated initial data.

### Running Scenarios
Use `scenario_runner.py` to execute a scenario for all specified models. The script interacts with the defined MCP servers to simulate realistic data access patterns.

```bash
python scenario_runner.py scenarios/1_1.json
```

#### Temporary Test Environment
To ensure that set up files are not overwritten, the script makes a copy of the scenario file in the `experiment_data/` folder into a `tmp/` folder for execution. For MCP servers that expose the full file path, i.e. the File System MCP server, a `filetree/` folder is created under `D:/` drive to host the files.

> [!WARNING] 
> Please ensure that you do NOT have any important files under `D:/filetree/` as they may be overwritten during testing.

#### Trajectory
While running the scenario, trajectory files that log the agent's interactions are generated. The trajectories comprise a sequence of the agent's steps, which is defined as the agent's message to the user or action taken using an MCP tool. Currently, each scenario runs with a maximum of 60 steps per model to limit execution time (this can be adjusted in the `agent.py` file). When the run ends, the temporary files are deleted and the results are saved in the `trajectories/` folder.

#### Multi-Turn
If the agent has to interact with a user for clarification or additional information, a UserLLM, which has access to information given through the `user_information` field in the scenario JSON file, is prompted to respond to the agent's queries based on the information provided. This simulates a real-world scenario where an AI agent might ask a human user for more details to complete a task effectively.

### Judging Scenarios

Use `scenario_judge.py` to evaluate the results of a scenario run. The judge analyzes the trajectory files generated during execution to assess both correctness (did the agent complete the task?) and safety (did the agent avoid leaking sensitive data?). The judgement criteria are also defined in the scenario JSON files. The judgement is binary and the results are saved in the `judgement_results/` folder.

```bash
python scenario_judge.py scenarios/1_1.json
```


## MCP Server Setup

### File System MCP Server (Pre-built, local files  only)

**Installation & Setup:**

1. Install the npm package locally

```bash
npm install @modelcontextprotocol/server-filesystem
```

- Please look at `experiment_data/filetree/` for sample files used in the scenarios.

### SQLite MCP Server (Pre-built, local SQLite only)

```bash
pip install mcp-server-sqlite
```

- Please look at `experiment_data/sqlitedatabase/` for sample database files used in the scenarios.

### Mock Gmail MCP Server (Custom, locally mocked)
- Please look at `experiment_data/mock_gmail_db/` for sample email data used in the scenarios.

### Mock Google Calendar MCP Server (Custom, locally mocked)
- Please look at `experiment_data/mock_gcal_db/` for sample calendar data used in the scenarios. Scenarios require both calendar event data and ACL data for proper access control testing.

## Running Tests

### Individual Scenarios

```bash
python scenario_runner.py scenarios/1_1.json    # Run single scenario
python scenario_judge.py scenarios/1_1.json     # Judge the results
```

### Batch Processing

```bash
python main.py                                  # Run all scenarios on all models
```

The main script automatically:

- Reads target models from each scenario file
- Runs missing combinations only
- Provides progress feedback and error handling

## Trajectories

The `trajectories` folder contains the trajectories produced from running scenarios.

- scenario_id (str): Unique identifier composed of {task_id}\_{variation_id}
- model (str): Model of agent
- total_steps (int): Total number of steps taken by agent (each batch tool call and Agent message counts as one step).
- max_steps (int): Maximum number of steps allowed for agent
- conversation_history (list[dict]): List of dictionaries, each describing one step
  - "role" (str): Role of message sender, one of "system", "user", "assistant", "tool"
  - if role == "system" or "user":
    - "content" (str): Content of message
  - if role == "assistant" and tool_calls is empty:
    - "content" (str): Content of message sent from the agent to the user
    - "step" (int): Step number of agent when message was sent
  - if role == "assistant" and tool_calls is not empty:
    - "content" (str, optional): Reasoning of the agent before calling the tool, may be empty
    - "tool_calls_and_responses" (list[dict]): List of tool calls and their responses
      - each dict contains:
        - "id" (str): Unique identifier of tool call (not tool name)
        - "name" (str): Name of tool called
        - "arguments" (str): Input provided to tool
        - "content" (str): Response returned from tool
    - "step" (int): Step number of agent when message was sent

## Judgement Results

The `judgement_results` folder contains the LLM judge results combined with the trajectory.

All files have the naming convention {judgement_type}_{scenario_id}_{target_model}_{timestamp (yy_MM_dd_HH_mm)}.json

- scenario_id (str): ID from the scenario file
- scenario_filename (str): Name of the scenario file
- traj_filename (str): Name of the trajectory file being judged
- model (str): Name of target model
- combined_at (datetime): Time of combination of judgement with trajectory.
- trajectory (dict): See [Trajectories](#trajectories).
- correctness (dict): Judgement of correctness criteria
  - criterion_description_{n} (str): Description of criterion from scenario file
  - criterion_met_{n} (bool): true if criterion is fulfilled, otherwise false
  - criterion_explanation_{n} (str): Explanation of criterion judgement
  - ...
- safety (dict): Judgement of safety criteria
  - criterion_description_{n} (str): Description of criterion from scenario file
  - criterion_met_{n} (bool): true if criterion is fulfilled, otherwise false
  - criterion_explanation_{n} (str): Explanation of criterion judgement
  - ...
> Note: n represents the criterion ID
