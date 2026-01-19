import difflib
import json

import boto3
import dotenv
import openai
from google import genai
from google.genai.types import GenerateContentConfig
from together import Together
from util.get_models import get_all_available_models

dotenv.load_dotenv(override=True)

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
DEFAULT_AWS_REGION_NAME = "us-east-1"
DEFAULT_MAX_TOKENS = 20000


def open_ai(
    model: str = None,
    system_prompt: str = None,
    user_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
):

    if not model:
        raise ValueError("Model name must be provided for OpenAI invocation.")
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    # Models that don't support temperature parameter
    models_without_temperature = [
        "gpt-5",
        "o3-deep-research",
        "o1",
        "o1-mini",
        "o1-preview",
    ]

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_completion_tokens": max_tokens,
    }

    # Only add temperature if the model supports it
    if not any(no_temp_model in model for no_temp_model in models_without_temperature):
        kwargs["temperature"] = temperature

    response = openai.chat.completions.create(**kwargs)

    return response.choices[0].message.content


def aws_bedrock(
    model: str = None,
    system_prompt: str = None,
    user_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
    region_name: str = DEFAULT_AWS_REGION_NAME,
):

    if not model:
        raise ValueError("Model name must be provided for AWS Bedrock invocation.")
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    if max_tokens is None:
        max_tokens = DEFAULT_MAX_TOKENS

    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime", region_name=region_name
    )

    if "anthropic.claude" in model or "us.anthropic.claude" in model:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
    else:
        body = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

    response = bedrock_runtime.invoke_model(modelId=model, body=json.dumps(body))

    response_body = json.loads(response["body"].read())

    if "anthropic.claude" in model or "us.anthropic.claude" in model:
        return response_body["content"][0]["text"]
    else:
        return response_body.get("completion", response_body)


def google_gemini(
    model: str = None,
    system_prompt: str = None,
    user_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
):

    if not model:
        raise ValueError("Model name must be provided for Google Gemini invocation.")
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    client = genai.Client()

    contents = user_prompt

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )

    return response.text


def together_ai(
    model: str = None,
    system_prompt: str = None,
    user_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
):

    if not model:
        raise ValueError("Model name must be provided for TogetherAI invocation.")
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    client = Together()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )

    return response.choices[0].message.content


def find_closest_match(input_str, choices):
    input_str_lower = input_str.lower()
    best_match = None
    highest_similarity = 0

    for choice in choices:
        similarity = difflib.SequenceMatcher(
            None, input_str_lower, choice.lower()
        ).ratio()
        if similarity == 1:
            return choice

        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = choice

    return best_match


def load_model_list(provider_name: str):
    """
    Loads models for each provider. Requires all_models.json to be present.
    """
    try:
        with open("util/all_models.json", "r", encoding="utf-8") as f:
            all_models = json.load(f)
    except FileNotFoundError:
        print("all_models.json not found, generating all_models.json")
        all_models = get_all_available_models()

    if provider_name.lower() == "openai":
        return all_models.get("openai", [])
    elif provider_name.lower() == "bedrock":
        return all_models.get("bedrock", [])
    elif provider_name.lower() == "gemini":
        return all_models.get("gemini", [])
    elif provider_name.lower() == "together":
        return all_models.get("together", [])
    else:
        raise ValueError(f"Unknown provider name: {provider_name}")


def invoke_model(
    model: str,
    system_prompt: str = None,
    user_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
    verbose: bool = False,
):
    """
    Invokes the model after matching it to the appropriate provider and model name.
    Please use @invoke_model_verbatim for faster results and more niche models.
    """
    if "gpt" in model.lower() or "o1" in model.lower():
        model = find_closest_match(model, load_model_list("openai"))
        if verbose:
            print(f"Using OpenAI model: {model}")
        return open_ai(model, system_prompt, user_prompt, temperature, max_tokens)
    elif model.startswith("gemini-"):
        model = find_closest_match(model, load_model_list("gemini"))
        if verbose:
            print(f"Using Google Gemini model: {model}")
        return google_gemini(model, system_prompt, user_prompt, temperature, max_tokens)
    elif "anthropic" in model.lower() or "claude" in model.lower():
        model = "us." + find_closest_match(model, load_model_list("bedrock"))
        if verbose:
            print(f"Using AWS Bedrock model: {model}")
        return aws_bedrock(model, system_prompt, user_prompt, temperature, max_tokens)
    else:
        model = find_closest_match(model, load_model_list("together"))
        if verbose:
            print(f"Using TogetherAI model: {model}")
        return together_ai(model, system_prompt, user_prompt, temperature, max_tokens)


