import asyncio
import json
import os
import sys
import traceback

from datetime import datetime
from dotenv import load_dotenv

from agent import Agent
from client import MCPClient
from util.copy_scenario_files import copy_scenario_files
from util.remove_scenario_files import remove_scenario_files
from user_llm import UserLLM

load_dotenv(override=True)


class ScenarioRunner:
    def __init__(self, scenario_path: str, model_name: str = None):
        self.scenario_path = scenario_path
        self.scenario = self._load_scenario()

        self.client = MCPClient()
        self.agent = None

        if model_name:
            self.model_names = [model_name]
        else:
            if not self.scenario.get("target_models", []):
                raise ValueError(
                    "Model name must be specified in scenario JSON with 'target_models' field or as command line argument"
                )
            self.model_names = self.scenario["target_models"]

        self.user_llm = UserLLM(scenario_path)

    def _load_scenario(self) -> dict:
        with open(self.scenario_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def copy_files(self):
        """Copy scenario files to their destination directories"""
        print("\n0. Copying Scenario Files")
        try:
            copy_scenario_files(self.scenario_path)
            print("Files copied successfully\n")
        except Exception as e:
            print(f"Warning: Error copying files: {e}\n")

    async def connect_to_servers(self):
        """Connect to all MCP servers defined in scenario"""
        print("1. Connecting to MCP Servers")
        required_servers = self.scenario.get("mcp_servers", [])

        await self.client.connect_to_servers(required_servers)

    async def run_scenario(self):
        """Execute the scenario"""
        print("\n2. Running Scenario")
        print(f"ID: {self.scenario.get('id')}")
        print(f"Description: {self.scenario.get('description')}")

        for model_name in self.model_names:
            await self.run_single_scenario(model_name)
        return

    async def run_single_scenario(self, model_name: str):
        self.agent = Agent(
            model_name, self.client, self.scenario.get("system_prompt", "")
        )

        # Skip initial prompt if interactive mode is enabled
        interactive_mode = self.scenario.get("interactive", False)
        if interactive_mode:
            print("Entering Interactive Mode")
            print("Type 'quit', 'exit', or 'q' to exit.\n")
            await self.interactive_loop()
            return

        # Get the initial user prompt from the scenario and send it directly
        user_prompt = self.scenario.get("user_prompt", "")
        if not user_prompt:
            raise Exception("ERROR: No user prompt found in scenario.")

        print(f"\nInitial User Prompt:\n{user_prompt}\n")
        print("\n[AgentLLM is processing initial prompt...]")
        initial_response = await self.agent.process_query(user_prompt)
        print(f"\nAgentLLM: {initial_response}")

        await self.automated_conversation_loop(initial_agent_response=initial_response)

        self.save_trajectory_and_print_evaluation(model_name)
        return

    def save_trajectory_and_print_evaluation(self, model_name: str):
        """Save execution logs to JSON file"""

        processed = []
        i = 0

        def response_matches_call(tool_call, tool_response):
            return (
                tool_response.get("role") == "tool"
                and tool_response.get("tool_call_id") == tool_call["id"]
            )

        def combine_call_and_response(tool_call, tool_response):
            return {
                "id": tool_call["id"],
                "name": tool_call["function"]["name"],
                "arguments": tool_call["function"]["arguments"],
                "content": tool_response["content"],
            }

        while i < len(self.agent.conversation_history):
            msg = self.agent.conversation_history[i]

            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                tool_calls_and_responses = []
                for j, tool_call in enumerate(msg["tool_calls"]):
                    if i + j + 1 < len(self.agent.conversation_history):
                        tool_response = self.agent.conversation_history[i + j + 1]
                        if response_matches_call(tool_call, tool_response):
                            tool_calls_and_responses.append(
                                combine_call_and_response(tool_call, tool_response)
                            )

                processed.append(
                    {
                        "role": "assistant",
                        "content": msg.get("content"),
                        "tool_calls_and_responses": tool_calls_and_responses,
                        "step": msg.get("step"),
                    }
                )

                i += 1 + len(tool_calls_and_responses)
            else:
                processed.append(msg)
                i += 1

        log_data = {
            "scenario_id": self.scenario.get("id"),
            "model": model_name,
            "total_steps": self.agent.total_steps,
            "max_steps": self.agent.max_steps,
            "conversation_history": processed,
        }

        safe_model_name = model_name.replace("/", "_").replace(":", "_")

        # Add timestamp annotation (yy_mm_dd_hh_mm)
        timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")

        traj_name = f"trajectories\\traj_{self.scenario.get('id', 'unknown')}_{safe_model_name}_{timestamp}.json"

        os.makedirs("trajectories", exist_ok=True)

        with open(traj_name, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, default=str, ensure_ascii=False)

        print(f"\n Trajectory saved to: {traj_name}")
        print(f"   Total steps: {self.agent.total_steps}/{self.agent.max_steps}")
        print(f"   Total messages: {len(self.agent.conversation_history)}")
        return

    async def automated_conversation_loop(self, initial_agent_response: str = None):
        """Run automated conversation between UserLLM and AgentLLM

        Args:
            initial_agent_response: Optional initial response from Agent to start the conversation
        """
        # Start with initial response if provided
        last_agent_response = initial_agent_response

        while self.agent.total_steps < self.agent.max_steps:
            print(f"Total Steps: {self.agent.total_steps}/{self.agent.max_steps}")

            try:
                print("\n[UserLLM is generating a query...]")
                user_query = self.user_llm.generate_response(last_agent_response)
                print(f"\nUserLLM: {user_query}")

                # Only the UserLLM can mark the conversation as finished
                if "[finished]" in user_query.lower():
                    print("\n[Conversation marked as finished by UserLLM]")
                    self.agent.conversation_history.append(
                        {
                            "role": "user",
                            "content": user_query,
                        }
                    )
                    break

                print("\n[AgentLLM is processing...]")
                agent_response = await self.agent.process_query(user_query)
                print(f"\nAgentLLM: {agent_response}")

                last_agent_response = agent_response

            except Exception as e:
                print(f"\nError in conversation: {str(e)}")

                traceback.print_exc()
                break

        if self.agent.total_steps >= self.agent.max_steps:
            print(f"\n[Reached maximum steps ({self.agent.max_steps})]")

        print("\n[Automated conversation ended]")

    async def interactive_loop(self):
        """Run an interactive chat loop where you can interact with the agent directly as a user"""
        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() in ["quit", "exit", "q"]:
                    break

                if not query:
                    continue

                response = await self.agent.process_query(query)
                print(f"\n{response}")

            except KeyboardInterrupt:
                print("\n\nExiting interactive mode...")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scenario_runner.py <scenario.json> [--model <model_name>]")
        print("\nExamples:")
        print("  python scenario_runner.py scenario1.json")
        sys.exit(1)

    scenario_path = sys.argv[1]

    model_name = None
    if len(sys.argv) >= 4 and sys.argv[2] == "--model":
        model_name = sys.argv[3]

    if "scenarios" not in scenario_path:
        scenario_path = os.path.join("scenarios", scenario_path)

    if not os.path.exists(scenario_path):
        print(f"Error: Scenario file not found: {scenario_path}")
        sys.exit(1)

    runner = ScenarioRunner(scenario_path, model_name)

    try:
        runner.copy_files()

        await runner.connect_to_servers()

        await runner.run_scenario()

        print("\nCleaning up copied files...")
        try:
            remove_scenario_files(scenario_path)
        except Exception as e:
            print(f"Warning: Error removing files: {e}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError during scenario execution: {e}")

        traceback.print_exc()
    finally:
        # Cleanup MCP client
        await runner.client.cleanup()

        # Give async tasks time to clean up
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    # Hotfix: Set Windows-specific event loop policy to avoid issues
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
