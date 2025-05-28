"""
Integration tests for variable collection with user settings.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from boilersync.interpolation_context import interpolation_context
from boilersync.template_processor import scan_template_for_variables
from boilersync.user_settings import UserSettings
from boilersync.variable_collector import collect_missing_variables


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)

    # Remove the file so we start with a clean slate
    temp_path.unlink()

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_user_settings(temp_config_file):
    """Create a mock user settings instance for testing."""
    with patch("boilersync.user_settings.paths.user_config_path", temp_config_file):
        settings = UserSettings()
        with patch("boilersync.variable_collector.user_settings", settings):
            yield settings


def test_variable_collection_uses_recent_values_as_defaults(mock_user_settings):
    """Test that variable collection uses recently saved values as defaults."""
    # Save some recent values
    mock_user_settings.save_multiple_variables(
        {
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "project_version": "1.0.0",
        }
    )

    # Clear interpolation context to ensure we're testing fresh
    interpolation_context.clear()
    interpolation_context.set_project_names("test_project", "Test Project")

    # Mock click.prompt to verify defaults are used
    # Note: Variables are processed in alphabetical order: author_email, author_name, project_version
    with patch("boilersync.variable_collector.click.prompt") as mock_prompt:
        # Set up mock to return the default values when called
        mock_prompt.side_effect = ["john@example.com", "John Doe", "2.0.0"]

        # Variables that need to be collected
        template_variables = {"author_name", "author_email", "project_version"}

        collect_missing_variables(template_variables)

        # Verify that click.prompt was called with the correct defaults
        assert mock_prompt.call_count == 3

        # Check that the calls included the recent values as defaults
        calls = mock_prompt.call_args_list

        # Find the call for author_name
        author_name_call = next(call for call in calls if "author_name" in str(call))
        assert author_name_call.kwargs.get("default") == "John Doe"

        # Find the call for author_email
        author_email_call = next(call for call in calls if "author_email" in str(call))
        assert author_email_call.kwargs.get("default") == "john@example.com"

        # Find the call for project_version
        version_call = next(call for call in calls if "project_version" in str(call))
        assert version_call.kwargs.get("default") == "1.0.0"


def test_variable_collection_saves_new_values(mock_user_settings):
    """Test that variable collection saves newly entered values."""
    # Clear interpolation context
    interpolation_context.clear()
    interpolation_context.set_project_names("test_project", "Test Project")

    # Mock click.prompt to return new values
    # Note: Variables are processed in alphabetical order: author_email, author_name, project_version
    with patch("boilersync.variable_collector.click.prompt") as mock_prompt:
        mock_prompt.side_effect = ["jane@example.com", "Jane Smith", "3.0.0"]

        # Variables that need to be collected
        template_variables = {"author_name", "author_email", "project_version"}

        collect_missing_variables(template_variables)

        # Verify that the new values were saved
        assert (
            mock_user_settings.get_recent_variable_value("author_name") == "Jane Smith"
        )
        assert (
            mock_user_settings.get_recent_variable_value("author_email")
            == "jane@example.com"
        )
        assert (
            mock_user_settings.get_recent_variable_value("project_version") == "3.0.0"
        )


def test_variable_collection_no_defaults_for_new_variables(mock_user_settings):
    """Test that new variables without recent values don't get defaults."""
    # Clear interpolation context
    interpolation_context.clear()
    interpolation_context.set_project_names("test_project", "Test Project")

    # Mock click.prompt
    with patch("boilersync.variable_collector.click.prompt") as mock_prompt:
        mock_prompt.side_effect = ["New Value", "Another Value"]

        # Variables that have never been used before
        template_variables = {"new_variable", "another_new_variable"}

        collect_missing_variables(template_variables)

        # Verify that click.prompt was called without defaults
        calls = mock_prompt.call_args_list

        for call in calls:
            # Should not have 'default' in kwargs for new variables
            assert "default" not in call.kwargs or call.kwargs.get("default") is None


def test_variable_collection_mixed_defaults(mock_user_settings):
    """Test variable collection with a mix of variables with and without defaults."""
    # Save some recent values (but not all)
    mock_user_settings.save_multiple_variables(
        {"author_name": "Existing User", "author_email": "existing@example.com"}
    )

    # Clear interpolation context
    interpolation_context.clear()
    interpolation_context.set_project_names("test_project", "Test Project")

    # Mock click.prompt
    # Note: Variables are processed in alphabetical order: author_email, author_name, description
    with patch("boilersync.variable_collector.click.prompt") as mock_prompt:
        mock_prompt.side_effect = [
            "existing@example.com",
            "Existing User",
            "New Description",
        ]

        # Mix of variables - some with recent values, some without
        template_variables = {"author_name", "author_email", "description"}

        collect_missing_variables(template_variables)

        # Verify the correct number of calls
        assert mock_prompt.call_count == 3

        calls = mock_prompt.call_args_list

        # Variables with recent values should have defaults
        author_name_call = next(call for call in calls if "author_name" in str(call))
        assert author_name_call.kwargs.get("default") == "Existing User"

        author_email_call = next(call for call in calls if "author_email" in str(call))
        assert author_email_call.kwargs.get("default") == "existing@example.com"

        # New variable should not have a default
        description_call = next(call for call in calls if "description" in str(call))
        assert (
            "default" not in description_call.kwargs
            or description_call.kwargs.get("default") is None
        )


def test_end_to_end_variable_collection_with_template(mock_user_settings):
    """Test end-to-end variable collection from template scanning to user settings."""
    # Create a temporary template directory
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir)

        # Create a template file with variables
        template_file = template_dir / "config.toml"
        template_content = """
[project]
name = "$${name_kebab}"
author = "$${author_name}"
email = "$${author_email}"
version = "$${project_version}"
"""
        template_file.write_text(template_content)

        # Set up interpolation context with project names
        interpolation_context.clear()
        interpolation_context.set_project_names("my_project", "My Project")

        # Scan template for variables
        template_variables = scan_template_for_variables(template_dir)

        # Should find the custom variables (not the predefined project name variables)
        expected_custom_vars = {"author_name", "author_email", "project_version"}
        custom_vars = template_variables - {"name_kebab"}  # Remove predefined variable
        assert custom_vars == expected_custom_vars

        # Mock user input
        # Note: Variables are processed in alphabetical order: author_email, author_name, project_version
        with patch("boilersync.variable_collector.click.prompt") as mock_prompt:
            mock_prompt.side_effect = ["test@example.com", "Test Author", "1.0.0"]

            # Collect missing variables
            collect_missing_variables(template_variables)

            # Verify variables were saved to user settings
            assert (
                mock_user_settings.get_recent_variable_value("author_name")
                == "Test Author"
            )
            assert (
                mock_user_settings.get_recent_variable_value("author_email")
                == "test@example.com"
            )
            assert (
                mock_user_settings.get_recent_variable_value("project_version")
                == "1.0.0"
            )

            # Verify variables are available in interpolation context
            context = interpolation_context.get_context()
            assert context["author_name"] == "Test Author"
            assert context["author_email"] == "test@example.com"
            assert context["project_version"] == "1.0.0"
