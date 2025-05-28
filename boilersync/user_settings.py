"""
User settings management for boilersync.

Handles saving and loading recently-used variable definitions from a global
configuration file in the user's home directory.
"""

import json
import logging
from typing import Any, Dict, Optional

from boilersync.paths import paths

logger = logging.getLogger(__name__)


class UserSettings:
    """Manages user settings and recently-used variable definitions."""

    def __init__(self):
        self._config_path = paths.user_config_path
        self._settings: Dict[str, Any] = {}
        self._load_settings()

    def _load_settings(self) -> None:
        """Load settings from the user config file."""
        try:
            if self._config_path.exists() and self._config_path.stat().st_size > 0:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
                logger.debug(f"Loaded user settings from {self._config_path}")
            else:
                self._settings = {"recent_variables": {}}
                logger.debug(
                    "No user config file found or file is empty, using defaults"
                )
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load user settings: {e}, using defaults")
            self._settings = {"recent_variables": {}}

    def _save_settings(self) -> None:
        """Save settings to the user config file."""
        try:
            # Ensure the parent directory exists
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
            logger.debug(f"Saved user settings to {self._config_path}")
        except OSError as e:
            logger.error(f"Failed to save user settings: {e}")

    def get_recent_variable_value(self, variable_name: str) -> Optional[str]:
        """Get the most recently used value for a variable.

        Args:
            variable_name: Name of the variable to look up

        Returns:
            The most recent value for the variable, or None if not found
        """
        recent_vars = self._settings.get("recent_variables", {})
        return recent_vars.get(variable_name)

    def save_variable_value(self, variable_name: str, value: str) -> None:
        """Save a variable value as recently used.

        Args:
            variable_name: Name of the variable
            value: Value to save
        """
        if "recent_variables" not in self._settings:
            self._settings["recent_variables"] = {}

        self._settings["recent_variables"][variable_name] = value
        self._save_settings()
        logger.debug(f"Saved recent variable: {variable_name} = {value}")

    def save_multiple_variables(self, variables: Dict[str, str]) -> None:
        """Save multiple variable values as recently used.

        Args:
            variables: Dictionary of variable names to values
        """
        if "recent_variables" not in self._settings:
            self._settings["recent_variables"] = {}

        self._settings["recent_variables"].update(variables)
        self._save_settings()
        logger.debug(f"Saved {len(variables)} recent variables")

    def get_all_recent_variables(self) -> Dict[str, str]:
        """Get all recently used variables.

        Returns:
            Dictionary of variable names to their most recent values
        """
        return self._settings.get("recent_variables", {}).copy()

    def clear_recent_variables(self) -> None:
        """Clear all recently used variables."""
        self._settings["recent_variables"] = {}
        self._save_settings()
        logger.debug("Cleared all recent variables")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a general setting value.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return self._settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a general setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        self._settings[key] = value
        self._save_settings()


# Global instance for use throughout the application
user_settings = UserSettings()
