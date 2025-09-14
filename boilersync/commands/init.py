import logging
from pathlib import Path

import click

from boilersync.commands.pull import pull
from boilersync.paths import paths

logger = logging.getLogger(__name__)


def init(
    template_name: str,
    current_dir: Path,
    collected_variables=None,
    project_name=None,
    no_input=False,
) -> None:
    """Initialize a new project from a template (empty directory only).

    Args:
        template_name: Name of the template to use from the boilerplate directory

    Raises:
        FileNotFoundError: If the template directory doesn't exist
        FileExistsError: If the target directory is not empty
    """

    # Check for parent .boilersync files before initializing
    parent_dir = paths.find_parent_boilersync(current_dir)

    # Initialize the project
    pull(
        template_name,
        allow_non_empty=False,
        include_starter=True,
        _recursive=False,
        collected_variables=collected_variables,
        current_dir=current_dir,
        project_name=project_name,
        no_input=no_input,
    )

    # If we found a parent .boilersync, register this project as a child
    if parent_dir is not None:
        parent_boilersync_path = parent_dir / ".boilersync"
        paths.add_child_to_parent(current_dir, parent_boilersync_path)
        logger.info(f"📎 Registered as child project in parent: {parent_dir}")


@click.command(name="init")
@click.argument("template_name")
@click.option("--no-input", is_flag=True, help="Do not prompt for input")
def init_cmd(template_name: str, no_input: bool = False):
    """Initialize a new project from a template (empty directory only).

    TEMPLATE_NAME is the name of the template directory in the boilerplate directory.
    This command only works in empty directories.
    """
    init(template_name, Path.cwd(), no_input=no_input)
