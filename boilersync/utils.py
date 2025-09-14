import click


def prompt_or_default(*args, **kwargs) -> str:
    """Prompt the user for input or return the default value."""
    no_input = kwargs.pop("no_input")
    default = kwargs["default"]
    if no_input:
        return default
    else:
        return click.prompt(*args, **kwargs)
