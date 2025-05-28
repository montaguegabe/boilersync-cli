import click

from boilersync._version import __version__
from boilersync.cli_helpers import common_command_wrapper
from boilersync.commands.init import init_cmd
from boilersync.commands.pull import pull_cmd
from boilersync.commands.push import push_cmd


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"cursor-multi {__version__}")
    ctx.exit()


@click.group()
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show the version and exit.",
)
def main():
    """BoilerSync - a boilerplate CLI tool that can not only generate projects from boilerplate templates, but keep the boilerplate "alive" and updated as you continue to develop the derivative projects."""
    pass


# Register commands
main.add_command(common_command_wrapper(init_cmd))
main.add_command(common_command_wrapper(pull_cmd))
main.add_command(common_command_wrapper(push_cmd))


if __name__ == "__main__":
    main()
