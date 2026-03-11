# Command Line Interface Guidelines (clig.dev)

Comprehensive reference for building excellent command-line interfaces based on clig.dev principles.

## Table of Contents

- [Philosophy](#philosophy)
- [Help](#help)
- [Documentation](#documentation)
- [Output](#output)
- [Errors](#errors)
- [Arguments and Flags](#arguments-and-flags)
- [Interactivity](#interactivity)
- [Subcommands](#subcommands)
- [Robustness](#robustness)
- [Future-proofing](#future-proofing)
- [Signals and Control Characters](#signals-and-control-characters)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Naming](#naming)
- [Stdin/Stdout Patterns](#stdinstdout-patterns)
- [Unicode and Emoji](#unicode-and-emoji)
- [Performance](#performance)
- [Testing](#testing)
- [Distribution](#distribution)
- [Analytics](#analytics)
- [Compliance Checklist](#compliance-checklist)
- [Common Mistakes (Bad vs Good)](#common-mistakes-bad-vs-good)

## Philosophy

### Human-First Design
- Optimize for humans first, machines second
- CLIs are both UIs and APIs
- Default to human-readable output, provide machine-readable on request

### Simple Parts That Work Together
- Follow Unix philosophy: Do one thing well
- Compose with other tools via pipes
- Read from stdin, write to stdout
- Use exit codes meaningfully

### Consistency
- Follow existing conventions (POSIX, GNU)
- Be consistent within your tool
- Match patterns users already know

## Help

### Provide `-h` and `--help`
Always support both short and long forms. Display help and exit successfully.

```bash
mycli -h
mycli --help
```

### Make Help Discoverable
- Show brief usage on errors
- Suggest `--help` when users make mistakes
- Don't require subcommands just for help

### Structure Help Output

```
Usage: mycli [OPTIONS] <input>

Brief one-line description

Arguments:
  <input>  Description of required positional argument

Options:
  -o, --output <file>  Output file [default: stdout]
  -f, --force          Overwrite existing files
  -v, --verbose        Show detailed output
  -h, --help          Print help
  -V, --version       Print version

Examples:
  mycli input.txt
  mycli input.txt -o output.txt
```

### Help Content Guidelines
- Lead with a concise description
- Group related options
- Show defaults in brackets
- Include common examples
- Link to full documentation
- Provide a support path (website URL or GitHub link) in top-level help
- Link to web docs for subcommands where detailed docs exist

### Show Concise Help When No Args Provided
If your command requires arguments, show a brief usage summary with 1-2 examples and a pointer to `--help`. Don't just print an error.

### Suggest Corrections
If the user typed something close to a valid command/flag, suggest the correction:
```
$ mycli delpoy
Error: unknown command "delpoy"
Did you mean "deploy"? [y/N]:
```

### Handle Interactive Stdin
If your command expects piped stdin and `stdin` is an interactive terminal, display help immediately and quit. Don't just hang like `cat`.

## Documentation

### Provide Web-Based Documentation
People need to search for and link to your docs. A web page is the most accessible format.

### Provide Terminal-Based Documentation
Terminal docs are fast, stay in sync with the installed version, and work offline.

### Consider Man Pages
Many users reflexively run `man mycmd`. Tools like [ronn](http://rtomayko.github.io/ronn/ronn.1.html) can generate both man pages and web docs from the same source. Also make man pages accessible via `mycli help <command>`.

### Provide `--version`
Show version on a single line with no prefix:

```
1.2.3
```

Not: `mycli version 1.2.3` or `v1.2.3`

### Use Standard Versioning
Follow semantic versioning (MAJOR.MINOR.PATCH)

### Include Examples
- Show the most common use cases
- Progress from simple to complex
- Use realistic data

## Output

### Human vs Machine Readable

**Default to human-readable:**
```bash
mycli process file.txt
Processing file.txt... done
Processed 1,234 records in 2.5s
```

**Provide machine-readable with flags:**
```bash
mycli process file.txt --json
{"records": 1234, "duration": 2.5, "status": "success"}
```

### Output Flags
- `--json` for JSON output
- `--yaml` for YAML output  
- `--quiet` or `-q` to suppress non-essential output
- `--verbose` or `-v` for detailed output

### Use Stdout for Output, Stderr for Messaging
```python
# Primary output → stdout
print(result)

# Progress, warnings, errors → stderr
print("Processing...", file=sys.stderr)
```

### Show Progress for Long Operations
```bash
Downloading file... 45% [=========>         ] 2.3s
```

Use progress bars for operations >2 seconds. Strip when output is piped.

### Tell the User About State Changes
When your command changes system state, explain what happened:
```bash
$ mycli deploy
Deployed api-server v1.2.3 to production
Endpoint: https://api.example.com
```

### Suggest Next Commands
Help users discover the workflow by suggesting what to run next:
```bash
$ mycli init
Initialized project in ./myapp
Next: run 'mycli build' to compile
```

### Provide `--plain` for Machine-Friendly Tabular Output
If your human-readable table wraps cells across lines, provide `--plain` that outputs strict one-record-per-line for `grep` and `awk`.

### Use a Pager for Long Output
If outputting many pages of text, pipe through a pager like `less`. Good defaults: `less -FIRX` (don't page if fits one screen, ignore case in search, enable color, leave content on screen when quitting). Only use a pager when stdout is a TTY.

### Don't Treat Stderr Like a Log File
Don't print log level labels (`ERR`, `WARN`) or extraneous context unless in verbose mode.

### No Animations When Not a TTY
Disable progress bars and spinners when stdout is not an interactive terminal. They turn into garbage in CI logs.

### Use Color Meaningfully
- Red for errors
- Yellow for warnings
- Green for success
- Blue/cyan for informational
- Detect TTY and disable color when piped

### Disable Color Rules
All of these should suppress color:
- `stdout`/`stderr` is not a TTY (check individually—stderr colors are still useful when piping stdout)
- `NO_COLOR` env var is set (any non-empty value)
- `TERM=dumb`
- `--no-color` flag passed
- Consider also supporting `MYAPP_NO_COLOR` for app-specific control

### Format Tables Properly
```
NAME       STATUS    SIZE     CREATED
app-1      running   1.2GB    2 days ago
app-2      stopped   512MB    1 week ago
```

Consider libraries like `tabulate` (Python) or `cli-table` (Node.js)

## Errors

### Write Errors to Stderr
All error messages, warnings, and debugging info go to stderr.

### Use Meaningful Exit Codes
- `0` - Success
- `1` - General error
- `2` - Misuse (invalid arguments)
- `126` - Command cannot execute
- `127` - Command not found
- `128+N` - Terminated by signal N
- Custom codes for specific error types (document them)

### Make Errors Actionable
```bash
# Bad
Error: Invalid input

# Good
Error: Cannot read 'config.json': file not found
Try: mycli init to create a default config
```

### Error Message Structure
1. What went wrong
2. Why it's a problem (if not obvious)
3. How to fix it

### Signal-to-Noise Ratio
The more irrelevant output you produce, the longer users take to find the real problem. Group multiple errors of the same type under a single header instead of printing many similar lines.

### Put Important Info at the End
The user's eye goes to the end of output first. Put the key message (what to do next) at the bottom.

### Provide Debug Info on Unexpected Errors
For unexpected errors, provide traceback and instructions on how to submit a bug. Consider writing debug logs to a file instead of cluttering the terminal. Make it easy to submit bug reports—provide a URL that pre-populates issue details.

### Handle Ctrl+C Gracefully
Catch SIGINT and clean up:
```python
import signal
import sys

def signal_handler(sig, frame):
    print('\nInterrupted. Cleaning up...', file=sys.stderr)
    # Clean up resources
    sys.exit(130)  # 128 + SIGINT

signal.signal(signal.SIGINT, signal_handler)
```

## Arguments and Flags

### Prefer Flags to Arguments
Flags are more explicit and easier to understand:
```bash
# Good
mycli --input file.txt --output result.txt

# Also acceptable for common cases
mycli file.txt -o result.txt
```

### Standard Flag Names
Use these conventional names when applicable:
- `-a`, `--all` — all items (e.g. `ps`, `fetchmail`)
- `-d`, `--debug` — show debugging output
- `-f`, `--force` — force operation, skip confirmations
- `--json` — display JSON output
- `-h`, `--help` — show help (never overload)
- `-n`, `--dry-run` — show what would happen without doing it
- `--no-input` — disable interactive prompts
- `-o`, `--output` — output file
- `-p`, `--port` — port number
- `-q`, `--quiet` — suppress non-essential output
- `-u`, `--user` — user name
- `--version` — show version
- `-v` — verbose (or version; prefer `-d` for debug to avoid ambiguity)

### Use Standard Flag Conventions
- Single dash for short form: `-v`
- Double dash for long form: `--verbose`
- Short flags can be combined: `-abc` = `-a -b -c`
- Long flags use `=` or space: `--output=file` or `--output file`

### Provide Both Short and Long Forms
For commonly used flags. Only use one-letter flags for common ones—don't pollute the namespace.
```
-v, --verbose
-o, --output <file>
-f, --force
```

### Make Arguments, Flags, and Subcommands Order-Independent
Users often hit up-arrow and add a flag at the end. Both of these should work:
```bash
mycli --verbose subcmd
mycli subcmd --verbose
```

### Never Require a Prompt
Always provide a way to pass input via flags or arguments. If stdin is not a TTY, skip prompting and require flags/args instead.

### Don't Read Secrets from Flags
Flag values leak into `ps` output and shell history. Accept secrets via:
- `--password-file <path>` (reads from a file)
- Standard input (pipe or redirect)
- A secret management service

### Make Defaults Intelligent
- Respect environment variables
- Use reasonable defaults
- Show defaults in help text

### Support `--` to End Flag Parsing
```bash
mycli --flag -- --looks-like-flag-but-isnt
```

## Interactivity

### Prompt for Dangerous Actions
```bash
$ mycli delete --all
This will delete 156 records. Continue? [y/N]: 
```

### Provide `--yes` or `-y` to Skip Prompts
For automation and scripting:
```bash
mycli delete --all --yes
```

### Respect `--no-interactive` or `CI=true`
Disable all prompts in non-interactive environments

### Don't Echo Passwords
When prompting for secrets, turn off terminal echo. Your language should have helpers for this.

### Let the User Escape
Make it clear how to get out. Make Ctrl-C always work. If wrapping another program where Ctrl-C can't quit (SSH, tmux), document the escape mechanism.

### Confirm Destructive Operations
Severity levels guide the confirmation approach:
- **Mild** (e.g., deleting a file): Optional prompt
- **Moderate** (e.g., deleting a directory or remote resource): Prompt for confirmation, offer `--dry-run`
- **Severe** (e.g., deleting an entire app/server): Require typing the resource name, or `--confirm="name-of-thing"` for scripting

Unless `--force` or `--yes` is provided.

## Subcommands

### Use Subcommands for Complex Tools
```bash
mycli init
mycli build --release
mycli deploy production
```

### Make Subcommands Discoverable
```bash
$ mycli
Usage: mycli <command>

Commands:
  init     Initialize a new project
  build    Build the project
  deploy   Deploy to environment
  help     Show help for a command

Run 'mycli <command> --help' for more information
```

### Support `help` as a Subcommand
```bash
mycli help
mycli help deploy
```

### Group Related Subcommands
Use namespacing for large command sets:
```bash
mycli config get
mycli config set
mycli config list
```

### Use Consistent Naming for Multi-Level Subcommands
If you have noun+verb patterns (`docker container create`), be consistent with verbs across all nouns. Either `noun verb` or `verb noun` works, but `noun verb` is more common.

### Don't Use Ambiguous or Similar Names
Having both "update" and "upgrade" is confusing. Use distinct words or disambiguate with extra words.

## Robustness

### Validate Early
Check inputs before doing work:
- File existence
- Permission checks
- Network connectivity
- Argument validity

### Fail Loudly
Don't silently continue on errors. Make problems visible.

### Be Atomic
Either complete fully or fail cleanly. Don't leave partial state.

### Make Things Time Out
Allow network timeouts to be configured. Have a reasonable default so nothing hangs forever.

### Make It Recoverable
If the program fails for a transient reason (e.g., network), the user should be able to hit up-arrow, Enter, and have it resume or retry from where it left off.

### Make It Crash-Only
If you can avoid needing cleanup after operations, or defer cleanup to the next run, your program can exit immediately on failure. This makes it more robust and responsive.

### Anticipate Misuse
People will wrap your program in scripts, run it on bad connections, run many instances at once, and use it in environments you haven't tested. (Did you know macOS filesystems are case-insensitive but case-preserving?)

### Handle Missing Dependencies
```bash
Error: 'git' is required but not found
Install: brew install git  (macOS)
         apt install git   (Debian/Ubuntu)
```

### Check Preconditions
```bash
Error: No git repository found
Try: git init
```

## Future-proofing

### Use Semantic Versioning
MAJOR.MINOR.PATCH

### Don't Break Compatibility
- Add new flags, don't change existing ones
- Deprecate with warnings before removing
- Use opt-in for breaking changes

### Version Your Config Files
```json
{
  "version": 2,
  "config": {...}
}
```

### Keep Scripts Forward-Compatible
Use explicit flags rather than positional arguments

### Don't Have a Catch-All Subcommand
Don't let users omit a subcommand name for brevity (e.g., `mycmd echo "hello"` instead of `mycmd run echo "hello"`). You can never add a subcommand named `echo` without breaking existing scripts.

### Don't Allow Arbitrary Abbreviations of Subcommands
If `mycmd i` means `mycmd install`, you can never add another command starting with `i`. Explicit aliases are fine, but they should be stable and documented.

### Changing Human Output Is OK
The only way to improve an interface is to iterate. Encourage users to use `--plain` or `--json` for stable output in scripts.

### Don't Create a Time Bomb
Will your command still work in 20 years? Don't depend on external services that may disappear. The server most likely to not exist in 20 years is the one you're maintaining now.

## Signals and Control Characters

### Exit Immediately on Ctrl-C
When the user hits Ctrl-C (SIGINT), say something immediately before starting cleanup. Add a timeout to cleanup code so it can't hang forever.

### Second Ctrl-C Should Force Quit
If cleanup might take a long time, let a second Ctrl-C skip it:
```
$ mycli up
…
^C Gracefully stopping... (press Ctrl+C again to force)
```

### Expect Unclean State on Start
Your program should handle the case where previous cleanup didn't run (crash-only design).

## Configuration

### Configuration Priority (highest to lowest)
1. Command-line flags
2. Environment variables
3. Project config file (`.myclirc` in project)
4. User config file (`~/.myclirc`)
5. System config file (`/etc/mycli/config`)
6. Defaults

### Use Standard Config Locations
- Unix: `~/.config/mycli/config`
- macOS: `~/Library/Application Support/mycli/config`
- Windows: `%APPDATA%\mycli\config`

Or use XDG Base Directory specification

### Support Multiple Config Formats
JSON, YAML, TOML - pick what makes sense for your tool

### Provide Config Management Commands
```bash
mycli config get key
mycli config set key value
mycli config list
```

## Environment Variables

### Use Prefixed Environment Variables
`MYCLI_API_KEY`, not `API_KEY`

### Naming Rules
Environment variable names must only contain uppercase letters, numbers, and underscores (and must not start with a number). For maximum portability.

### Prefer Single-Line Values
Multi-line env var values create usability issues with the `env` command.

### Document All Environment Variables
In `--help` output or README

### Respect Standard Variables
- `NO_COLOR` - disable color
- `TERM` - terminal type
- `EDITOR` - default editor
- `PAGER` - default pager
- `HOME` - home directory
- `CI` - running in CI environment

### Example Environment Variable Usage
```bash
MYCLI_API_KEY=secret mycli deploy
MYCLI_DEBUG=1 mycli process
NO_COLOR=1 mycli status
```

### Read from `.env` Where Appropriate
If variables are unlikely to change within a project directory, read them from a local `.env` file. Many languages have libraries for this ([dotenv](https://www.npmjs.com/package/dotenv) for Node, [python-dotenv](https://pypi.org/project/python-dotenv/), [dotenvy](https://crates.io/crates/dotenvy) for Rust).

However, don't use `.env` as a substitute for a proper config file—it only supports strings, has no history in version control, and often contains secrets that would be better stored securely.

### Don't Read Secrets from Environment Variables
Env vars are insecure:
- Exported to every child process, easily leaked into logs
- Shell substitutions like `curl -H "Authorization: Bearer $TOKEN"` leak into globally-readable process state
- Docker `inspect` and `systemctl show` expose them

Accept secrets via credential files, pipes, `AF_UNIX` sockets, or secret management services.

## Naming

### Choose Clear, Specific Names
- Good: `imagemin`, `webpack`, `rustup`
- Avoid: `data`, `process`, `manager`

### Use Lowercase
`mycli`, not `MyCLI` or `myCli`

### Avoid Special Characters
Stick to letters, numbers, hyphens

### Be Consistent
- Use same name everywhere (CLI, docs, repo)
- Match package manager naming conventions

### Don't Conflict with Existing Tools
Check if the name is already taken:
```bash
which mycli
command -v mycli
```

## Stdin/Stdout Patterns

### Read from Stdin When No File Specified
```bash
cat data.txt | mycli process
mycli process < data.txt
```

### Support Both File and Stdin
```python
import sys

def read_input(filename=None):
    if filename and filename != '-':
        with open(filename) as f:
            return f.read()
    else:
        return sys.stdin.read()
```

### Use `-` to Explicitly Mean Stdin/Stdout
```bash
mycli process - < input.txt > output.txt
```

### Be Pipeable
```bash
cat file.txt | mycli process | grep pattern | sort
```

## Unicode and Emoji

### Support Unicode
Handle UTF-8 correctly in input and output

### Use Emoji Sparingly
- ✓ for success
- ✗ for errors
- Provide `--no-emoji` flag
- Fallback to ASCII: `[OK]`, `[ERROR]`

## Performance

### Start Fast
Target <100ms startup time for simple commands

### Show Progress for Slow Operations
Operations >2 seconds should show progress

### Cache When Appropriate
Store expensive computations, respect `--no-cache`

### Provide `--verbose` for Debugging
Show timing, API calls, decisions made

## Testing

### Provide `--dry-run`
Show what would happen without doing it:
```bash
mycli deploy --dry-run
Would deploy:
  - api-server (v1.2.3)
  - web-frontend (v2.1.0)
```

### Support `--debug`
Show detailed internal information

### Make Testing Easy
- Use `--quiet` to suppress output
- Return meaningful exit codes
- Support JSON output for validation

## Distribution

### Distribute as a Single Binary if Possible
If your language doesn't compile to binaries natively, consider tools like [PyInstaller](https://www.pyinstaller.org/) (Python), `pkg` (Node.js), or static linking. For language-specific tools (linters, formatters), it's fine to assume the runtime is installed.

### Make It Easy to Uninstall
Put uninstall instructions at the bottom of your install instructions—one of the most common times people want to uninstall is right after installing. Don't scatter files across the filesystem; use native package installers.

## Analytics

### Don't Phone Home Without Consent
Users expect to control their CLI environment. Collecting usage or crash data without telling them will make them angry.
- **Opt-in** is ideal: ask users if they want to contribute data
- **Opt-out** at minimum: clearly tell users on first run, make it easy to disable
- Be explicit about what you collect, how you anonymize it, and how long you retain it

### Consider Alternatives to Analytics
- Instrument your web docs to understand usage patterns
- Track download counts by platform
- Talk to your users directly
- Encourage feedback and feature requests in your repos

## Compliance Checklist

Audit any CLI against this checklist to verify clig.dev compliance:

- [ ] Provides `-h`/`--help` with usage examples
- [ ] Shows concise help when run with no args (or shows usage error)
- [ ] Suggests corrections for typos ("did you mean?")
- [ ] Error messages are actionable (what happened + how to fix)
- [ ] Errors go to stderr, primary output to stdout
- [ ] Handles Ctrl+C gracefully (exit code 130)
- [ ] Second Ctrl+C force-quits during cleanup
- [ ] Supports `--json` for machine-readable output
- [ ] Supports `--plain` for grep/awk-friendly tabular output
- [ ] Supports stdin when no file argument given
- [ ] Respects `NO_COLOR` environment variable
- [ ] No animations/progress bars when not a TTY
- [ ] Uses meaningful exit codes (0=success, 1=error, 2=misuse)
- [ ] Doesn't read secrets from flags or env vars
- [ ] Suggests next commands after state changes

## Common Mistakes (Bad vs Good)

### Error Output

```bash
# ❌ BAD: error to stdout, no exit code
echo "File not found"

# ✅ GOOD: error to stderr, actionable message, proper exit code
echo "Error: config.yaml not found. Run 'mycli init' to create one." >&2
exit 1
```

### Help Text

```
# ❌ BAD: no examples, technical jargon
Usage: mycli [OPTIONS] FILE
  --threshold  Set the threshold

# ✅ GOOD: real examples, clear descriptions
Usage: mycli [OPTIONS] <file>

Transform data files to JSON format.

Arguments:
  <file>  Input file to process (use - for stdin)

Options:
  -t, --threshold <n>  Skip values below n (default: 0)
  -o, --output <file>  Write to file instead of stdout

Examples:
  mycli data.csv
  mycli -t 10 data.csv -o result.json
  cat data.csv | mycli -
```

### Color Handling

```python
# ❌ BAD: hardcoded colors, breaks pipes and NO_COLOR
print("\033[31mError: failed\033[0m")

# ✅ GOOD: respect NO_COLOR and TTY
import sys, os
use_color = sys.stderr.isatty() and not os.environ.get("NO_COLOR")
RED = "\033[31m" if use_color else ""
RESET = "\033[0m" if use_color else ""
print(f"{RED}Error: failed{RESET}", file=sys.stderr)
```

### Signal Handling

```bash
# ❌ BAD: swallow Ctrl+C, exit 0
trap '' INT
# ... cleanup ...
exit 0

# ✅ GOOD: clean up, preserve exit code 130
trap 'cleanup; exit 130' INT
```

### Stdin Detection

```python
# ❌ BAD: hangs waiting for stdin with no indication
data = sys.stdin.read()

# ✅ GOOD: detect TTY, show guidance
if sys.stdin.isatty():
    print("Error: no input. Pipe data or pass a file.", file=sys.stderr)
    sys.exit(2)
data = sys.stdin.read()
```
