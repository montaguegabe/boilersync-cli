from typing import Set

import click
from jinja2 import Environment, meta

from boilersync.interpolation_context import interpolation_context


def extract_variables_from_template_content(content: str) -> Set[str]:
    """Extract all variables used in a template string.

    Args:
        content: Template content with Jinja2 syntax

    Returns:
        Set of variable names found in the template
    """
    try:
        # Create a Jinja2 environment with our custom delimiters
        env = Environment(
            block_start_string="$${%",
            block_end_string="%}",
            variable_start_string="$${",
            variable_end_string="}",
            comment_start_string="$${#",
            comment_end_string="#}",
        )

        # Parse the template and find undeclared variables
        ast = env.parse(content)
        variables = meta.find_undeclared_variables(ast)
        return variables
    except Exception:
        # If parsing fails, return empty set
        return set()


def collect_missing_variables(template_variables: Set[str]) -> None:
    """Collect any missing variables from the user.

    Args:
        template_variables: Variables found in template content
    """
    missing_variables = []

    for var in template_variables:
        if not interpolation_context.has_variable(var):
            missing_variables.append(var)

    if missing_variables:
        click.echo("\n🔧 Additional variables needed for this template:")
        click.echo("=" * 50)

        for var in sorted(missing_variables):
            # Provide helpful prompts based on variable name patterns
            prompt_text = f"Enter value for '{var}'"

            if var.lower().endswith("_name"):
                prompt_text += " (name)"
            elif var.lower().endswith("_url"):
                prompt_text += " (URL)"
            elif var.lower().endswith("_email"):
                prompt_text += " (email address)"
            elif var.lower().endswith("_version"):
                prompt_text += " (version number)"
            elif var.lower().endswith("_description"):
                prompt_text += " (description)"

            value = click.prompt(prompt_text, type=str)
            interpolation_context.set_collected_variable(var, value)

        click.echo("=" * 50)
        click.echo("✅ All variables collected!\n")
