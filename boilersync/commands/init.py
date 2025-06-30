from pathlib import Path

import click

from boilersync.commands.pull import pull
from boilersync.names import normalize_to_snake, snake_to_pretty
from boilersync.paths import paths


def init(template_name: str, current_dir: Path, no_input: bool = False) -> None:
    """Initialize a new project from a template (empty directory only).

    Args:
        template_name: Name of the template to use from the boilerplate directory
        current_dir: Directory to initialize the project in
        no_input: If True, auto-generate project names to avoid interactive prompts

    Raises:
        FileNotFoundError: If the template directory doesn't exist
        FileExistsError: If the target directory is not empty
    """

    # Check for parent .boilersync files before initializing
    parent_dir = paths.find_parent_boilersync(current_dir)

    if no_input:
        # Generate project names from directory name to avoid prompts
        directory_name = current_dir.name
        project_name = normalize_to_snake(directory_name)
        pretty_name = snake_to_pretty(project_name)

        # Initialize the project with project names to avoid interactive prompts
        pull(
            template_name,
            project_name=project_name,
            pretty_name=pretty_name,
            allow_non_empty=False,
            include_starter=True,
            _recursive=False,
        )
    else:
        # Initialize the project with interactive prompts (default behavior)
        pull(
            template_name, allow_non_empty=False, include_starter=True, _recursive=False
        )

    # If we found a parent .boilersync, register this project as a child
    if parent_dir is not None:
        parent_boilersync_path = parent_dir / ".boilersync"
        paths.add_child_to_parent(current_dir, parent_boilersync_path)
        click.echo(f"📎 Registered as child project in parent: {parent_dir}")


@click.command(name="init")
@click.argument("template_name")
def init_cmd(template_name: str):
    """Initialize a new project from a template (empty directory only).

    TEMPLATE_NAME is the name of the template directory in the boilerplate directory.
    This command only works in empty directories.
    """
    init(template_name, Path.cwd())
