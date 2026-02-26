import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import click

from boilersync.commands.templates import init_templates


class TestTemplatesInit(unittest.TestCase):
    def test_raises_when_repo_arg_and_option_are_both_provided(self):
        with self.assertRaises(click.UsageError):
            init_templates(
                repo_url="https://example.com/from-arg.git",
                repo_url_option="https://example.com/from-option.git",
            )

    def test_raises_when_no_url_and_no_input(self):
        with self.assertRaises(click.ClickException):
            init_templates(repo_url=None, repo_url_option=None, no_input=True)

    def test_prompts_for_url_when_not_supplied(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_dir = Path(tmp) / "templates"
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_dir)},
                clear=True,
            ):
                with patch(
                    "boilersync.commands.templates.click.prompt",
                    return_value="https://example.com/templates.git",
                ) as mock_prompt:
                    with patch("boilersync.commands.templates.subprocess.run") as mock_run:
                        init_templates(repo_url=None, repo_url_option=None, no_input=False)

                mock_prompt.assert_called_once()
                mock_run.assert_called_once_with(
                    [
                        "git",
                        "clone",
                        "https://example.com/templates.git",
                        str(template_dir),
                    ],
                    check=True,
                )

    def test_clones_to_env_override_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_dir = Path(tmp) / "nested" / "templates"
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_dir)},
                clear=True,
            ):
                with patch("boilersync.commands.templates.subprocess.run") as mock_run:
                    init_templates(repo_url="https://example.com/templates.git")

            self.assertTrue(template_dir.parent.exists())
            mock_run.assert_called_once_with(
                [
                    "git",
                    "clone",
                    "https://example.com/templates.git",
                    str(template_dir),
                ],
                check=True,
            )

    def test_skips_clone_when_templates_repo_already_initialized(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_dir = Path(tmp) / "templates"
            (template_dir / ".git").mkdir(parents=True)
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_dir)},
                clear=True,
            ):
                with patch("boilersync.commands.templates.subprocess.run") as mock_run:
                    init_templates(repo_url="https://example.com/templates.git")

            mock_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
