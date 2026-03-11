#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.0",
# ]
# ///
"""CLI template following clig.dev guidelines.

Rename this file and customize for your use case.
"""

import signal
import sys

import click


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    click.echo("\nInterrupted. Cleaning up...", err=True)
    sys.exit(130)


signal.signal(signal.SIGINT, signal_handler)


@click.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.option("-o", "--output", type=click.Path(), help="Output file (default: stdout)")
@click.option("-v", "--verbose", is_flag=True, help="Show detailed output")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.version_option(version="1.0.0")
def cli(input_file, output, verbose, output_json):
    r"""Process INPUT_FILE and transform it.

    If INPUT_FILE is omitted or -, read from stdin.

    \b
    Examples:
      mycli data.txt
      mycli data.txt -o result.txt
      cat data.txt | mycli -
      mycli --json < data.txt
    """
    # Read input
    try:
        if input_file and input_file != "-":
            with open(input_file) as f:
                content = f.read()
        else:
            content = sys.stdin.read()
    except (FileNotFoundError, PermissionError, OSError) as e:
        click.secho(f"Error reading input: {e}", fg="red", err=True)
        sys.exit(1)

    if verbose:
        click.secho("Processing...", fg="cyan", err=True)

    # Process (customize this)
    result = content.upper()

    # Output
    if output_json:
        import json

        data = {"result": result, "length": len(result)}
        output_text = json.dumps(data)
    else:
        output_text = result

    if output:
        try:
            with open(output, "w") as f:
                f.write(output_text)
            if verbose:
                click.secho(f"✓ Written to {output}", fg="green", err=True)
        except (PermissionError, OSError) as e:
            click.secho(f"Error writing output: {e}", fg="red", err=True)
            sys.exit(1)
    else:
        click.echo(output_text)


if __name__ == "__main__":
    cli()