def invoke_model_verbatim(
    model: str,
    system_prompt: str = None,
    user_prompt: str = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
):
    """
    Invokes the model as given without any matching. This assumes the user knows the EXACT model name.
    """
    if "gpt" in model.lower() or "o1" in model.lower():
        return open_ai(model, system_prompt, user_prompt, temperature, max_tokens)
    elif model.startswith("gemini-"):
        return google_gemini(model, system_prompt, user_prompt, temperature, max_tokens)
    elif "anthropic" in model.lower():
        return aws_bedrock(model, system_prompt, user_prompt, temperature, max_tokens)
    else:
        return together_ai(model, system_prompt, user_prompt, temperature, max_tokens)


def _sanitize_tool_schema(schema):
    """
    Sanitize tool schema to ensure it's valid for all model providers.
    Fixes common issues like missing or invalid 'type' fields.
    """
    if not isinstance(schema, dict):
        return schema

    sanitized = schema.copy()

    # Fix missing or invalid type field
    if (
        "type" not in sanitized
        or sanitized["type"] is None
        or sanitized["type"] == "None"
    ):
        sanitized["type"] = "object"

    # Add properties field to object schemas as required by some models
    if sanitized.get("type") == "object" and "properties" not in sanitized:
        sanitized["properties"] = {}

    # Recursively sanitize nested schemas
    if "properties" in sanitized and isinstance(sanitized["properties"], dict):
        sanitized["properties"] = {
            key: _sanitize_tool_schema(val) if isinstance(val, dict) else val
            for key, val in sanitized["properties"].items()
        }

    if "items" in sanitized and isinstance(sanitized["items"], dict):
        sanitized["items"] = _sanitize_tool_schema(sanitized["items"])

    return sanitized


def _sanitize_tools(tools):
    """Sanitize all tools in the list"""
    sanitized_tools = []
    for tool in tools:
        sanitized_tool = tool.copy()
        if "function" in sanitized_tool and "parameters" in sanitized_tool["function"]:
            sanitized_tool["function"] = sanitized_tool["function"].copy()
            sanitized_tool["function"]["parameters"] = _sanitize_tool_schema(
                sanitized_tool["function"]["parameters"]
            )
        sanitized_tools.append(sanitized_tool)
    return sanitized_tools


def invoke_model_with_tools(
    model: str,
    messages: list,
    tools: list,
    temperature: float = 0.7,
    max_tokens: int = None,
):
    """
    Invokes the model with tool/function calling support.

    Args:
        model: Exact model name (verbatim)
        messages: Conversation history in OpenAI format
        tools: List of tool definitions in OpenAI format
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        The assistant message object with potential tool_calls
    """
    tools = _sanitize_tools(tools)

    if "gpt" in model.lower() or "o1" in model.lower():
        return _openai_with_tools(model, messages, tools, temperature, max_tokens)
    elif "gemini" in model.lower():
        return _gemini_with_tools(model, messages, tools, temperature, max_tokens)
    elif (
        "anthropic" in model.lower()
        or "claude" in model.lower()
        or "pixtral" in model.lower()
    ):
        return _bedrock_with_tools(model, messages, tools, temperature, max_tokens)
    else:
        return _together_with_tools(
            model, messages, tools, temperature, max_tokens
        )  # NOTE: Assume TogetherAI for other models, might not always be true.


def _openai_with_tools(
    model: str, messages: list, tools: list, temperature: float, max_tokens: int
):
    """OpenAI tool calling implementation"""
    client = openai.OpenAI()

    # Models that don't support temperature
    models_without_temperature = [
        "gpt-5",
        "o3-deep-research",
        "o1",
        "o1-mini",
        "o1-preview",
    ]

    kwargs = {"model": model, "messages": messages, "tools": tools}

    if max_tokens:
        kwargs["max_completion_tokens"] = max_tokens

    if not any(no_temp_model in model for no_temp_model in models_without_temperature):
        kwargs["temperature"] = temperature

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message


