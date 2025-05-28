import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import click

from boilersync.commands.init import init
from boilersync.paths import paths


def diff() -> None:
    """Show differences between current project and its template.

    Creates a temporary directory with a fresh template initialization,
    then copies the current project files over it to show differences.

    Raises:
        FileNotFoundError: If no .boilersync file is found
        subprocess.CalledProcessError: If git or github commands fail
    """
    # Find the root directory (where .boilersync file is located)
    root_dir = paths.root_dir
    boilersync_file = paths.boilersync_json_path

    # Read the template name from .boilersync file
    try:
        with open(boilersync_file, "r", encoding="utf-8") as f:
            boilersync_data = json.load(f)
        template_name = boilersync_data["template"]
        project_name = boilersync_data.get("name_snake")
        pretty_name = boilersync_data.get("name_pretty")
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        raise FileNotFoundError(
            f"Could not read template name from {boilersync_file}: {e}"
        )

    click.echo(f"🔍 Creating diff for template '{template_name}'...")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        project_temp_dir = temp_dir / "project"
        project_temp_dir.mkdir()

        # Change to temp directory and run init
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(project_temp_dir)

            # Run init command in temp directory with saved project names
            click.echo("📦 Initializing fresh template in temporary directory...")
            init(template_name, project_name, pretty_name)

            # Initialize git repo
            click.echo("🔧 Setting up git repository...")
            subprocess.run(
                ["git", "init"], cwd=project_temp_dir, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "add", "."],
                cwd=project_temp_dir,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"Fresh template: {template_name}"],
                cwd=project_temp_dir,
                check=True,
                capture_output=True,
            )

            # Copy files from root directory to temp directory, overwriting
            click.echo("📋 Copying current project files...")
            copy_project_files(root_dir, project_temp_dir)

            # Open in GitHub Desktop
            click.echo("🚀 Opening in GitHub Desktop...")
            subprocess.run(["github", str(project_temp_dir)], check=True)

            # Keep the process alive so the temp directory doesn't get cleaned up immediately
            click.echo("📂 Temporary directory created and opened in GitHub Desktop.")
            click.echo("⏳ Press Enter when you're done reviewing the diff...")
            input()

        finally:
            os.chdir(original_cwd)


def copy_project_files(source_dir: Path, target_dir: Path) -> None:
    """Copy files from source to target, preserving structure and overwriting.

    Args:
        source_dir: Source directory (current project)
        target_dir: Target directory (temp directory with fresh template)
    """
    for item in source_dir.rglob("*"):
        if item.is_file():
            # Skip .boilersync file and git files
            if item.name in [".boilersync", ".git"] or ".git/" in str(
                item.relative_to(source_dir)
            ):
                continue

            # Calculate relative path and target location
            rel_path = item.relative_to(source_dir)
            target_file = target_dir / rel_path

            # Create parent directories if they don't exist
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(item, target_file)


@click.command(name="diff")
def diff_cmd():
    """Show differences between current project and its template.

    Creates a temporary directory with a fresh template initialization,
    then copies the current project files over it to show differences in GitHub Desktop.
    """
    diff()
