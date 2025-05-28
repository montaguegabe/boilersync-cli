from typing import Any, Dict, Set

import click
from jinja2 import Environment, meta

from boilersync.interpolation_context import interpolation_context
from boilersync.user_settings import user_settings


def create_jinja_environment(loader=None) -> Environment:
    """Create a Jinja2 environment with our custom delimiters.

    Args:
        loader: Optional Jinja2 loader (e.g., FileSystemLoader)

    Returns:
        Configured Jinja2 environment
    """
    return Environment(
        loader=loader,
        block_start_string="$${%",
        block_end_string="%}",
        variable_start_string="$${",
        variable_end_string="}",
        comment_start_string="$${#",
        comment_end_string="#}",
        autoescape=False,  # Don't escape content since we're not dealing with HTML
    )


def extract_variables_from_template_content(content: str) -> Set[str]:
    """Extract all variables used in a template string using Jinja2 meta API.

    Args:
        content: Template content with Jinja2 syntax

    Returns:
        Set of variable names found in the template
    """
    try:
        env = create_jinja_environment()
        # Parse the template and find undeclared variables using Jinja2 meta API
        ast = env.parse(content)
        variables = meta.find_undeclared_variables(ast)
        return variables
    except Exception:
        # If parsing fails, return empty set
        return set()


def convert_string_to_appropriate_type(value: str) -> Any:
    """Convert a string value to its most appropriate type for template processing.

    Args:
        value: String value from user input

    Returns:
        Converted value (bool, int, float, or original string)
    """
    # Strip whitespace for all conversions
    stripped_value = value.strip()
    lower_value = stripped_value.lower()

    # Handle boolean-like values
    if lower_value in ("true", "yes", "y", "1", "on", "enable", "enabled"):
        return True
    elif lower_value in ("false", "no", "n", "0", "off", "disable", "disabled", ""):
        return False

    # Handle numeric values
    try:
        # Try integer first
        if "." not in stripped_value:
            return int(stripped_value)
        else:
            return float(stripped_value)
    except ValueError:
        pass

    # Return as string if no conversion applies
    return value


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

        collected_variables: Dict[str, str] = {}

        for var in sorted(missing_variables):
            # Get recent value as default
            recent_value = user_settings.get_recent_variable_value(var)

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

            # Use recent value as default if available
            if recent_value:
                value = click.prompt(prompt_text, default=recent_value, type=str)
            else:
                value = click.prompt(prompt_text, type=str)

            # Convert the string value to appropriate type for template processing
            converted_value = convert_string_to_appropriate_type(value)
            interpolation_context.set_collected_variable(var, converted_value)
            collected_variables[var] = value  # Save original string for user settings

        # Save all collected variables to user settings
        if collected_variables:
            user_settings.save_multiple_variables(collected_variables)

        click.echo("=" * 50)
        click.echo("✅ All variables collected!\n")
