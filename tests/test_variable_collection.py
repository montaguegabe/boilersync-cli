"""
Test variable collection functionality.
"""

import tempfile
from pathlib import Path

from boilersync.template_processor import scan_template_for_variables


def test_variable_collection_from_all_files():
    """Test that variables are collected from all files, not just .boilersync files."""

    # Create a temporary directory with test template files
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir)

        # Create a test file without .boilersync extension (like pyproject.toml)
        test_file = template_dir / "pyproject.toml"
        test_content = """[project]
name = "$${name_kebab}"
description = "$${description}"
authors = [{ name = "$${author_name}", email = "$${author_email}" }]
readme = "README.md"
requires-python = ">=$${python_version}"

[project.urls]
Repository = "https://github.com/$${author_github_name}/$${name_kebab}"
"""
        test_file.write_text(test_content)

        # Create another test file with .boilersync extension
        boilersync_file = template_dir / "config.json.boilersync"
        boilersync_content = """
{
    "app_name": "$${name_snake}",
    "version": "$${app_version}",
    "debug": $${debug_mode}
}
"""
        boilersync_file.write_text(boilersync_content)

        # Scan for variables
        variables = scan_template_for_variables(template_dir)

        # Expected variables from both files
        expected_variables = {
            "name_kebab",
            "description",
            "author_name",
            "author_email",
            "python_version",
            "author_github_name",
            "name_snake",
            "app_version",
            "debug_mode",
        }

        # Check that all expected variables were found
        assert variables == expected_variables, (
            f"Expected {expected_variables}, but got {variables}"
        )


def test_variable_collection_with_jinja_blocks():
    """Test that variables are collected from Jinja2 blocks and conditionals."""

    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir)

        # Create a test file with Jinja2 blocks
        test_file = template_dir / "template_with_blocks.txt"
        test_content = """
Base config: $${base_config}

$${% if enable_feature %}
Feature enabled with value: $${feature_value}
$${% endif %}

$${% block dependencies %}
Default dependency: $${default_dep}
$${% endblock %}

$${% for item in item_list %}
Item: $${item.name} - $${item.value}
$${% endfor %}
"""
        test_file.write_text(test_content)

        # Scan for variables
        variables = scan_template_for_variables(template_dir)

        # Expected variables (note: item_list, item are expected, but item.name and item.value
        # are attribute access, so only the base variables should be detected)
        expected_variables = {
            "base_config",
            "enable_feature",
            "feature_value",
            "default_dep",
            "item_list",
        }

        assert variables == expected_variables, (
            f"Expected {expected_variables}, but got {variables}"
        )


def test_variable_collection_ignores_binary_files():
    """Test that binary files are gracefully ignored during variable scanning."""

    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir)

        # Create a text file with variables
        text_file = template_dir / "config.txt"
        text_file.write_text("Config: $${config_value}")

        # Create a binary file (simulate with bytes that would cause encoding errors)
        binary_file = template_dir / "image.png"
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00")

        # Scan for variables - should not crash on binary file
        variables = scan_template_for_variables(template_dir)

        # Should only find variables from the text file
        expected_variables = {"config_value"}
        assert variables == expected_variables, (
            f"Expected {expected_variables}, but got {variables}"
        )


def test_variable_collection_empty_directory():
    """Test that scanning an empty directory returns empty set."""

    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir)

        # Scan empty directory
        variables = scan_template_for_variables(template_dir)

        assert variables == set(), f"Expected empty set, but got {variables}"


def test_variable_collection_no_variables():
    """Test that files without template variables return empty set."""

    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir)

        # Create files without any template variables
        file1 = template_dir / "plain.txt"
        file1.write_text("This is just plain text with no variables.")

        file2 = template_dir / "config.json"
        file2.write_text('{"name": "static_value", "version": "1.0.0"}')

        # Scan for variables
        variables = scan_template_for_variables(template_dir)

        assert variables == set(), f"Expected empty set, but got {variables}"
