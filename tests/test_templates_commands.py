import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from boilersync.commands.init import parse_key_value_options
from boilersync.commands.templates import get_template_details, list_local_templates


def _write_template(
    template_root_dir: Path,
    *,
    org: str,
    repo: str,
    subdir: str,
    files: dict[str, str],
    config: dict[str, object] | None = None,
) -> None:
    repo_dir = template_root_dir / org / repo
    template_dir = repo_dir / subdir
    (repo_dir / ".git").mkdir(parents=True, exist_ok=True)
    template_dir.mkdir(parents=True, exist_ok=True)

    if config is not None:
        (template_dir / "template.json").write_text(
            json.dumps(config),
            encoding="utf-8",
        )

    for relative_path, contents in files.items():
        output_path = template_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(contents, encoding="utf-8")


class TestTemplatesCommands(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.template_root_dir = Path(self.temp_dir.name) / "templates"
        self.template_root_dir.mkdir()
        self.env_patcher = patch.dict(
            os.environ,
            {"BOILERSYNC_TEMPLATE_DIR": str(self.template_root_dir)},
            clear=False,
        )
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    def test_list_local_templates_returns_source_refs(self) -> None:
        _write_template(
            self.template_root_dir,
            org="acme",
            repo="platform",
            subdir="python/service",
            files={"README.md.boilersync": "hello"},
            config={},
        )

        templates = list_local_templates()
        refs = {template["template_ref"] for template in templates}
        self.assertIn("acme/platform#python/service", refs)

    def test_get_template_details_returns_variables_and_options(self) -> None:
        _write_template(
            self.template_root_dir,
            org="acme",
            repo="platform",
            subdir="base",
            files={"README.md.boilersync": "Base $${company_name}\n"},
            config={},
        )
        _write_template(
            self.template_root_dir,
            org="acme",
            repo="platform",
            subdir="service",
            files={
                "main.py.boilersync": "tier = '$${service_tier}'\nname = '$${name_snake}'\n"
            },
            config={
                "extends": "acme/platform#base",
                "variables": {
                    "company_name": {
                        "description": "Company name",
                        "default": "Acme",
                    },
                    "region": {
                        "type": "string",
                        "choices": ["us", "eu"],
                        "default": "us",
                    },
                },
                "options": {
                    "with_ci": {
                        "type": "boolean",
                        "description": "Enable CI workflow",
                        "default": True,
                    }
                },
            },
        )

        details = get_template_details("acme/platform#service")
        variable_map = {item["name"]: item for item in details["variables"]}
        option_map = {item["name"]: item for item in details["options"]}

        self.assertIn("company_name", variable_map)
        self.assertFalse(variable_map["company_name"]["required"])
        self.assertIn("service_tier", variable_map)
        self.assertTrue(variable_map["service_tier"]["required"])
        self.assertIn("region", variable_map)
        self.assertEqual(variable_map["region"]["choices"], ["us", "eu"])
        self.assertNotIn("name_snake", variable_map)

        self.assertIn("with_ci", option_map)
        self.assertEqual(option_map["with_ci"]["type"], "boolean")
        self.assertTrue(option_map["with_ci"]["default"])

    def test_parse_key_value_options_converts_values(self) -> None:
        parsed = parse_key_value_options(("with_ci=true", "retries=3"))
        self.assertTrue(parsed["with_ci"])
        self.assertEqual(parsed["retries"], 3)


if __name__ == "__main__":
    unittest.main()
