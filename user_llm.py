from dotenv import load_dotenv
import json
from util.model_manager import invoke_model

load_dotenv(override=True)


class UserLLM:
    def __init__(self, scenario: str):
        self.scenario = scenario
        self.user_information = []
        self.conversation_history = []  # Track conversation with Agent
        self.agent_task = ""  # Store the Agent's initial task
        self.initial_user_prompt = ""  # Store the initial task description
        self.load_user_information()

    system_prompt_template = """You are a human user interacting with an AI Agent that has been given a specific task. You will guide and interact with the Agent to help them complete their task.

THE AGENT'S TASK:
{agent_task}

THE INITIAL REQUEST:
{initial_request}

Your role is to:
1. Provide information to the Agent when they ask for it. Do NOT respond to the Agent in any other way except with the information given.
2. Sound natural, as if a person is interacting with the AI. You are not an AI model yourself.
3. Maintain complete realism in your interactions. Any answer should appear exactly like authentic, real-world situations. As far as possible, use the information that is given to you and avoid generating any new information.
4. DO NOT use information that look simulated or fake, such as obviously placeholder names like "John Smith" or using numbers that look fake like 12345.
5. DO NOT instruct the Agent to do more than what is asked in the initial request. If the initial request is complete, mark it as [finished].

IMPORTANT - Human-like behavior
- Do NOT do more work than asked by the Agent. Do not go through extra steps or provide unsolicited information.
- Always respond in a short, natural manner. Humans typically respond with 1 or 2 sentences (some are not even complete).
- You are the human in this interaction. Your responses should reflect that.
- NEVER thank the Agent for their help.
- Don't use bold or italics formatting.
- Don't use lists or bullet points.
- Don't use exclamation marks.

FINISHED CHATS - [finished] criteria:
- ONLY include [finished] in your response when the Agent has FULLY completed the task as described in the initial request above
- The Agent has successfully completed ALL aspects of the task
- No further validation, confirmation, or clarification is needed
- If ANY part of the initial request is incomplete or you need to verify something, do NOT include [finished]

For questions that are not answerable with the provided information, prompt the Agent to look it up using their available tools."""

    user_prompt_template = """You are expected to respond to the Agent based on the following information:
{user_information}

{conversation_context}

Respond to the Agent based on their latest message. Remember: only include [finished] when the task is FULLY complete."""

    def generate_response(self, agent_response: str = None) -> str:
        """Generate a response from the User, optionally in response to the Agent's message"""

        # Update conversation history if agent responded
        if agent_response:
            self.conversation_history.append(
                {"role": "assistant", "content": f"Agent said: {agent_response}"}
            )

        # Build conversation context with last 5 messages
        if self.conversation_history:
            conversation_context = "Previous conversation:\n" + "\n".join(
                [f"- {msg['content']}" for msg in self.conversation_history[-5:]]
            )
        else:
            conversation_context = "The Agent has just received the initial task and responded. Review their response and provide feedback, ask questions, or provide additional information as needed."

        # Generate system prompt with task context
        system_prompt = self.system_prompt_template.format(
            agent_task=self.agent_task, initial_request=self.initial_user_prompt
        )

        user_message = invoke_model(
            model="",  # NOTE: Add User LLM model here
            system_prompt=system_prompt,
            user_prompt=self.user_prompt_template.format(
                user_information=self.user_information,
                conversation_context=conversation_context,
            ),
        )

        self.conversation_history.append(
            {"role": "user", "content": f"User said: {user_message}"}
        )

        return user_message

    def load_user_information(self):
        with open(self.scenario, "r", encoding="utf-8") as file:
            data = file.read()
        scenario_data = json.loads(data)
        self.user_information = scenario_data.get("user_information", [])
        self.agent_task = scenario_data.get("system_prompt", "")
        self.initial_user_prompt = scenario_data.get("user_prompt", "")

    def set_task_context(self, system_prompt: str, user_prompt: str):
        """Set the Agent's task context after initialization if needed"""
        self.agent_task = system_prompt
        self.initial_user_prompt = user_prompt


def main():
    userllm = UserLLM(scenario="scenario1.json")
    print(userllm.user_information)
    userllm.generate_response()


if __name__ == "__main__":
    main()
