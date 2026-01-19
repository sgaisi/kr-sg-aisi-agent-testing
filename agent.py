import json
from util.model_manager import invoke_model_with_tools


class Agent:
    """Agent that processes queries and executes tools using a language model"""

    def __init__(self, model_name: str, client, system_prompt: str = ""):
        """
        Initialize the Agent

        Args:
            model_name: Name of the model to use
            client: MCPClient instance for tool execution
            system_prompt: Optional system prompt for the agent
        """
        self.model_name = model_name
        self.client = client
        self.conversation_history = []
        self.total_steps = 1
        self.max_steps = 60

        if system_prompt:
            self.conversation_history.append(
                {"role": "system", "content": system_prompt}
            )

    async def process_query(self, query: str) -> str:
        """
        Process a query using the language model and available tools

        Args:
            query: User query to process

        Returns:
            str: Agent's response text
        """
        if self.total_steps >= self.max_steps:
            raise RuntimeError(
                f"Maximum steps ({self.max_steps}) reached. Cannot process further queries."
            )

        self.conversation_history.append({"role": "user", "content": query})

        final_text = []

        while self.total_steps < self.max_steps:
            assistant_message = invoke_model_with_tools(
                model=self.model_name,
                messages=self.conversation_history,
                tools=self.client.available_tools,
            )

            print("\n[Assistant Response]")
            print(assistant_message)

            if not assistant_message.tool_calls:
                if assistant_message.content:
                    self.conversation_history.append(
                        {
                            "role": "assistant",
                            "content": assistant_message.content,
                            "step": self.total_steps,
                        }
                    )
                    self.total_steps += 1
                    final_text.append(assistant_message.content)
                break

            # Track and print assistant's reasoning before tool calls
            reasoning_text = (
                assistant_message.content if assistant_message.content else ""
            )

            print(f"Reasoning: {reasoning_text}")

            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        tc.model_dump() for tc in assistant_message.tool_calls
                    ],
                    "step": self.total_steps,
                }
            )
            self.total_steps += 1

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                try:
                    tool_result_content = await self.client.call_tool(
                        tool_name, tool_args
                    )
                except Exception as e:
                    error_msg = f"Error executing tool '{tool_name}': {str(e)}"
                    print(f"\n[{error_msg}]")
                    tool_result_content = error_msg

                self.conversation_history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result_content,
                    }
                )

        return "\n".join(final_text) if final_text else "Task completed."
