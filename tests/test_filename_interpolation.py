"""
Test filename interpolation functionality.
"""

from boilersync.template_processor import interpolate_path_name


def test_interpolate_path_name_only_name_variables():
    """Test that interpolate_path_name only interpolates uppercase NAME_* variables."""
    context = {
        "NAME_SNAKE": "my_project",
        "NAME_PASCAL": "MyProject",
        "NAME_KEBAB": "my-project",
        "NAME_CAMEL": "myProject",
        "NAME_PRETTY": "My Project",
        "publish": "1",
        "debug": "true",
        "author_name": "John Doe",
        "name_snake": "my_project",  # lowercase version
    }

    # Test that NAME_* variables are interpolated
    result = interpolate_path_name("NAME_SNAKE_service.py", context)
    assert result == "my_project_service.py"

    result = interpolate_path_name("NAME_PASCAL/", context)
    assert result == "MyProject/"

    result = interpolate_path_name("docs/NAME_KEBAB-guide.md", context)
    assert result == "docs/my-project-guide.md"

    # Test that non-NAME_* variables are NOT interpolated in filenames
    result = interpolate_path_name("publish.yml", context)
    assert result == "publish.yml"  # Should NOT become "1.yml"

    result = interpolate_path_name("debug.config", context)
    assert result == "debug.config"  # Should NOT become "true.config"

    result = interpolate_path_name("author_name.txt", context)
    assert result == "author_name.txt"  # Should NOT become "John Doe.txt"

    # Test that lowercase name variables are NOT interpolated in filenames
    result = interpolate_path_name("name_snake_test.py", context)
    assert result == "name_snake_test.py"  # Should NOT become "my_project_test.py"


def test_interpolate_path_name_mixed_variables():
    """Test filename with both NAME_* and other variables."""
    context = {"NAME_SNAKE": "awesome_app", "publish": "0", "version": "1.0.0"}

    # Only NAME_* should be interpolated
    result = interpolate_path_name("NAME_SNAKE_publish_version.py", context)
    assert result == "awesome_app_publish_version.py"


def test_interpolate_path_name_no_variables():
    """Test filename with no variables to interpolate."""
    context = {"NAME_SNAKE": "test_project", "publish": "1"}

    result = interpolate_path_name("regular_file.txt", context)
    assert result == "regular_file.txt"


def test_interpolate_path_name_empty_context():
    """Test filename interpolation with empty context."""
    result = interpolate_path_name("NAME_SNAKE_file.py", {})
    assert result == "NAME_SNAKE_file.py"  # Should remain unchanged
