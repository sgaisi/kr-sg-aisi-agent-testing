import json
import openai
import boto3
from google import genai
from together import Together
import dotenv

dotenv.load_dotenv(override=True)

DEFAULT_AWS_REGION_NAME = "us-east-2"


def get_all_available_models(save_to_file=True, verbose=False):
    if verbose:
        print("AVAILABLE MODELS (Active API Access Only)")

    all_models = {"openai": [], "bedrock": [], "gemini": [], "together": []}

    if verbose:
        print("\nOpenAI Models:")
    try:
        client = openai.OpenAI()
        models_response = client.models.list()
        openai_models = []
        for model in models_response.data:
            if any(x in model.id for x in ["gpt", "o1"]):
                openai_models.append(model.id)

        openai_models.sort()
        all_models["openai"] = openai_models

        if verbose:
            if openai_models:
                for i, model in enumerate(openai_models, 1):
                    print(f"{i}. {model}")
            else:
                print("No models found")
    except Exception as e:
        if verbose:
            print(f"No access - Error: {str(e)}")

    if verbose:
        print("\nAWS Bedrock Models:")
    try:
        bedrock = boto3.client("bedrock", region_name=DEFAULT_AWS_REGION_NAME)
        response = bedrock.list_foundation_models()
        bedrock_models = []
        for model in response.get("modelSummaries", []):
            model_id = model.get("modelId")
            if model_id:
                bedrock_models.append(model_id)

        bedrock_models.sort()
        all_models["bedrock"] = bedrock_models

        if verbose:
            if bedrock_models:
                for i, model_id in enumerate(bedrock_models, 1):
                    print(f"{i}. {model_id}")
            else:
                print("No models found")
    except Exception as e:
        if verbose:
            print(f"No access - Error: {str(e)}")

    if verbose:
        print("\nGoogle Gemini Models:")
    try:
        client = genai.Client()
        models_response = client.models.list()
        gemini_models = []
        for model in models_response:
            if hasattr(model, "name"):
                model_name = model.name.replace("models/", "")
                if "gemini" in model_name.lower():
                    gemini_models.append(model_name)

        gemini_models.sort()
        all_models["gemini"] = gemini_models

        if verbose:
            if gemini_models:
                for i, model in enumerate(gemini_models, 1):
                    print(f"{i}. {model}")
            else:
                print("No Gemini models found")
    except Exception as e:
        if verbose:
            print(f"No access - Error: {str(e)}")

    if verbose:
        print("\nTogether AI Models:")
    try:
        client = Together()
        models_response = client.models.list()
        together_models = []
        for model in models_response:
            if hasattr(model, "id"):
                together_models.append(model.id)

        together_models.sort()
        all_models["together"] = together_models

        if verbose:
            if together_models:
                for i, model in enumerate(together_models, 1):
                    print(f"{i}. {model}")
            else:
                print("No models found")
    except Exception as e:
        if verbose:
            print(f"No access - Error: {str(e)}")

    if save_to_file:
        with open("util/all_models.json", "w") as f:
            json.dump(all_models, f, indent=2)
        if verbose:
            print("\nSaved all models to all_models.json")

    return all_models


if __name__ == "__main__":
    get_all_available_models()
