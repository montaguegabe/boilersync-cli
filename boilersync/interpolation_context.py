from pathlib import Path
from typing import Any, Dict

from boilersync.names import ProjectNames, create_project_names, normalize_to_snake


class InterpolationContext:
    """Context for template interpolation with project names and other variables."""

    def __init__(self):
        self._names: ProjectNames | None = None
        self._custom_vars: Dict[str, Any] = {}
        self._collected_vars: Dict[str, Any] = {}  # Variables collected from user input

    def set_project_name_from_directory(self, directory: Path) -> None:
        """Set project names based on a directory name.

        Args:
            directory: Directory whose name will be used for the project
        """
        project_name = directory.name
        snake_name = normalize_to_snake(project_name)
        self._names = create_project_names(snake_name)

    def set_project_names(self, snake_name: str, pretty_name: str) -> None:
        """Set project names from user input.

        Args:
            snake_name: Project name in snake_case
            pretty_name: Pretty display name
        """
        self._names = create_project_names(snake_name, pretty_name)

    def set_custom_variable(self, key: str, value: Any) -> None:
        """Set a custom variable for interpolation.

        Args:
            key: Variable name
            value: Variable value
        """
        self._custom_vars[key] = value

    def set_collected_variable(self, key: str, value: Any) -> None:
        """Set a variable that was collected from user input.

        Args:
            key: Variable name
            value: Variable value from user input (can be string, bool, int, float, etc.)
        """
        self._collected_vars[key] = value

    def get_context(self) -> Dict[str, Any]:
        """Get the complete interpolation context.

        Returns:
            Dictionary with all interpolation variables including:
            - Uppercase variables for file/folder names (NAME_SNAKE, NAME_PASCAL, etc.)
            - Lowercase variables for file contents (name_snake, name_pascal, etc.)
            - Custom variables
            - User-collected variables
        """
        context = {}

        # Add project names if available
        if self._names:
            # Uppercase variables for file/folder names (no special symbols)
            context.update(
                {
                    "NAME_SNAKE": self._names.snake,
                    "NAME_PASCAL": self._names.pascal,
                    "NAME_KEBAB": self._names.kebab,
                    "NAME_CAMEL": self._names.camel,
                    "NAME_PRETTY": self._names.pretty,
                }
            )

            # Lowercase variables for file contents (used with Jinja2 delimiters)
            context.update(
                {
                    "name_snake": self._names.snake,
                    "name_pascal": self._names.pascal,
                    "name_kebab": self._names.kebab,
                    "name_camel": self._names.camel,
                    "name_pretty": self._names.pretty,
                }
            )

        # Add custom variables
        context.update(self._custom_vars)

        # Add user-collected variables
        context.update(self._collected_vars)

        return context

    def has_variable(self, key: str) -> bool:
        """Check if a variable is available in the context.

        Args:
            key: Variable name to check

        Returns:
            True if the variable is available, False otherwise
        """
        return key in self.get_context()

    @property
    def names(self) -> ProjectNames | None:
        """Get the current project names."""
        return self._names

    def clear(self) -> None:
        """Clear all context variables."""
        self._names = None
        self._custom_vars.clear()
        self._collected_vars.clear()

    def get_collected_variables(self) -> Dict[str, Any]:
        """Get all variables that were collected from user input.

        Returns:
            Dictionary of collected variables
        """
        return self._collected_vars.copy()

    def set_collected_variables(self, variables: Dict[str, Any]) -> None:
        """Set multiple collected variables at once.

        Args:
            variables: Dictionary of variable names and values
        """
        self._collected_vars.update(variables)


# Global instance for use throughout the application
interpolation_context = InterpolationContext()
