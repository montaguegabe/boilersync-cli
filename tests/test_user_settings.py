"""
Test user settings functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from boilersync.user_settings import UserSettings


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_user_settings_initialization_new_file(temp_config_file):
    """Test UserSettings initialization with a new config file."""
    # Remove the temp file so we test with a truly non-existent file
    temp_config_file.unlink()

    with patch("boilersync.user_settings.paths.user_config_path", temp_config_file):
        settings = UserSettings()

        # Should have default structure
        assert settings.get_all_recent_variables() == {}

        # Config file should not exist yet (only created on first save)
        assert not temp_config_file.exists()

        # Save a variable to trigger file creation
        settings.save_variable_value("test", "value")

        # Now config file should be created
        assert temp_config_file.exists()

        # Should contain the saved variable
        with open(temp_config_file, "r") as f:
            config = json.load(f)
        assert config == {"recent_variables": {"test": "value"}}


def test_user_settings_load_existing_file(temp_config_file):
    """Test UserSettings loading from an existing config file."""
    # Create a config file with some data
    config_data = {
        "recent_variables": {
            "author_name": "John Doe",
            "author_email": "john@example.com",
        }
    }

    with open(temp_config_file, "w") as f:
        json.dump(config_data, f)

    with patch("boilersync.user_settings.paths.user_config_path", temp_config_file):
        settings = UserSettings()

        # Should load existing data
        assert settings.get_recent_variable_value("author_name") == "John Doe"
        assert settings.get_recent_variable_value("author_email") == "john@example.com"
        assert settings.get_recent_variable_value("nonexistent") is None


def test_save_and_retrieve_variable(temp_config_file):
    """Test saving and retrieving a single variable."""
    with patch("boilersync.user_settings.paths.user_config_path", temp_config_file):
        settings = UserSettings()

        # Save a variable
        settings.save_variable_value("test_var", "test_value")

        # Should be able to retrieve it
        assert settings.get_recent_variable_value("test_var") == "test_value"

        # Should persist to file
        with open(temp_config_file, "r") as f:
            config = json.load(f)
        assert config["recent_variables"]["test_var"] == "test_value"


def test_save_multiple_variables(temp_config_file):
    """Test saving multiple variables at once."""
    with patch("boilersync.user_settings.paths.user_config_path", temp_config_file):
        settings = UserSettings()

        # Save multiple variables
        variables = {
            "author_name": "Jane Doe",
            "author_email": "jane@example.com",
            "project_version": "1.0.0",
        }
        settings.save_multiple_variables(variables)

        # Should be able to retrieve all of them
        for var_name, var_value in variables.items():
            assert settings.get_recent_variable_value(var_name) == var_value

        # Should get all variables
        all_vars = settings.get_all_recent_variables()
        assert all_vars == variables


def test_clear_recent_variables(temp_config_file):
    """Test clearing all recent variables."""
    with patch("boilersync.user_settings.paths.user_config_path", temp_config_file):
        settings = UserSettings()

        # Add some variables
        settings.save_multiple_variables({"var1": "value1", "var2": "value2"})

        # Clear them
        settings.clear_recent_variables()

        # Should be empty
        assert settings.get_all_recent_variables() == {}
        assert settings.get_recent_variable_value("var1") is None


def test_general_settings(temp_config_file):
    """Test general setting functionality."""
    with patch("boilersync.user_settings.paths.user_config_path", temp_config_file):
        settings = UserSettings()

        # Test setting and getting general settings
        settings.set_setting("theme", "dark")
        settings.set_setting("auto_save", True)

        assert settings.get_setting("theme") == "dark"
        assert settings.get_setting("auto_save") is True
        assert settings.get_setting("nonexistent") is None
        assert settings.get_setting("nonexistent", "default") == "default"


def test_corrupted_config_file(temp_config_file):
    """Test handling of corrupted config file."""
    # Write invalid JSON
    with open(temp_config_file, "w") as f:
        f.write("invalid json content")

    with patch("boilersync.user_settings.paths.user_config_path", temp_config_file):
        # Should handle gracefully and use defaults
        settings = UserSettings()
        assert settings.get_all_recent_variables() == {}


def test_config_file_permissions_error(temp_config_file):
    """Test handling of file permission errors."""
    with patch("boilersync.user_settings.paths.user_config_path", temp_config_file):
        settings = UserSettings()

        # Mock a permission error on save
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Should not raise an exception
            settings.save_variable_value("test", "value")

            # Value should still be in memory but not persisted
            assert settings.get_recent_variable_value("test") == "value"
