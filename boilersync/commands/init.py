import logging
from pathlib import Path
from typing import Any

import click

from boilersync.commands.pull import pull
from boilersync.paths import paths
from boilersync.variable_collector import convert_string_to_appropriate_type

logger = logging.getLogger(__name__)


def init(
    template_name: str,
    target_dir: Path,
    collected_variables: dict[str, Any] | None = None,
    project_name: str | None = None,
    pretty_name: str | None = None,
    no_input: bool = False,
) -> None:
    """Initialize a new project from a template (empty directory only).

    Args:
        template_name: Name of the template to use from the boilerplate directory

    Raises:
        FileNotFoundError: If the template directory doesn't exist
        FileExistsError: If the target directory is not empty
    """

    # Check for parent .boilersync files before initializing
    parent_dir = paths.find_parent_boilersync(target_dir)

    # Initialize the project
    pull(
        template_name,
        allow_non_empty=False,
        include_starter=True,
        _recursive=False,
        collected_variables=collected_variables,
        target_dir=target_dir,
        project_name=project_name,
        pretty_name=pretty_name,
        no_input=no_input,
    )

    # If we found a parent .boilersync, register this project as a child
    if parent_dir is not None:
        parent_boilersync_path = parent_dir / ".boilersync"
        paths.add_child_to_parent(target_dir, parent_boilersync_path)
        logger.info(f"📎 Registered as child project in parent: {parent_dir}")


def parse_var(ctx, param, value: tuple[str, ...]) -> dict[str, Any]:
    """Parse --var options into a dictionary."""
    result: dict[str, Any] = {}
    for item in value:
        if "=" not in item:
            raise click.BadParameter(
                f"Variable must be in KEY=VALUE format, got: {item}"
            )
        key, val = item.split("=", 1)
        result[key.strip()] = convert_string_to_appropriate_type(val)
    return result


@click.command(name="init")
@click.argument("template_name")
@click.option(
    "-n",
    "--name",
    "project_name",
    help="Project name in snake_case (defaults to directory name)",
)
@click.option(
    "--pretty-name",
    help="Pretty display name for the project",
)
@click.option(
    "-v",
    "--var",
    "variables",
    multiple=True,
    callback=parse_var,
    help="Template variable in KEY=VALUE format (can be used multiple times)",
)
@click.option("--no-input", is_flag=True, help="Do not prompt for input (use defaults)")
def init_cmd(
    template_name: str,
    project_name: str | None,
    pretty_name: str | None,
    variables: dict[str, Any],
    no_input: bool,
):
    """Initialize a new project from a template (empty directory only).

    TEMPLATE_NAME is the name of the template directory in the boilerplate directory.
    This command only works in empty directories.

    For non-interactive usage, provide --name and any required template variables:

    \b
      boilersync init my-template --name my_project --var author_name="John Doe"
    """
    init(
        template_name,
        target_dir=Path.cwd(),
        project_name=project_name,
        pretty_name=pretty_name,
        collected_variables=variables if variables else None,
        no_input=no_input,
    )
