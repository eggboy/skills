---
name: cli-creator
description: |
  Create command-line interface (CLI) tools following clig.dev best practices.
  USE FOR: building CLI apps, command-line tools, terminal utilities, improving
  existing CLI code, argument parsing, help text, error handling, output formatting,
  progress bars, colors, stdin/stdout, signals/Ctrl+C handling, configuration,
  environment variables. Covers Python (Click, Typer, argparse), Node.js
  (Commander, yargs), Go (Cobra), Rust (Clap), Bash (getopts). Includes starter
  templates and language-specific references.
  DO NOT USE FOR: GUI applications, TUI frameworks (textual, bubbletea, tui-rs),
  long-running daemons/services, web servers, or desktop apps.
---

# CLI Creator

Create excellent command-line interfaces following clig.dev best practices.

## Workflow

Determine the task type and follow the appropriate path:

**Creating a new CLI?** → Follow "New CLI" below
**Improving an existing CLI?** → Follow "Improve Existing CLI" below

### New CLI

1. Select language and framework (see table below)
2. Copy the corresponding starter template from `assets/templates/` into the user's project directory, rename to match the CLI name
3. Customize the template for the use case
4. Read the language-specific reference for advanced patterns (subcommands, progress bars, prompts)
5. Validate against [references/guidelines.md](references/guidelines.md)
6. For Bash scripts, run `shellcheck` to validate correctness

### Improve Existing CLI

1. Read [references/guidelines.md](references/guidelines.md) for clig.dev principles
2. Audit against the [compliance checklist](references/guidelines.md#compliance-checklist) — covers: help/usage, errors→stderr, stdin/stdout, signals/cleanup, `--json`/`--plain`, `NO_COLOR`, exit codes, secrets
3. Read the language-specific reference for implementation patterns
4. Apply fixes for identified gaps
5. For Bash scripts, run `shellcheck` to validate correctness

## Language and Framework Selection

| Language | Framework | Best For | Reference |
|----------|-----------|----------|-----------|
| Python | **Click** | General purpose, decorator-based | [references/python.md](references/python.md) |
| Python | **Typer** | Type-hint based, modern | [references/python.md](references/python.md) |
| Python | **argparse** | No dependencies, simple CLIs | [references/python.md](references/python.md) |
| Node.js | **Commander** | Most popular, clean API | [references/nodejs.md](references/nodejs.md) |
| Node.js | **yargs** | Feature-rich, complex CLIs | [references/nodejs.md](references/nodejs.md) |
| Go | **Cobra** | Industry standard (kubectl, hugo, gh) | [references/go.md](references/go.md) |
| Rust | **Clap** | Derive or builder API | [references/rust.md](references/rust.md) |
| Bash | **getopts** | Simple scripts, no dependencies | [references/bash.md](references/bash.md) |

## Starter Templates

Copy the appropriate template into the user's project, rename, and customize the processing logic:

- `assets/templates/python-click-template.py` — Python + Click (PEP 723, run with `uvx`)
- `assets/templates/nodejs-commander-template.js` — Node.js + Commander
- `assets/templates/go-cobra-template.go` — Go + Cobra
- `assets/templates/rust-clap-template.rs` — Rust + Clap
- `assets/templates/bash-template.sh` — Bash + getopts

All templates include: argument parsing, stdin/stdout support, error handling with exit codes, Ctrl+C handling, `--verbose` and `--json` flags, and `NO_COLOR` respect.

## Subcommand CLIs

For multi-command tools (`mycli init`, `mycli build`, `mycli deploy`), read the subcommand section in the language-specific reference:

- Python: Click `@click.group()` or Typer app with multiple `@app.command()`
- Node.js: Commander `.command()` or yargs `.command()`
- Go: Cobra `AddCommand()` tree
- Rust: Clap `#[derive(Subcommand)]` enum
- Bash: `case` dispatch on `$1` with per-command functions

## Reference Documentation

Read these as needed for detailed patterns and examples:

- **[references/guidelines.md](references/guidelines.md)** — Complete clig.dev principles: philosophy, help text structure, output formatting, error handling, arguments/flags, interactivity, configuration, environment variables, naming, signals, distribution, analytics
- **[references/python.md](references/python.md)** — Click, Typer, argparse: subcommands, progress bars, colors, stdin, JSON output, env vars, testing
- **[references/nodejs.md](references/nodejs.md)** — Commander, yargs: subcommands, chalk/ora, stdin, prompts, package.json setup, testing
- **[references/go.md](references/go.md)** — Cobra, urfave/cli, flag: subcommands, colors, progress, signal handling, cross-compilation
- **[references/rust.md](references/rust.md)** — Clap (derive + builder): subcommands, colored, indicatif, anyhow errors, testing with assert_cmd
- **[references/bash.md](references/bash.md)** — getopts: subcommands, colors, stdin, JSON with jq, signals, testing with bats-core, shellcheck
