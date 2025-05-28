import logging
import os
from functools import cached_property
from pathlib import Path

logger = logging.getLogger(__name__)


class Paths:
    @cached_property
    def root_dir(self) -> Path:
        return self._get_root()

    @cached_property
    def boilersync_json_path(self) -> Path:
        return self.root_dir / ".boilersync"

    @cached_property
    def boilerplate_dir(self) -> Path:
        return Path(
            "/Users/gabemontague/Dropbox/Mac/Documents/Documents/Developer/code/boilerplate/"
        )

    @cached_property
    def user_config_path(self) -> Path:
        """Path to the user's global boilersync configuration file."""
        return Path.home() / ".boilersync_config"

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
