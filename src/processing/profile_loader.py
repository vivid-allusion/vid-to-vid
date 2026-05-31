"""Profile loading utilities."""

import yaml
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger
from natsort import natsorted

from .profile_validator import ProfileValidator
from ..exceptions import ProfileValidationError


def find_yaml_files(profiles_dir: Path) -> List[Path]:
    """Find all YAML files in the profiles directory."""
    yaml_files = list(profiles_dir.glob("*.yaml"))
    yaml_files.extend(profiles_dir.glob("*.yml"))
    return yaml_files


def load_single_profile(yaml_file: Path) -> Dict[str, Any]:
    """Load and validate a single profile from YAML file."""
    with open(yaml_file, "r") as f:
        profile_data = yaml.safe_load(f) or {}

    profile_name = yaml_file.stem
    validator = ProfileValidator()

    model_section = validator.validate_model_section(profile_data, yaml_file)
    pricing = validator.validate_pricing_section(profile_data, yaml_file)
    params = validator.validate_params_section(profile_data, yaml_file)

    image_url_param = profile_data.get("image_url", "image")

    if "generate_audio" in profile_data:
        params["generate_audio"] = profile_data["generate_audio"]

    prompt_prefix, prompt_suffix = validator.validate_prompt_modifications(
        profile_data, yaml_file
    )

    project_name = None
    custom_input_path = None
    custom_output_path = None

    if "project" in profile_data:
        project_config = profile_data["project"]
        if isinstance(project_config, dict):
            project_name = project_config.get("name", None)
        elif isinstance(project_config, str):
            project_name = project_config

    if "paths" in profile_data:
        paths_config = profile_data["paths"]
        if isinstance(paths_config, dict):
            if "input" in paths_config:
                custom_input_path = Path(paths_config["input"])
            if "output" in paths_config:
                custom_output_path = Path(paths_config["output"])

    profile = {
        "name": profile_name,
        "model_id": model_section["endpoint"],
        "nickname": model_section.get("code-nickname", profile_name),
        "pricing": pricing,
        "params": params,
        "image_url_param": image_url_param,
        "prompt_prefix": prompt_prefix,
        "prompt_suffix": prompt_suffix,
        "project_name": project_name,
        "custom_input_path": str(custom_input_path) if custom_input_path else None,
        "custom_output_path": str(custom_output_path) if custom_output_path else None,
    }

    logger.info(
        f"Loaded profile: {profile_name} (endpoint: {model_section['endpoint']})"
    )

    modifications = []
    if prompt_prefix and prompt_prefix.strip():
        modifications.append(f"prefix='{prompt_prefix.strip()}'")
    if prompt_suffix and prompt_suffix.strip():
        modifications.append(f"suffix='{prompt_suffix.strip()}'")

    if modifications:
        logger.info(f"  → Prompt modifications: {', '.join(modifications)}")

    if project_name:
        logger.info(f"  → Project: {project_name}")
    if custom_input_path:
        logger.info(f"  → Custom input: {custom_input_path}")
    if custom_output_path:
        logger.info(f"  → Custom output: {custom_output_path}")

    return profile


def load_active_profile(profiles_dir: Path) -> Dict[str, Any]:
    """
    Load the single active profile from the profiles directory.

    Expects exactly one YAML file in the directory. Errors if zero or multiple exist.

    Args:
        profiles_dir: Directory containing profile YAML files

    Returns:
        Single profile dictionary

    Raises:
        FileNotFoundError: If profiles directory doesn't exist
        ProfileValidationError: If no profiles found or multiple profiles found
    """
    if not profiles_dir.exists():
        raise FileNotFoundError(f"Profiles directory not found: {profiles_dir}")

    yaml_files = find_yaml_files(profiles_dir)

    if not yaml_files:
        raise ProfileValidationError(
            f"No profile files found in {profiles_dir}. "
            "Add exactly one profile YAML file to USER-FILES/03.PROFILES/"
        )

    if len(yaml_files) > 1:
        file_names = ", ".join(f.name for f in natsorted(yaml_files))
        raise ProfileValidationError(
            f"Expected 1 profile, found {len(yaml_files)}: {file_names}. "
            "Remove extra profiles from USER-FILES/03.PROFILES/"
        )

    yaml_file = yaml_files[0]

    try:
        profile = load_single_profile(yaml_file)
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {yaml_file}: {e}")
        raise

    logger.info(f"Loaded profile: {profile['name']}")
    return profile
