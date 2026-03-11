# Python CLI Patterns

Python implementations of clig.dev guidelines using Click, Typer, and argparse.

## Table of Contents

- [Recommended Libraries](#recommended-libraries)
- [Quick Comparison](#quick-comparison)
- [Click Examples](#click-examples): Basic CLI, Subcommands, Progress Bars, Colors and Styling, Reading from Stdin, JSON Output, Environment Variables, Testing
- [Typer Examples](#typer-examples): Basic CLI, Subcommands, Progress Bars
- [Argparse Examples](#argparse-examples): Basic CLI, Subcommands
- [Common Patterns](#common-patterns): SIGINT Handling, Stdin or File, Color Detection, Configuration Loading, PEP 723

## Recommended Libraries

**Click** - Most popular, decorator-based, mature
**Typer** - Modern, type-hint based, built on Click
**argparse** - Standard library, good for simple CLIs

## Quick Comparison

| Feature | Click | Typer | argparse |
|---------|-------|-------|----------|
| Install | pip install click | pip install typer | stdlib |
| Style | Decorators | Type hints | Imperative |
| Subcommands | Excellent | Excellent | Good |
| Help generation | Automatic | Automatic | Manual |
| Testing | click.testing | typer.testing | unittest |

## Click Examples

### Basic CLI

```python
#!/usr/bin/env python3
import click
import sys
from pathlib import Path

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-f', '--force', is_flag=True, help='Overwrite existing files')
@click.version_option(version='1.0.0')
def process(input_file, output, verbose, force):
    """Process INPUT_FILE and transform it.
    
    Examples:
      mycli data.txt
      mycli data.txt -o result.txt
      mycli data.txt --verbose --force
    """
    if verbose:
        click.echo(f"Processing {input_file}...", err=True)
    
    try:
        with open(input_file) as f:
            content = f.read()
        
        result = content.upper()  # Example transformation
        
        if output:
            if not force and Path(output).exists():
                click.echo(f"Error: {output} exists. Use --force to overwrite", err=True)
                sys.exit(1)
            with open(output, 'w') as f:
                f.write(result)
            if verbose:
                click.echo(f"Written to {output}", err=True)
        else:
            click.echo(result)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    process()
```

### Subcommands

```python
import click

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """My awesome CLI tool."""
    pass

@cli.command()
@click.option('--name', prompt='Project name', help='Name of the project')
def init(name):
    """Initialize a new project."""
    click.echo(f"Initializing {name}...")
    # Implementation

@cli.command()
@click.option('--release', is_flag=True, help='Build in release mode')
def build(release):
    """Build the project."""
    mode = "release" if release else "debug"
    click.echo(f"Building in {mode} mode...")
    # Implementation

@cli.command()
@click.argument('environment', type=click.Choice(['dev', 'staging', 'prod']))
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def deploy(environment, yes):
    """Deploy to ENVIRONMENT."""
    if not yes:
        if not click.confirm(f'Deploy to {environment}?'):
            click.echo('Cancelled')
            return
    
    click.echo(f"Deploying to {environment}...")
    # Implementation

if __name__ == '__main__':
    cli()
```

### Progress Bars

```python
import click
import time

@click.command()
@click.argument('count', type=int)
def process(count):
    """Process COUNT items with progress bar."""
    with click.progressbar(
        range(count),
        label='Processing',
        show_eta=True,
        show_percent=True
    ) as bar:
        for item in bar:
            # Do work
            time.sleep(0.1)
    
    click.secho('✓ Done!', fg='green')

# Alternative: Manual updates
@click.command()
def download():
    """Download with custom progress."""
    with click.progressbar(length=100, label='Downloading') as bar:
        for i in range(100):
            time.sleep(0.05)
            bar.update(1)
```

### Colors and Styling

```python
import click

@click.command()
def status():
    """Show colorful status."""
    click.secho('✓ Success', fg='green')
    click.secho('⚠ Warning', fg='yellow')
    click.secho('✗ Error', fg='red', bold=True)
    click.secho('Info', fg='cyan')
    
    # Respect NO_COLOR
    if click.get_text_stream('stdout').isatty():
        click.echo(click.style('Styled', fg='blue', bold=True))
```

### Reading from Stdin

```python
import click
import sys

@click.command()
@click.argument('input_file', type=click.File('r'), default='-')
@click.option('-o', '--output', type=click.File('w'), default='-')
def transform(input_file, output):
    """Transform INPUT_FILE (or stdin) to OUTPUT (or stdout)."""
    for line in input_file:
        transformed = line.upper()
        output.write(transformed)
```

### JSON Output

```python
import click
import json

@click.command()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def stats(output_json):
    """Show statistics."""
    data = {
        'files': 42,
        'size': 1024,
        'duration': 2.5
    }
    
    if output_json:
        click.echo(json.dumps(data))
    else:
        click.echo(f"Files: {data['files']}")
        click.echo(f"Size: {data['size']} bytes")
        click.echo(f"Duration: {data['duration']}s")
```

### Environment Variables

```python
import click

@click.command()
@click.option('--api-key', envvar='MYCLI_API_KEY', help='API key')
@click.option('--debug', envvar='MYCLI_DEBUG', is_flag=True, help='Debug mode')
def api_call(api_key, debug):
    """Make API call with key from --api-key or $MYCLI_API_KEY."""
    if not api_key:
        click.echo('Error: API key required', err=True)
        click.echo('Set MYCLI_API_KEY or use --api-key', err=True)
        sys.exit(1)
    
    if debug:
        click.echo(f"Using API key: {api_key[:8]}...", err=True)
```

### Testing with Click

```python
from click.testing import CliRunner
import pytest

def test_basic_command():
    runner = CliRunner()
    result = runner.invoke(process, ['test.txt'])
    assert result.exit_code == 0
    assert 'Processing' in result.output

def test_with_isolated_filesystem():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test.txt', 'w') as f:
            f.write('hello')
        
        result = runner.invoke(process, ['test.txt', '-o', 'out.txt'])
        assert result.exit_code == 0
        assert Path('out.txt').exists()
```

## Typer Examples

### Basic CLI

```python
#!/usr/bin/env python3
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer()

def version_callback(value: bool):
    if value:
        typer.echo("1.0.0")
        raise typer.Exit()

@app.command()
def process(
    input_file: Path = typer.Argument(..., exists=True, help="Input file to process"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output file"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite existing"),
    version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, is_eager=True)
):
    """
    Process INPUT_FILE and transform it.
    
    Examples:
      mycli data.txt
      mycli data.txt -o result.txt
    """
    if verbose:
        typer.secho(f"Processing {input_file}...", err=True, fg=typer.colors.CYAN)
    
    try:
        content = input_file.read_text()
        result = content.upper()
        
        if output:
            if output.exists() and not force:
                typer.secho(f"Error: {output} exists. Use --force", err=True, fg=typer.colors.RED)
                raise typer.Exit(1)
            output.write_text(result)
            if verbose:
                typer.secho(f"✓ Written to {output}", fg=typer.colors.GREEN)
        else:
            typer.echo(result)
    except Exception as e:
        typer.secho(f"Error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
```

### Subcommands

```python
import typer
from enum import Enum

app = typer.Typer()

class Environment(str, Enum):
    dev = "dev"
    staging = "staging"
    prod = "prod"

@app.command()
def init(name: str = typer.Option(..., prompt=True)):
    """Initialize a new project."""
    typer.echo(f"Initializing {name}...")

@app.command()
def build(release: bool = typer.Option(False, help="Build in release mode")):
    """Build the project."""
    mode = "release" if release else "debug"
    typer.echo(f"Building in {mode} mode...")

@app.command()
def deploy(
    environment: Environment,
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation")
):
    """Deploy to environment."""
    if not yes:
        confirmed = typer.confirm(f"Deploy to {environment.value}?")
        if not confirmed:
            typer.echo("Cancelled")
            raise typer.Exit()
    
    typer.echo(f"Deploying to {environment.value}...")

if __name__ == "__main__":
    app()
```

### Progress Bars

```python
import typer
import time

def process_with_progress(count: int):
    """Process with progress bar."""
    with typer.progressbar(
        range(count),
        label="Processing"
    ) as progress:
        for item in progress:
            time.sleep(0.1)
    
    typer.secho("✓ Done!", fg=typer.colors.GREEN)
```

## Argparse Examples

### Basic CLI

```python
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        prog='mycli',
        description='Process INPUT_FILE and transform it',
        epilog='Examples:\n'
               '  mycli data.txt\n'
               '  mycli data.txt -o result.txt',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('input_file', type=Path, help='Input file to process')
    parser.add_argument('-o', '--output', type=Path, help='Output file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite existing')
    parser.add_argument('--version', action='version', version='1.0.0')
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: {args.input_file} not found", file=sys.stderr)
        sys.exit(1)
    
    if args.verbose:
        print(f"Processing {args.input_file}...", file=sys.stderr)
    
    try:
        content = args.input_file.read_text()
        result = content.upper()
        
        if args.output:
            if args.output.exists() and not args.force:
                print(f"Error: {args.output} exists. Use --force", file=sys.stderr)
                sys.exit(1)
            args.output.write_text(result)
            if args.verbose:
                print(f"Written to {args.output}", file=sys.stderr)
        else:
            print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### Subcommands with Argparse

```python
import argparse
import sys

def cmd_init(args):
    """Initialize project."""
    print(f"Initializing {args.name}...")

def cmd_build(args):
    """Build project."""
    mode = "release" if args.release else "debug"
    print(f"Building in {mode} mode...")

def cmd_deploy(args):
    """Deploy project.""" 
    if not args.yes:
        response = input(f"Deploy to {args.environment}? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled")
            return
    print(f"Deploying to {args.environment}...")

def main():
    parser = argparse.ArgumentParser(prog='mycli')
    parser.add_argument('--version', action='version', version='1.0.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # init subcommand
    init_parser = subparsers.add_parser('init', help='Initialize a new project')
    init_parser.add_argument('--name', required=True, help='Project name')
    init_parser.set_defaults(func=cmd_init)
    
    # build subcommand
    build_parser = subparsers.add_parser('build', help='Build the project')
    build_parser.add_argument('--release', action='store_true', help='Build in release mode')
    build_parser.set_defaults(func=cmd_build)
    
    # deploy subcommand
    deploy_parser = subparsers.add_parser('deploy', help='Deploy to environment')
    deploy_parser.add_argument('environment', choices=['dev', 'staging', 'prod'])
    deploy_parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation')
    deploy_parser.set_defaults(func=cmd_deploy)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## Common Patterns

### Graceful SIGINT Handling

```python
import signal
import sys

def signal_handler(sig, frame):
    print('\nInterrupted. Cleaning up...', file=sys.stderr)
    # Cleanup code here
    sys.exit(130)  # 128 + SIGINT (2)

signal.signal(signal.SIGINT, signal_handler)
```

### Reading Stdin or File

```python
import sys

def read_input(filename=None):
    """Read from file or stdin if filename is None or '-'."""
    if filename and filename != '-':
        with open(filename) as f:
            return f.read()
    else:
        return sys.stdin.read()

# Usage
content = read_input(args.input_file)
```

### Color Support Detection

```python
import sys
import os

def supports_color():
    """Check if terminal supports color."""
    if os.environ.get('NO_COLOR'):
        return False
    if not hasattr(sys.stdout, 'isatty'):
        return False
    if not sys.stdout.isatty():
        return False
    return True

def colorize(text, color):
    """Colorize text if supported."""
    if not supports_color():
        return text
    
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
    }
    reset = '\033[0m'
    return f"{colors.get(color, '')}{text}{reset}"
```

### Configuration Loading

```python
import json
from pathlib import Path

def load_config():
    """Load config with priority: CLI args > env vars > config file > defaults."""
    config = {
        'api_key': None,
        'timeout': 30,
        'verbose': False
    }
    
    # 1. Load from config file
    config_path = Path.home() / '.config' / 'mycli' / 'config.json'
    if config_path.exists():
        with open(config_path) as f:
            file_config = json.load(f)
            config.update(file_config)
    
    # 2. Load from environment
    import os
    if api_key := os.environ.get('MYCLI_API_KEY'):
        config['api_key'] = api_key
    if timeout := os.environ.get('MYCLI_TIMEOUT'):
        config['timeout'] = int(timeout)
    
    return config
```

### PEP 723 Script with Dependencies

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0",
# ]
# ///

import click
from rich.console import Console

console = Console()

@click.command()
def main():
    """Example script with inline dependencies."""
    console.print("[green]Hello from uvx![/green]")

if __name__ == '__main__':
    main()
```

Run with: `uvx run script.py`
