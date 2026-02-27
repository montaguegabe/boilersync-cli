import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from boilersync.template_sources import (
    SOURCE_RESOLUTION,
    build_source_backlink,
    parse_repo_locator,
    resolve_source_from_boilersync,
    resolve_template_source,
)


class TestTemplateSources(unittest.TestCase):
    def test_parse_repo_locator_org_repo(self):
        org, repo, clone_url = parse_repo_locator("acme/template-kit")
        self.assertEqual(org, "acme")
        self.assertEqual(repo, "template-kit")
        self.assertEqual(clone_url, "https://github.com/acme/template-kit.git")

    def test_parse_repo_locator_https(self):
        org, repo, clone_url = parse_repo_locator("https://github.com/acme/template-kit.git")
        self.assertEqual(org, "acme")
        self.assertEqual(repo, "template-kit")
        self.assertEqual(clone_url, "https://github.com/acme/template-kit.git")

    def test_parse_repo_locator_ssh(self):
        org, repo, clone_url = parse_repo_locator("git@github.com:acme/template-kit.git")
        self.assertEqual(org, "acme")
        self.assertEqual(repo, "template-kit")
        self.assertEqual(clone_url, "git@github.com:acme/template-kit.git")

    def test_resolve_legacy_template_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_root_dir = Path(tmp)
            (template_root_dir / "legacy-template").mkdir()
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                source = resolve_template_source("legacy-template", warn_on_legacy=False)

        self.assertEqual(source.resolution, "legacy_name")
        self.assertEqual(source.ref, "legacy-template")

    def test_resolve_legacy_template_ref_from_nested_repo_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_root_dir = Path(tmp)
            expected_dir = (
                template_root_dir / "openbase-community" / "templates" / "electron-app"
            )
            expected_dir.mkdir(parents=True)
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                source = resolve_template_source("electron-app", warn_on_legacy=False)

        self.assertEqual(source.resolution, "legacy_name")
        self.assertEqual(source.ref, "electron-app")
        self.assertEqual(source.template_dir, expected_dir)

    def test_resolve_legacy_template_ref_raises_when_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_root_dir = Path(tmp)
            (template_root_dir / "org-one" / "templates" / "electron-app").mkdir(
                parents=True
            )
            (template_root_dir / "org-two" / "templates" / "electron-app").mkdir(
                parents=True
            )
            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                with self.assertRaises(FileNotFoundError):
                    resolve_template_source("electron-app", warn_on_legacy=False)

    def test_resolve_source_ref_from_existing_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_root_dir = Path(tmp)
            local_repo = template_root_dir / "acme" / "template-kit"
            (local_repo / ".git").mkdir(parents=True)
            (local_repo / "python/service-template").mkdir(parents=True)

            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                source = resolve_template_source(
                    "acme/template-kit#python/service-template",
                    clone_missing_repo=False,
                )

        self.assertEqual(source.resolution, SOURCE_RESOLUTION)
        self.assertEqual(source.org, "acme")
        self.assertEqual(source.repo, "template-kit")
        self.assertEqual(source.subdir, "python/service-template")

    def test_resolve_source_from_boilersync(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_root_dir = Path(tmp)
            local_repo = template_root_dir / "acme" / "template-kit"
            (local_repo / ".git").mkdir(parents=True)
            (local_repo / "python/service-template").mkdir(parents=True)

            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                source = resolve_source_from_boilersync(
                    template_ref="legacy-template",
                    source_data={
                        "ref": "acme/template-kit#python/service-template",
                    },
                    clone_missing_repo=False,
                )

        self.assertEqual(source.ref, "acme/template-kit#python/service-template")
        self.assertEqual(source.template_dir, local_repo / "python/service-template")

    def test_build_source_backlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_root_dir = Path(tmp)
            local_repo = template_root_dir / "acme" / "template-kit"
            (local_repo / ".git").mkdir(parents=True)
            (local_repo / "python/service-template").mkdir(parents=True)

            with patch.dict(
                os.environ,
                {"BOILERSYNC_TEMPLATE_DIR": str(template_root_dir)},
                clear=True,
            ):
                source = resolve_template_source(
                    "acme/template-kit#python/service-template",
                    clone_missing_repo=False,
                )

        backlink = build_source_backlink(source)
        self.assertIsNotNone(backlink)
        assert backlink is not None
        self.assertEqual(backlink["org"], "acme")
        self.assertEqual(backlink["repo"], "template-kit")
        self.assertEqual(backlink["subdir"], "python/service-template")


if __name__ == "__main__":
    unittest.main()
