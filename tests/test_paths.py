import os
import unittest
from pathlib import Path
from unittest.mock import patch

from boilersync.paths import Paths


class TestPaths(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_template_root_dir_defaults_to_boilersync_templates(self):
        path_helper = Paths()
        expected = Path.home() / ".boilersync" / "templates"
        self.assertEqual(path_helper.template_root_dir, expected)

    @patch.dict(
        os.environ, {"BOILERSYNC_TEMPLATE_DIR": "~/custom-templates"}, clear=True
    )
    def test_template_root_dir_respects_env_override(self):
        path_helper = Paths()
        expected = Path.home() / "custom-templates"
        self.assertEqual(path_helper.template_root_dir, expected)


if __name__ == "__main__":
    unittest.main()