def _bedrock_with_tools(
    model: str, messages: list, tools: list, temperature: float, max_tokens: int
):
    """AWS Bedrock Claude tool calling implementation"""
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime", region_name=DEFAULT_AWS_REGION_NAME
    )

    # Convert OpenAI format to Claude format
    claude_messages = []
    system_prompt = None

    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        elif msg["role"] == "user":
            claude_messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])

            if tool_calls:
                # Assistant made tool calls
                tool_use_content = []
                if content:
                    tool_use_content.append({"type": "text", "text": content})

                for tc in tool_calls:
                    tool_use_content.append(
                        {
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"]),
                        }
                    )
                claude_messages.append(
                    {"role": "assistant", "content": tool_use_content}
                )
            else:
                claude_messages.append({"role": "assistant", "content": content})
        elif msg["role"] == "tool":
            # Tool result
            claude_messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg["tool_call_id"],
                            "content": msg["content"],
                        }
                    ],
                }
            )

    # Convert tools to Claude format
    claude_tools = []
    for tool in tools:
        func = tool["function"]
        claude_tools.append(
            {
                "name": func["name"],
                "description": func["description"],
                "input_schema": func["parameters"],
            }
        )

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens or 20000,
        "temperature": temperature,
        "messages": claude_messages,
        "tools": claude_tools,
    }

    if system_prompt:
        body["system"] = system_prompt

    response = bedrock_runtime.invoke_model(modelId=model, body=json.dumps(body))

    response_body = json.loads(response["body"].read())

    # Convert Claude response to OpenAI format
    class AssistantMessage:
        def __init__(self):
            self.content = None
            self.tool_calls = None

    assistant_msg = AssistantMessage()

    # Extract text content and tool uses
    text_content = []
    tool_calls = []

    for content_item in response_body.get("content", []):
        if content_item.get("type") == "text":
            text_content.append(content_item["text"])
        elif content_item.get("type") == "tool_use":
            # Convert to OpenAI tool call format
            class ToolCall:
                def __init__(self, tc_id, name, arguments):
                    self.id = tc_id
                    self.type = "function"
                    self.function = type(
                        "obj",
                        (object,),
                        {"name": name, "arguments": json.dumps(arguments)},
                    )()

                def model_dump(self):
                    return {
                        "id": self.id,
                        "type": self.type,
                        "function": {
                            "name": self.function.name,
                            "arguments": self.function.arguments,
                        },
                    }

            tool_calls.append(
                ToolCall(
                    content_item["id"], content_item["name"], content_item["input"]
                )
            )

    assistant_msg.content = "\n".join(text_content) if text_content else None
    assistant_msg.tool_calls = tool_calls if tool_calls else None

    return assistant_msg


