import json
import os
import sys
import subprocess
from typing import List, Dict

from util.get_models import get_all_available_models

scenarios = [
    "1_1.json",
    "2_1.json",
    "3_1.json",
    "4_1.json",
    "5_1.json",
    "6_1.json",
]

runs_per_model = 10


def load_all_models() -> Dict[str, List[str]]:
    """Load all available models from all_models.json"""
    try:
        with open("util/all_models.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("all_models.json not found, generating all_models.json")
        return get_all_available_models()


def get_scenario_models(scenario_path: str) -> List[str]:
    """Get target models from a scenario file"""
    try:
        with open(scenario_path, "r", encoding="utf-8") as f:
            scenario_data = json.load(f)
        return scenario_data.get("target_models", [])
    except Exception as e:
        print(f"Error reading scenario {scenario_path}: {e}")
        return []


def run_scenario_on_model(scenario_path: str, model: str) -> bool:
    """Run a single scenario on a specific model"""
    try:
        print(f"Running scenario {os.path.basename(scenario_path)} on model {model}...")

        cmd = [sys.executable, "scenario_runner.py", scenario_path, "--model", model]

        result = subprocess.run(cmd, text=True, timeout=3000)  # 50 minute timeout

        if result.returncode == 0:
            print(
                f"Successfully completed {os.path.basename(scenario_path)} on {model}"
            )
            return True
        else:
            print(f"Failed to run {os.path.basename(scenario_path)} on {model}")
            print(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"Timeout running {os.path.basename(scenario_path)} on {model}")
        return False
    except Exception as e:
        print(f"Exception running {os.path.basename(scenario_path)} on {model}: {e}")
        return False


def main():
    print("Bilateral Testing Scenario Runner")
    print("=" * 50)

    total_runs = 0
    successful_runs = 0

    for scenario_file in scenarios:
        scenario_path = os.path.join("scenarios", scenario_file)

        if not os.path.exists(scenario_path):
            print(f"Warning: Scenario file {scenario_path} not found, skipping...")
            continue

        scenario_id = scenario_file.replace(".json", "")
        print(f"Processing scenario: {scenario_id}")

        scenario_models = get_scenario_models(scenario_path)
        if not scenario_models:
            print(f"  No target models found in {scenario_file}, skipping...")
            continue

        print(f"  Target models: {', '.join(scenario_models)}")

        for model in scenario_models:
            for _ in range(runs_per_model):
                total_runs += 1
                if run_scenario_on_model(scenario_path, model):
                    successful_runs += 1

        print()

    print("=" * 50)
    print("Execution Summary:")
    print(f"Total runs attempted: {total_runs}")
    print(f"Successful runs: {successful_runs}")
    print(f"Failed runs: {total_runs - successful_runs}")

    if successful_runs == total_runs:
        print("All scenario runs completed successfully!")
    elif successful_runs > 0:
        print("Some scenario runs failed. Check the logs above for details.")
    else:
        print("All scenario runs failed.")

    return 0 if successful_runs == total_runs else 1


if __name__ == "__main__":
    sys.exit(main())
