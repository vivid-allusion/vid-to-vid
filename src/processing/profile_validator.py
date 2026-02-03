"""Profile validation utilities."""

from pathlib import Path
from typing import Dict, Any, List
from ..exceptions import ProfileValidationError


class ProfileValidator:
    """Generic profile validator with configurable sections."""

    @staticmethod
    def validate_section(
        profile_data: Dict[str, Any],
        yaml_file: Path,
        section_name: str,
        required_fields: List[str],
    ) -> Dict[str, Any]:
        """
        Generic section validator.

        Args:
            profile_data: Profile data dictionary
            yaml_file: Path to YAML file for error messages
            section_name: Name of section to validate
            required_fields: List of required field names

        Returns:
            Validated section data

        Raises:
            ProfileValidationError: If section missing or invalid
        """
        if section_name not in profile_data:
            raise ProfileValidationError(
                f"Profile {yaml_file} is missing '{section_name}' section. "
                f"Required fields: {', '.join(required_fields)}"
            )

        section = profile_data[section_name]

        for field in required_fields:
            if field not in section:
                raise ProfileValidationError(
                    f"Profile {yaml_file} is missing '{section_name}.{field}' field."
                )

        return section

    @staticmethod
    def validate_model_section(
        profile_data: Dict[str, Any], yaml_file: Path
    ) -> Dict[str, Any]:
        """Validate and extract model section from profile."""
        return ProfileValidator.validate_section(
            profile_data, yaml_file, "Model", ["endpoint"]
        )

    @staticmethod
    def validate_pricing_section(
        profile_data: Dict[str, Any], yaml_file: Path
    ) -> Dict[str, Any]:
        """Validate and extract pricing section from profile."""
        if "pricing" not in profile_data:
            raise ProfileValidationError(
                f"Profile {yaml_file} is missing 'pricing' section. "
                f"Must specify cost_per_second for motion control pricing."
            )

        pricing = profile_data["pricing"]

        pricing_fields = ["cost_per_frame", "cost_per_second", "cost_per_prediction"]
        if not any(field in pricing for field in pricing_fields):
            raise ProfileValidationError(
                f"Profile {yaml_file} must have at least one pricing field: "
                f"{', '.join(pricing_fields)}"
            )

        return pricing

    @staticmethod
    def validate_params_section(
        profile_data: Dict[str, Any], yaml_file: Path
    ) -> Dict[str, Any]:
        """Validate params section exists."""
        if "params" not in profile_data:
            raise ProfileValidationError(
                f"Profile {yaml_file} is missing 'params' section. "
                f"Must specify generation parameters."
            )
        return profile_data["params"]

    @staticmethod
    def validate_prompt_modifications(
        profile_data: Dict[str, Any], yaml_file: Path
    ) -> tuple:
        """
        Validate optional prompt_prefix and prompt_suffix fields.

        Args:
            profile_data: Profile data dictionary
            yaml_file: Path to YAML file for error messages

        Returns:
            Tuple of (prompt_prefix, prompt_suffix) - both can be None or str

        Raises:
            ProfileValidationError: If prefix/suffix is not str or None
        """
        prompt_prefix = profile_data.get("prompt_prefix", None)
        prompt_suffix = profile_data.get("prompt_suffix", None)

        # Type validation - must be string or None
        if prompt_prefix is not None and not isinstance(prompt_prefix, str):
            raise ProfileValidationError(
                f"Profile {yaml_file} has invalid prompt_prefix. "
                f"Must be a string or omitted, got {type(prompt_prefix).__name__}"
            )

        if prompt_suffix is not None and not isinstance(prompt_suffix, str):
            raise ProfileValidationError(
                f"Profile {yaml_file} has invalid prompt_suffix. "
                f"Must be a string or omitted, got {type(prompt_suffix).__name__}"
            )

        return prompt_prefix, prompt_suffix