def _gemini_with_tools(
    model: str, messages: list, tools: list, temperature: float, max_tokens: int
):
    """Google Gemini tool calling implementation"""
    from google.genai.types import Tool as GeminiTool, FunctionDeclaration

    client = genai.Client()

    def clean_schema_for_gemini(schema):
        """Recursively remove fields that Gemini doesn't accept"""
        if isinstance(schema, dict):
            # Remove problematic fields
            cleaned = {}
            for key, value in schema.items():
                if key in ["$schema", "additionalProperties", "additional_properties"]:
                    continue
                cleaned[key] = clean_schema_for_gemini(value)
            return cleaned
        elif isinstance(schema, list):
            return [clean_schema_for_gemini(item) for item in schema]
        else:
            return schema

    # Convert OpenAI format to Gemini format
    system_instruction = None
    gemini_messages = []

    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
        elif msg["role"] == "user":
            gemini_messages.append(
                {"role": "user", "parts": [{"text": msg["content"]}]}
            )
        elif msg["role"] == "assistant":
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])

            parts = []
            if content:
                parts.append({"text": content})

            if tool_calls:
                for tc in tool_calls:
                    parts.append(
                        {
                            "function_call": {
                                "name": tc["function"]["name"],
                                "args": json.loads(tc["function"]["arguments"]),
                            }
                        }
                    )

            # Only add the message if there are parts
            if parts:
                gemini_messages.append({"role": "model", "parts": parts})
        elif msg["role"] == "tool":
            # Tool result
            gemini_messages.append(
                {
                    "role": "function",
                    "parts": [
                        {
                            "function_response": {
                                "name": msg.get("name", "tool_result"),
                                "response": {"result": msg["content"]},
                            }
                        }
                    ],
                }
            )

    # Convert tools to Gemini format
    gemini_tools = []
    for tool in tools:
        func = tool["function"]
        # Clean parameters recursively to remove fields Gemini doesn't accept
        params = clean_schema_for_gemini(func["parameters"])

        gemini_tools.append(
            FunctionDeclaration(
                name=func["name"], description=func["description"], parameters=params
            )
        )

    config = GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        tools=[GeminiTool(function_declarations=gemini_tools)],
    )

    if system_instruction:
        config.system_instruction = system_instruction

    response = client.models.generate_content(
        model=model, contents=gemini_messages, config=config
    )

    # Convert Gemini response to OpenAI format
    class AssistantMessage:
        def __init__(self):
            self.content = None
            self.tool_calls = None

    assistant_msg = AssistantMessage()

    # Check if response has valid content
    if (
        not response.candidates
        or not response.candidates[0].content
        or not response.candidates[0].content.parts
    ):
        # Handle blocked or error responses
        error_msg = "Response blocked or empty."
        if response.candidates and hasattr(response.candidates[0], "finish_reason"):
            error_msg = (
                f"Response finish reason: {response.candidates[0].finish_reason}"
            )
        if hasattr(response, "prompt_feedback"):
            error_msg += f" Prompt feedback: {response.prompt_feedback}"
        raise ValueError(f"Gemini API error: {error_msg}")

    # Extract text and function calls
    text_parts = []
    tool_calls = []

    for part in response.candidates[0].content.parts:
        if hasattr(part, "text") and part.text:
            text_parts.append(part.text)
        elif hasattr(part, "function_call"):
            # Convert to OpenAI tool call format
            import uuid

            class ToolCall:
                def __init__(self, name, arguments):
                    self.id = f"call_{uuid.uuid4().hex[:24]}"
                    self.type = "function"
                    self.function = type(
                        "obj",
                        (object,),
                        {"name": name, "arguments": json.dumps(dict(arguments))},
                    )()

                def model_dump(self):
                    return {
                        "id": self.id,
                        "type": self.type,
                        "function": {
                            "name": self.function.name,
                            "arguments": self.function.arguments,
                        },
                    }

            tool_calls.append(
                ToolCall(part.function_call.name, part.function_call.args)
            )

    assistant_msg.content = "\n".join(text_parts) if text_parts else None
    assistant_msg.tool_calls = tool_calls if tool_calls else None

    return assistant_msg


def _together_with_tools(
    model: str, messages: list, tools: list, temperature: float, max_tokens: int
):
    """Together AI tool calling implementation"""
    client = Together()

    kwargs = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "temperature": temperature,
    }

    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message

    # Special handling for certain models which put tool calls in reasoning field
    if hasattr(message, "reasoning") and message.reasoning:
        # Parse XML-like tool call format from reasoning field
        reasoning = message.reasoning

        # Check if it contains tool calls
        if "<|tool_calls_section_begin|>" in reasoning:
            import re
            import uuid

            # Extract all tool calls from reasoning
            tool_call_pattern = r"<\|tool_call_begin\|>\s*(\S+):(\d+)\s*<\|tool_call_argument_begin\|>\s*(\{[^}]*\})\s*<\|tool_call_end\|>"
            matches = re.findall(tool_call_pattern, reasoning, re.DOTALL)

            if matches:
                # Build tool_calls list
                parsed_tool_calls = []

                class ToolCall:
                    def __init__(self, tool_name, arguments_json):
                        self.id = f"functions.{tool_name}:{uuid.uuid4().hex[:4]}"
                        self.type = "function"
                        self.function = type(
                            "obj",
                            (object,),
                            {
                                "name": (
                                    tool_name.split(".")[-1]
                                    if "." in tool_name
                                    else tool_name
                                ),
                                "arguments": arguments_json,
                            },
                        )()

                    def model_dump(self):
                        return {
                            "id": self.id,
                            "type": self.type,
                            "function": {
                                "name": self.function.name,
                                "arguments": self.function.arguments,
                            },
                        }

                for tool_name, call_id, arguments in matches:
                    try:
                        # Validate JSON
                        json.loads(arguments)
                        parsed_tool_calls.append(ToolCall(tool_name, arguments))
                    except json.JSONDecodeError:
                        # Skip malformed tool calls
                        continue

                if parsed_tool_calls:
                    message.tool_calls = parsed_tool_calls

    return message


def main():
    print("This is model_manager.py")


if __name__ == "__main__":
    main()
