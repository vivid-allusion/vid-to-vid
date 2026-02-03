"""Tests for cost calculator."""
import pytest
from src.processing.cost_calculator import (
    calculate_video_cost,
    calculate_motion_control_cost,
    _validate_numeric_field,
)


class TestValidateNumericField:
    """Tests for _validate_numeric_field function."""

    def test_valid_integer(self):
        """Test with valid integer value."""
        _validate_numeric_field(10, "test_field", "test_profile")

    def test_valid_float(self):
        """Test with valid float value."""
        _validate_numeric_field(10.5, "test_field", "test_profile")

    def test_zero_value(self):
        """Test with zero value (valid)."""
        _validate_numeric_field(0, "test_field", "test_profile")

    def test_negative_value(self):
        """Test with negative value (invalid)."""
        with pytest.raises(ValueError, match="invalid test_field"):
            _validate_numeric_field(-1, "test_field", "test_profile")


class TestCalculateVideoCost:
    """Tests for calculate_video_cost function."""

    def test_time_based_pricing(self):
        """Test time-based pricing model."""
        profile = {
            "name": "test_profile",
            "pricing": {"cost_per_second": 0.01}
        }
        cost = calculate_video_cost(profile, 100)
        assert cost == 1.0

    def test_missing_pricing_section(self):
        """Test with missing pricing section."""
        profile = {"name": "test_profile"}
        with pytest.raises(ValueError, match="missing pricing configuration"):
            calculate_video_cost(profile, 100)

    def test_no_cost_per_second(self):
        """Test with pricing section but no cost_per_second."""
        profile = {
            "name": "test_profile",
            "pricing": {"cost_per_frame": 0.001}
        }
        with pytest.raises(ValueError, match="must have 'cost_per_second'"):
            calculate_video_cost(profile, 100)


class TestCalculateMotionControlCost:
    """Tests for calculate_motion_control_cost function."""

    def test_motion_control_cost(self):
        """Test motion control cost calculation."""
        profile = {
            "name": "test_profile",
            "pricing": {"cost_per_second": 0.12},
            "default_duration": 5
        }
        cost = calculate_motion_control_cost(profile)
        assert cost == 0.6

    def test_motion_control_cost_default_duration(self):
        """Test with default duration when not specified."""
        profile = {
            "name": "test_profile",
            "pricing": {"cost_per_second": 0.10}
        }
        cost = calculate_motion_control_cost(profile)
        assert cost == 0.5

    def test_motion_control_missing_pricing(self):
        """Test motion control with missing pricing section."""
        profile = {"name": "test_profile"}
        with pytest.raises(ValueError, match="missing pricing configuration"):
            calculate_motion_control_cost(profile)
