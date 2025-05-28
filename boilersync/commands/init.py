import click

from boilersync.commands.pull import pull


def init(template_name: str) -> None:
    """Initialize a new project from a template (empty directory only).

    Args:
        template_name: Name of the template to use from the boilerplate directory

    Raises:
        FileNotFoundError: If the template directory doesn't exist
        FileExistsError: If the target directory is not empty
    """
    pull(template_name, allow_non_empty=False)


@click.command(name="init")
@click.argument("template_name")
def init_cmd(template_name: str):
    """Initialize a new project from a template (empty directory only).

    TEMPLATE_NAME is the name of the template directory in the boilerplate directory.
    This command only works in empty directories.
    """
    init(template_name)
