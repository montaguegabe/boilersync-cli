import re
from typing import NamedTuple


class ProjectNames(NamedTuple):
    """Container for different naming conventions of a project name."""

    snake: str  # my_project_name
    pascal: str  # MyProjectName
    kebab: str  # my-project-name
    camel: str  # myProjectName
    pretty: str  # My Project Name


def detect_name_format(name: str) -> str:
    """Detect the format of a given name string.

    Args:
        name: The name string to analyze

    Returns:
        One of: 'snake', 'pascal', 'kebab', 'camel', 'unknown'
    """
    if "_" in name and name.islower():
        return "snake"
    elif "-" in name and name.islower():
        return "kebab"
    elif name[0].isupper() and any(c.isupper() for c in name[1:]):
        return "pascal"
    elif name[0].islower() and any(c.isupper() for c in name[1:]):
        return "camel"
    else:
        return "unknown"


def normalize_to_snake(name: str) -> str:
    """Convert any naming convention to snake_case.

    Args:
        name: Name in any convention

    Returns:
        Name in snake_case
    """
    # Handle kebab-case
    if "-" in name:
        return name.replace("-", "_").lower()

    # Handle camelCase and PascalCase
    # Insert underscore before uppercase letters (except the first character)
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    return snake


def snake_to_pascal(snake_name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in snake_name.split("_"))


def snake_to_kebab(snake_name: str) -> str:
    """Convert snake_case to kebab-case."""
    return snake_name.replace("_", "-")


def snake_to_camel(snake_name: str) -> str:
    """Convert snake_case to camelCase."""
    words = snake_name.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


def snake_to_pretty(snake_name: str) -> str:
    """Convert snake_case to Pretty Name."""
    return " ".join(word.capitalize() for word in snake_name.split("_"))


def create_project_names(
    snake_name: str, pretty_name: str | None = None
) -> ProjectNames:
    """Create all naming conventions from snake_case name and optional pretty name.

    Args:
        snake_name: Project name in snake_case
        pretty_name: Optional pretty display name, will be generated if not provided

    Returns:
        ProjectNames with all conventions populated
    """
    if pretty_name is None:
        pretty_name = snake_to_pretty(snake_name)

    return ProjectNames(
        snake=snake_name,
        pascal=snake_to_pascal(snake_name),
        kebab=snake_to_kebab(snake_name),
        camel=snake_to_camel(snake_name),
        pretty=pretty_name,
    )
