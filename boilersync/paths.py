import json
import logging
import os
from functools import cached_property
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Paths:
    def root_dir(self) -> Path:
        return self._get_root()

    def boilersync_json_path(self) -> Path:
        return self.root_dir / ".boilersync"

    @cached_property
    def boilerplate_dir(self) -> Path:
        env_path = os.environ.get("BOILERSYNC_TEMPLATE_DIR", "")
        if env_path:
            return Path(env_path).expanduser()
        # Default to ~/boilerplate if not set
        return Path.home() / "boilerplate"

    @cached_property
    def user_config_path(self) -> Path:
        """Path to the user's global boilersync configuration file."""
        return Path.home() / ".boilersync_config"

    def find_parent_boilersync(
        self, start_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """Find the nearest parent directory containing .boilersync file.

        Args:
            start_dir: Directory to start searching from. Defaults to current working directory.

        Returns:
            Path to the parent directory containing .boilersync, or None if not found.
        """
        if start_dir is None:
            start_dir = Path.cwd()

        # Start from the parent of start_dir to avoid finding the same .boilersync
        current = start_dir.parent

        while True:
            if (current / ".boilersync").exists():
                return current

            if current.parent == current:  # Reached root directory
                return None

            current = current.parent

    def add_child_to_parent(
        self, child_path: Path, parent_boilersync_path: Path
    ) -> None:
        """Add a child project path to the parent's .boilersync file.

        Args:
            child_path: Absolute path to the child project directory
            parent_boilersync_path: Path to the parent's .boilersync file
        """
        try:
            # Read existing .boilersync file
            with open(parent_boilersync_path, "r", encoding="utf-8") as f:
                parent_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(
                f"Could not read parent .boilersync file at {parent_boilersync_path}"
            )
            return

        # Calculate relative path from parent to child
        parent_dir = parent_boilersync_path.parent
        try:
            relative_child_path = child_path.relative_to(parent_dir)
        except ValueError:
            logger.warning(
                f"Child path {child_path} is not relative to parent {parent_dir}"
            )
            return

        # Initialize children list if it doesn't exist
        if "children" not in parent_data:
            parent_data["children"] = []

        # Add child if not already present
        relative_path_str = str(relative_child_path)
        if relative_path_str not in parent_data["children"]:
            parent_data["children"].append(relative_path_str)

            # Write back to file
            with open(parent_boilersync_path, "w", encoding="utf-8") as f:
                json.dump(parent_data, f, indent=2)

            logger.info(
                f"Added child project '{relative_path_str}' to parent .boilersync"
            )

    def get_children_from_boilersync(self, boilersync_path: Path) -> list[Path]:
        """Get list of child project paths from a .boilersync file.

        Args:
            boilersync_path: Path to the .boilersync file

        Returns:
            List of absolute paths to child projects
        """
        try:
            with open(boilersync_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        children = data.get("children", [])
        parent_dir = boilersync_path.parent

        # Convert relative paths to absolute paths and filter existing directories
        child_paths = []
        for child_rel_path in children:
            child_abs_path = parent_dir / child_rel_path
            if child_abs_path.exists() and child_abs_path.is_dir():
                child_paths.append(child_abs_path)
            else:
                logger.warning(f"Child project path does not exist: {child_abs_path}")

        return child_paths

    def _get_root(self) -> Path:
        """Get the root directory by finding the first parent directory containing .boilersync.

        Returns:
            The absolute path to the root directory containing .boilersync.

        Raises:
            FileNotFoundError: If no .boilersync is found in any parent directory.
        """
        override_root_dir = os.getenv("BOILERSYNC_ROOT_DIR")
        if override_root_dir:
            return Path(override_root_dir)

        current = Path.cwd()

        while True:
            if (current / ".boilersync").exists():
                return current

            if current.parent == current:  # Reached root directory
                msg = "Could not find .boilersync in any parent directory"
                logger.error(msg)
                raise FileNotFoundError(msg)

            current = current.parent


# Global instance that can be mocked in tests
paths = Paths()
