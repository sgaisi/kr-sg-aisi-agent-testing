"""
Utility to combine trajectory and judgement data into a single combined file.

This module provides the function to combine trajectory and judgement data
after judgement is complete, saving directly to judgement_results.

The combined output files use the same naming convention as judgement_results
(e.g., judgement_1_1_[MODEL NAME]_25_12_03_12_24.json).
"""

import json
import os
from datetime import datetime


# Default directory
JUDGEMENT_RESULTS_DIR = "judgement_results"


def get_judgement_filename_from_traj(
    traj_filename: str, prompt_type: str = "sg"
) -> str:
    """Convert trajectory filename to judgement filename with prompt prefix.

    Example: traj_1_1_[MODEL NAME]_25_12_03_12_24.json -> sg_judgement_1_1_[MODEL NAME]_25_12_03_12_24.json
    """
    return traj_filename.replace("traj_", f"{prompt_type}_judgement_")


def combine_trajectory_and_judgement(traj_data: dict, judgement_data: dict) -> dict:
    """Combine trajectory and judgement data into a single structure.

    Args:
        traj_data: The trajectory JSON data
        judgement_data: The judgement JSON data

    Returns:
        Combined dictionary with trajectory and judgement data
    """
    combined = {
        "metadata": {
            "scenario_id": judgement_data.get(
                "scenario_id", traj_data.get("scenario_id")
            ),
            "scenario_filename": judgement_data.get("scenario_filename"),
            "traj_filename": judgement_data.get("traj_filename"),
            "model": traj_data.get("model"),
            "combined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "trajectory": {
            "total_steps": traj_data.get("total_steps"),
            "max_steps": traj_data.get("max_steps"),
            "conversation_history": traj_data.get("conversation_history", []),
        },
        "judgement": {
            "correctness": judgement_data.get("correctness", {}),
            "safety": judgement_data.get("safety", {}),
        },
    }

    return combined


def combine_and_save_from_data(
    traj_path: str,
    traj_data: dict,
    judgement_data: dict,
    output_dir: str = JUDGEMENT_RESULTS_DIR,
    overwrite: bool = False,
    prompt_type: str = "sg",
) -> str | None:
    """Combine trajectory and judgement data directly and save to file.

    This function is used after judgement is complete to save the combined file
    directly without first saving a separate judgement file.

    Args:
        traj_path: Path to the trajectory file (used to derive output filename)
        traj_data: The trajectory data dict
        judgement_data: The judgement data dict
        output_dir: Directory to save combined file (default: judgement_results)
        overwrite: Whether to overwrite existing combined files
        prompt_type: Prompt type prefix for filename ('sg' or 'kr')

    Returns:
        Path to the combined file, or None if skipped/failed
    """
    traj_filename = os.path.basename(traj_path)
    judgement_filename = get_judgement_filename_from_traj(traj_filename, prompt_type)
    output_path = os.path.join(output_dir, judgement_filename)

    if os.path.exists(output_path) and not overwrite:
        print(f"Skipping (already exists): {output_path}")
        return None

    combined = combine_trajectory_and_judgement(traj_data, judgement_data)

    os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"Created: {output_path}")
    return output_path
