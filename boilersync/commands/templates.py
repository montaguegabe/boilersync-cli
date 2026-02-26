import subprocess
from pathlib import Path

import click

from boilersync.paths import paths


def init_templates(
    repo_url: str | None,
    repo_url_option: str | None = None,
    no_input: bool = False,
) -> None:
    """Initialize the local templates directory by cloning a templates repository."""
    if repo_url and repo_url_option:
        raise click.UsageError(
            "Provide either REPO_URL argument or --repo-url, not both."
        )

    final_repo_url = repo_url_option or repo_url
    if not final_repo_url:
        if no_input:
            raise click.ClickException(
                "Template repository URL is required when --no-input is used."
            )
        final_repo_url = click.prompt(
            "Template repository URL to clone into local templates directory",
            type=str,
        ).strip()
        if not final_repo_url:
            raise click.ClickException("Template repository URL cannot be empty.")

    target_dir = paths.boilerplate_dir
    target_parent = target_dir.parent
    target_parent.mkdir(parents=True, exist_ok=True)

    if target_dir.exists():
        if (target_dir / ".git").exists():
            click.echo(f"✅ Templates repository already initialized at: {target_dir}")
            return
        if any(target_dir.iterdir()):
            raise click.ClickException(
                f"Templates directory already exists and is not empty: {target_dir}"
            )

    click.echo(f"📦 Cloning templates repository into: {target_dir}")
    try:
        subprocess.run(["git", "clone", final_repo_url, str(target_dir)], check=True)
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"Failed to clone templates repository: {e}") from e
    click.echo("✅ Templates initialized successfully.")


@click.command(name="init")
@click.argument("repo_url", required=False)
@click.option(
    "--repo-url",
    "repo_url_option",
    help="Template repository URL to clone.",
)
@click.option("--no-input", is_flag=True, help="Do not prompt for input.")
def templates_init_cmd(
    repo_url: str | None,
    repo_url_option: str | None,
    no_input: bool,
) -> None:
    """Clone a templates repository into the configured templates directory.

    REPO_URL is optional. If omitted, Boilersync will prompt for it.
    """
    init_templates(
        repo_url=repo_url,
        repo_url_option=repo_url_option,
        no_input=no_input,
    )


@click.group(name="templates")
def templates_cmd() -> None:
    """Manage local templates directory configuration and setup."""
    pass


templates_cmd.add_command(templates_init_cmd)
