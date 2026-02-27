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
            template_root_dir = Path(tmp) / "templates"
            target_dir = template_root_dir / "acme" / "templates"
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                with patch(
                    "boilersync.commands.templates.click.prompt",
                    return_value="https://example.com/acme/templates.git",
                ) as mock_prompt:
                    with patch("boilersync.commands.templates.subprocess.run") as mock_run:
                        init_templates(repo_url=None, repo_url_option=None, no_input=False)

                mock_prompt.assert_called_once()
                mock_run.assert_called_once_with(
                    [
                        "git",
                        "clone",
                        "https://example.com/acme/templates.git",
                        str(template_root_dir / "acme" / "templates"),
                    ],
                    check=True,
                )

    def test_clones_to_env_override_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_root_dir = Path(tmp) / "nested" / "templates"
            target_dir = template_root_dir / "acme" / "templates"
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                with patch("boilersync.commands.templates.subprocess.run") as mock_run:
                    init_templates(repo_url="https://example.com/acme/templates.git")

            self.assertTrue(target_dir.parent.exists())
            mock_run.assert_called_once_with(
                [
                    "git",
                    "clone",
                    "https://example.com/acme/templates.git",
                    str(target_dir),
                ],
                check=True,
            )

    def test_skips_clone_when_template_source_already_initialized(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_root_dir = Path(tmp) / "templates"
            target_dir = template_root_dir / "acme" / "templates"
            (target_dir / ".git").mkdir(parents=True)
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                with patch("boilersync.commands.templates.subprocess.run") as mock_run:
                    init_templates(repo_url="https://example.com/acme/templates.git")

            mock_run.assert_not_called()

    def test_clones_org_repo_shorthand_to_github_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_root_dir = Path(tmp) / "templates"
            target_dir = template_root_dir / "acme" / "platform-templates"
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                with patch("boilersync.commands.templates.subprocess.run") as mock_run:
                    init_templates(repo_url="acme/platform-templates")

            mock_run.assert_called_once_with(
                [
                    "git",
                    "clone",
                    "https://github.com/acme/platform-templates.git",
                    str(target_dir),
                ],
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
