import json
from pathlib import Path
from typing import Any

import click

from boilersync.interpolation_context import interpolation_context
from boilersync.names import normalize_to_snake, snake_to_pretty
from boilersync.paths import paths
from boilersync.template_processor import process_template_directory


def pull(
    template_name: str,
    project_name: str | None = None,
    pretty_name: str | None = None,
    collected_variables: dict[str, Any] | None = None,
) -> None:
    """Pull template/boilerplate changes to the current project.

    Args:
        template_name: Name of the template to use from the boilerplate directory
        project_name: Optional predefined project name (snake_case)
        pretty_name: Optional predefined pretty name
        collected_variables: Optional pre-collected variables to restore

    Raises:
        FileNotFoundError: If the template directory doesn't exist
        FileExistsError: If the target directory is not empty
    """
    template_dir = paths.boilerplate_dir / template_name
    if not template_dir.exists():
        raise FileNotFoundError(
            f"Template '{template_name}' not found in {paths.boilerplate_dir}"
        )

    target_dir = Path.cwd()
    # Check if directory has any files besides .DS_Store
    has_files = any(p for p in target_dir.iterdir() if p.name != ".DS_Store")
    if has_files:
        raise FileExistsError("Target directory is not empty")

    # If project names are provided, use them; otherwise prompt user
    if project_name is not None and pretty_name is not None:
        snake_name = project_name
        final_pretty_name = pretty_name
        click.echo(f"\n🚀 Initializing project from template '{template_name}'")
        click.echo(f"📝 Using saved project name: {snake_name}")
        click.echo(f"📝 Using saved pretty name: {final_pretty_name}")
    else:
        # Get the default snake_case name from the directory
        directory_name = target_dir.name
        default_snake_name = normalize_to_snake(directory_name)
        default_pretty_name = snake_to_pretty(default_snake_name)

        # Prompt user for project names
        click.echo(f"\n🚀 Initializing project from template '{template_name}'")
        click.echo("=" * 50)

        snake_name = click.prompt(
            "Project name (snake_case)", default=default_snake_name, type=str
        )

        final_pretty_name = click.prompt(
            "Pretty name for display", default=default_pretty_name, type=str
        )

        click.echo("=" * 50)

    # Set up interpolation context with project names
    interpolation_context.set_project_names(snake_name, final_pretty_name)

    # Restore any pre-collected variables
    if collected_variables:
        interpolation_context.set_collected_variables(collected_variables)

    # Process the template directory with interpolation
    process_template_directory(template_dir, target_dir)

    # Get all collected variables to save them
    collected_variables = interpolation_context.get_collected_variables()

    # Create .boilersync file to track the template
    boilersync_file = target_dir / ".boilersync"
    boilersync_data = {
        "template": template_name,
        "name_snake": snake_name,
        "name_pretty": final_pretty_name,
        "variables": collected_variables,
    }

    with open(boilersync_file, "w", encoding="utf-8") as f:
        json.dump(boilersync_data, f, indent=2)

    click.echo(
        f"\n✅ Project initialized successfully from template '{template_name}'!"
    )
    click.echo("📁 Created .boilersync file to track template origin")


@click.command(name="pull")
@click.argument("template_name")
def pull_cmd(template_name: str):
    """Pull template/boilerplate changes to the current project.

    TEMPLATE_NAME is the name of the template directory in the boilerplate directory.
    """
    pull(template_name)
