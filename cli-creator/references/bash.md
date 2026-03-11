# Bash CLI Patterns

Bash implementations of clig.dev guidelines using built-in features and getopts.

## Table of Contents

- [Recommended Tools](#recommended-tools)
- [Style Conventions](#style-conventions): Variables, Constants, Functions, Quoting, Arithmetic, Tests, File Safety, Scope Pitfalls
- [Pure Bash (getopts)](#pure-bash-getopts): Basic CLI, Subcommands
- [Colors and Progress](#colors-and-progress): Color Functions, Progress Indicators, Spinners
- [Reading from Stdin](#reading-from-stdin)
- [JSON Output](#json-output)
- [Environment Variables](#environment-variables)
- [Common Patterns](#common-patterns): SIGINT Handling, Stdin or File, Color Detection, Configuration Loading, Temp File Cleanup, Dependency Checking, TTY Detection, Dry Run, Debug Tracing
- [Testing](#testing)
- [Distribution](#distribution)

## Recommended Tools

**getopts** — Built-in, POSIX-compliant, short options only
**bats-core** — Bash Automated Testing System ([bats-core](https://github.com/bats-core/bats-core))
**shellcheck** — Static analysis for shell scripts ([shellcheck](https://www.shellcheck.net/))

## Style Conventions

Apply these conventions in all generated Bash code.

### Variables

| Use | Avoid | Why |
|-----|-------|-----|
| `"${var}"` | `"$var"` | Braces prevent ambiguity in `${filename}_backup` |
| `local var; var=$(cmd)` | `local var=$(cmd)` | `local` always returns 0, masking failures |
| `local -i count=0` | `local count=0` | Enforces arithmetic context |
| Descriptive: `file_path` | Abbreviated: `fp` | Readability |

### Constants

| Use | Avoid |
|-----|-------|
| `readonly VERSION="1.0.0"` | `VERSION="1.0.0"` |
| `readonly E_NOTFOUND=65` | Magic numbers inline |

### Functions

| Use | Avoid |
|-----|-------|
| `function my_func() { }` | `my_func() { }` |
| `snake_case` names | `camelCase` or `PascalCase` |

Assign positional args to named locals at the top:

```bash
function process_file() {
    local input_file="${1}"
    local output_file="${2}"
    # ...
}
```

Wrap the script in a `main` function called at the end:

```bash
function main() {
    # script logic
}

main "${@}"
```

### Quoting

| Use | Avoid | Why |
|-----|-------|-----|
| `"${var}"` | `${var}` | Prevents word splitting |
| `"$(command)"` | `$(command)` | Prevents word splitting |
| `'literal string'` | `literal\ string` | Clearer than backslash escaping |
| `"${array[@]}"` | `${array[@]}` | Preserves elements with spaces |

Only omit quotes when word splitting is intentional.

### Arithmetic

| Use | Avoid |
|-----|-------|
| `((i++))` | `let i++` |
| `$((x + 1))` | `expr $x + 1` |
| `for ((i=1; i<=10; i++))` | `for i in $(seq 1 10)` |
| `for i in {1..10}` | `for i in $(seq 1 10)` |

### Tests

| Use | Avoid | Why |
|-----|-------|-----|
| `[[ ... ]]` | `[ ... ]` | Safer, supports globs and regex |
| `==` for equality | `=` for equality | Clarity |
| `[[ -n "${var}" ]]` | `[[ "${var}" ]]` | Explicit intent |
| `if grep -q 'pat' file` | `if [[ $(grep 'pat' file) ]]` | Test exit code directly |
| `command -v git` | `which git` | POSIX-compliant, consistent |

### File Safety

| Use | Avoid | Why |
|-----|-------|-----|
| `rm ./*.txt` | `rm *.txt` | Prevents `-filename` as option |
| `for f in ./*.txt` | `for f in $(ls *.txt)` | Globs handle spaces correctly |
| `while IFS= read -r line` | `for line in $(cat file)` | Splits on newlines, not words |
| `grep pattern file` | `cat file \| grep pattern` | Avoids useless `cat` |
| `tmp=$(mktemp)` | `tmp=/tmp/myfile.$$` | Secure, no race conditions |
| `<<'EOF'` | `<<EOF` | Prevents unintended interpolation |

### Scope Pitfalls

Variables modified inside pipelines or subshells don't affect the parent:

```bash
count=0
echo "a b c" | while read -r word; do
    ((count++))  # modified in subshell
done
echo "${count}"  # still 0
```

Fix with process substitution:

```bash
count=0
while read -r word; do
    ((count++))
done < <(echo "a b c")
echo "${count}"  # 3
```

Use a subshell for temporary directory changes:

```bash
# Use: doesn't affect parent shell
(cd /some/dir && make)

# Avoid: changes cwd for rest of script
cd /some/dir
make
cd -
```

## Pure Bash (getopts)

### Basic CLI

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly VERSION="1.0.0"
VERBOSE=false
FORCE=false
OUTPUT=""

function usage() {
    cat <<'USAGE'
Usage: mycli [OPTIONS] <input>

Process INPUT file and transform it.

Arguments:
  <input>          Input file to process (use - for stdin)

Options:
  -o <file>        Output file (default: stdout)
  -v               Verbose output
  -f               Overwrite existing files
  -h               Show this help
  -V               Show version

Examples:
  mycli data.txt
  mycli data.txt -o result.txt
  mycli -v -f data.txt -o result.txt
  cat data.txt | mycli -
USAGE
}

function die() {
    printf 'Error: %s\n' "${1}" >&2
    exit "${2:-1}"
}

function log() {
    if [[ "${VERBOSE}" == true ]]; then
        printf '%s\n' "$*" >&2
    fi
}

function main() {
    while getopts ':o:vfhV' opt; do
        case "${opt}" in
            o) OUTPUT="${OPTARG}" ;;
            v) VERBOSE=true ;;
            f) FORCE=true ;;
            h) usage; exit 0 ;;
            V) printf '%s\n' "${VERSION}"; exit 0 ;;
            :) die "Option -${OPTARG} requires an argument" 2 ;;
            *) die "Unknown option: -${OPTARG}. Use -h for help" 2 ;;
        esac
    done
    shift $((OPTIND - 1))

    # Require input argument
    if [[ $# -lt 1 ]]; then
        usage >&2
        exit 2
    fi

    local input="${1}"

    # Read input
    local content
    if [[ "${input}" == "-" ]]; then
        content=$(cat)
    elif [[ -f "${input}" ]]; then
        content=$(<"${input}")
    else
        die "File not found: ${input}"
    fi

    log "Processing ${input}..."

    # Process (customize this)
    local result
    result=$(printf '%s' "${content}" | tr '[:lower:]' '[:upper:]')

    # Output
    if [[ -n "${OUTPUT}" ]]; then
        if [[ -e "${OUTPUT}" && "${FORCE}" != true ]]; then
            die "${OUTPUT} exists. Use -f to overwrite"
        fi
        printf '%s' "${result}" > "${OUTPUT}"
        log "Written to ${OUTPUT}"
    else
        printf '%s\n' "${result}"
    fi
}

main "${@}"
```

### Subcommands

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly PROG=$(basename "${0}")
readonly VERSION="1.0.0"

function usage() {
    cat <<USAGE
Usage: ${PROG} <command> [options]

A multi-command CLI tool.

Commands:
  init       Initialize a new project
  build      Build the project
  deploy     Deploy to environment
  help       Show help for a command

Options:
  -h         Show this help
  -V         Show version

Run '${PROG} help <command>' for more information on a command.
USAGE
}

function cmd_init() {
    local dir="."
    while getopts ':d:h' opt; do
        case "${opt}" in
            d) dir="${OPTARG}" ;;
            h) printf 'Usage: %s init [-d <dir>]\n\nInitialize a new project.\n' "${PROG}"; return 0 ;;
            *) printf 'Error: Unknown option -%s\n' "${OPTARG}" >&2; return 2 ;;
        esac
    done

    mkdir -p "${dir}"
    printf 'Initialized project in %s\n' "${dir}" >&2
    printf 'Next: run '\''%s build'\'' to compile\n' "${PROG}" >&2
}

function cmd_build() {
    local release=false
    while getopts ':rh' opt; do
        case "${opt}" in
            r) release=true ;;
            h) printf 'Usage: %s build [-r]\n\nBuild the project.\n\n  -r  Release mode\n' "${PROG}"; return 0 ;;
            *) printf 'Error: Unknown option -%s\n' "${OPTARG}" >&2; return 2 ;;
        esac
    done

    if [[ "${release}" == true ]]; then
        printf 'Building in release mode...\n' >&2
    else
        printf 'Building...\n' >&2
    fi
}

function cmd_deploy() {
    local env="${1:-}"
    if [[ -z "${env}" ]]; then
        printf 'Error: Environment required\nUsage: %s deploy <environment>\n' "${PROG}" >&2
        return 2
    fi
    printf 'Deploying to %s...\n' "${env}" >&2
}

function main() {
    # Parse global options before subcommand
    while getopts ':hV' opt; do
        case "${opt}" in
            h) usage; exit 0 ;;
            V) printf '%s\n' "${VERSION}"; exit 0 ;;
            *) break ;;
        esac
    done
    shift $((OPTIND - 1))

    local command="${1:-}"
    shift || true

    case "${command}" in
        init)   cmd_init "$@" ;;
        build)  cmd_build "$@" ;;
        deploy) cmd_deploy "$@" ;;
        help)
            case "${1:-}" in
                init)   cmd_init -h ;;
                build)  cmd_build -h ;;
                deploy) printf 'Usage: %s deploy <environment>\n\nDeploy to environment.\n' "${PROG}" ;;
                *)      usage ;;
            esac
            ;;
        "")
            usage >&2
            exit 2
            ;;
        *)
            printf 'Error: Unknown command '\''%s'\''\n' "${command}" >&2
            printf 'Run '\''%s -h'\'' for available commands\n' "${PROG}" >&2
            exit 2
            ;;
    esac
}

main "${@}"
```

## Colors and Progress

### Color Functions

```bash
# Respect NO_COLOR (https://no-color.org)
if [[ -t 1 ]] && [[ -z "${NO_COLOR:-}" ]] && [[ "${TERM:-}" != "dumb" ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[0;33m'
    readonly BLUE='\033[0;34m'
    readonly BOLD='\033[1m'
    readonly RESET='\033[0m'
else
    readonly RED=''
    readonly GREEN=''
    readonly YELLOW=''
    readonly BLUE=''
    readonly BOLD=''
    readonly RESET=''
fi

function error()   { printf "${RED}Error: %s${RESET}\n" "${1}" >&2; }
function warn()    { printf "${YELLOW}Warning: %s${RESET}\n" "${1}" >&2; }
function info()    { printf "${BLUE}%s${RESET}\n" "${1}" >&2; }
function success() { printf "${GREEN}✓ %s${RESET}\n" "${1}" >&2; }
```

### Progress Indicators

```bash
# Simple progress bar
function progress_bar() {
    local -i current=${1} total=${2} width=40
    local -i percent=$((current * 100 / total))
    local -i filled=$((current * width / total))
    local -i empty=$((width - filled))

    printf '\r['
    printf '%0.s=' $(seq 1 "${filled}" 2>/dev/null) || true
    printf '%0.s ' $(seq 1 "${empty}" 2>/dev/null) || true
    printf '] %3d%%' "${percent}"
}

# Usage
readonly total=100
for ((i=1; i<=total; i++)); do
    progress_bar "${i}" "${total}"
    sleep 0.01
done
printf '\n'
```

### Spinners

```bash
function spinner() {
    local pid="${1}"
    local message="${2:-Working...}"
    local chars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

    # Only show spinner on interactive terminals
    if [[ ! -t 2 ]]; then
        wait "${pid}"
        return $?
    fi

    while kill -0 "${pid}" 2>/dev/null; do
        for (( i=0; i<${#chars}; i++ )); do
            printf '\r%s %s' "${chars:$i:1}" "${message}" >&2
            sleep 0.1
        done
    done
    printf '\r%s\n' "✓ ${message}" >&2
    wait "${pid}"
}

# Usage
long_running_task &
spinner $! "Processing files..."
```

## Reading from Stdin

```bash
# Read from file argument or stdin
function read_input() {
    local file="${1:-}"
    if [[ -n "${file}" && "${file}" != "-" ]]; then
        if [[ ! -f "${file}" ]]; then
            printf 'Error: %s not found\n' "${file}" >&2
            return 1
        fi
        cat "${file}"
    elif [[ ! -t 0 ]]; then
        # stdin is piped
        cat
    else
        printf 'Error: No input. Provide a file or pipe data via stdin.\n' >&2
        printf 'Usage: %s <file> or command | %s -\n' "$(basename "${0}")" "$(basename "${0}")" >&2
        return 1
    fi
}

# Line-by-line processing from stdin or file
# Uses process substitution to avoid subshell scope issues
function process_lines() {
    local file="${1:--}"
    while IFS= read -r line; do
        printf '%s\n' "$(process_line "${line}")"
    done < <(read_input "${file}")
}
```

## JSON Output

```bash
# Simple JSON output (no dependencies)
function json_output() {
    local result="${1}" length="${2}" status="${3}"
    # Escape special characters for JSON
    result=$(printf '%s' "${result}" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\n/\\n/g')
    printf '{"result":"%s","length":%d,"status":"%s"}\n' "${result}" "${length}" "${status}"
}

# Using jq for complex JSON (if available)
function json_output_jq() {
    local result="${1}" length="${2}" status="${3}"
    jq -n \
        --arg result "${result}" \
        --argjson length "${length}" \
        --arg status "${status}" \
        '{result: $result, length: $length, status: $status}'
}

# Array output
function json_array() {
    local -a items=("$@")
    printf '['
    local first=true
    for item in "${items[@]}"; do
        [[ "${first}" == true ]] || printf ','
        printf '"%s"' "${item}"
        first=false
    done
    printf ']\n'
}

# Conditional JSON or human output
function output_result() {
    local result="${1}"
    if [[ "${JSON:-false}" == true ]]; then
        json_output "${result}" "${#result}" "success"
    else
        printf '%s\n' "${result}"
    fi
}
```

## Environment Variables

```bash
# Load with defaults and env var override
: "${MYCLI_CONFIG_DIR:=${XDG_CONFIG_HOME:-$HOME/.config}/mycli}"
: "${MYCLI_TIMEOUT:=30}"
: "${MYCLI_VERBOSE:=false}"
: "${MYCLI_NO_COLOR:=${NO_COLOR:-}}"

# Load from .env file if present
function load_dotenv() {
    local envfile="${1:-.env}"
    if [[ -f "${envfile}" ]]; then
        # Only load lines matching KEY=VALUE, skip comments and blank lines
        while IFS='=' read -r key value; do
            # Skip comments and blank lines
            [[ -z "${key}" || "${key}" == \#* ]] && continue
            # Strip surrounding quotes from value
            value="${value%\"}"
            value="${value#\"}"
            value="${value%\'}"
            value="${value#\'}"
            export "${key}=${value}"
        done < "${envfile}"
    fi
}

# Document env vars in help text
function env_help() {
    cat <<'ENVHELP'

Environment Variables:
  MYCLI_CONFIG_DIR   Config directory (default: ~/.config/mycli)
  MYCLI_TIMEOUT      Request timeout in seconds (default: 30)
  MYCLI_VERBOSE      Enable verbose output (default: false)
  NO_COLOR           Disable color output (any non-empty value)
ENVHELP
}
```

## Common Patterns

### Graceful SIGINT Handling

```bash
# Track child processes for cleanup
CHILD_PID=""
CLEANUP_DONE=false

function cleanup() {
    local exit_code="${?}"  # preserve original exit code
    [[ "${CLEANUP_DONE}" == true ]] && return
    CLEANUP_DONE=true

    printf '\nInterrupted. Cleaning up...\n' >&2

    # Kill child processes
    [[ -n "${CHILD_PID}" ]] && kill "${CHILD_PID}" 2>/dev/null

    # Remove temp files
    [[ -n "${TMPDIR_CREATED:-}" ]] && rm -rf "${TMPDIR_CREATED}"

    exit "${exit_code}"
}

# Second Ctrl+C force-quits
function force_quit() {
    printf '\nForce quit.\n' >&2
    exit 130
}

trap cleanup INT TERM
# After first Ctrl+C, next one force-quits
trap 'trap force_quit INT; cleanup' INT
```

### Stdin or File Helper

```bash
# Portable read from file or stdin
function input_from() {
    local source="${1:--}"
    if [[ "${source}" == "-" ]]; then
        cat
    else
        cat "${source}"
    fi
}

# Usage: result=$(input_from "${file}" | process)
```

### Color Support Detection

```bash
function supports_color() {
    # Check stderr separately from stdout
    local fd="${1:-1}"  # 1=stdout, 2=stderr

    [[ -z "${NO_COLOR:-}" ]] || return 1
    [[ "${TERM:-}" != "dumb" ]] || return 1
    [[ -t "${fd}" ]] || return 1
    return 0
}
```

### Configuration Loading

```bash
function load_config() {
    local config_file="${MYCLI_CONFIG_DIR}/config"

    # Defaults
    declare -gA CONFIG=(
        [api_url]="https://api.example.com"
        [timeout]="30"
        [retries]="3"
    )

    # Load system config
    [[ -f "/etc/mycli/config" ]] && source_config "/etc/mycli/config"

    # Load user config
    [[ -f "${config_file}" ]] && source_config "${config_file}"

    # Load project config
    [[ -f ".myclirc" ]] && source_config ".myclirc"

    # Environment overrides
    [[ -n "${MYCLI_API_URL:-}" ]] && CONFIG[api_url]="${MYCLI_API_URL}"
    [[ -n "${MYCLI_TIMEOUT:-}" ]] && CONFIG[timeout]="${MYCLI_TIMEOUT}"
}

function source_config() {
    # Simple KEY=VALUE config reader (not sourced for safety)
    while IFS='=' read -r key value; do
        [[ -z "${key}" || "${key}" == \#* ]] && continue
        CONFIG["${key}"]="${value}"
    done < "${1}"
}
```

### Temp File Cleanup

```bash
# Create a temp directory that auto-cleans on exit
# Preserve exit code so cleanup doesn't mask failures
TMPDIR_CREATED=$(mktemp -d)
trap 'local ec="${?}"; rm -rf "${TMPDIR_CREATED}"; exit "${ec}"' EXIT

# Safe temp file usage
tmpfile="${TMPDIR_CREATED}/work.tmp"
```

### Dependency Checking

```bash
function check_deps() {
    local missing=()
    for cmd in "$@"; do
        # Use command -v (POSIX), not which (inconsistent across systems)
        if ! command -v "${cmd}" &>/dev/null; then
            missing+=("${cmd}")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        printf 'Error: Missing required dependencies: %s\n' "${missing[*]}" >&2
        printf 'Install with:\n' >&2
        for cmd in "${missing[@]}"; do
            case "${cmd}" in
                jq)   printf '  brew install jq  (macOS)\n  apt install jq   (Debian/Ubuntu)\n' >&2 ;;
                curl) printf '  brew install curl (macOS)\n  apt install curl  (Debian/Ubuntu)\n' >&2 ;;
                *)    printf '  Install %s for your platform\n' "${cmd}" >&2 ;;
            esac
        done
        return 1
    fi
}

# Usage at script start
check_deps jq curl git
```

### TTY Detection

```bash
function is_interactive() {
    [[ -t 0 ]] && [[ -t 1 ]]
}

# Conditional prompting
function confirm() {
    local message="${1:-Continue?}"
    if ! is_interactive; then
        printf 'Error: Confirmation required. Run interactively or pass --force.\n' >&2
        return 1
    fi
    printf '%s [y/N]: ' "${message}" >&2
    local response
    read -r response
    [[ "${response}" =~ ^[Yy]$ ]]
}
```

### Dry Run Pattern

```bash
DRY_RUN=false

function run_cmd() {
    if [[ "${DRY_RUN}" == true ]]; then
        printf '[dry-run] %s\n' "$*" >&2
    else
        "$@"
    fi
}

# Usage
run_cmd rm -rf "${BUILD_DIR}"
run_cmd cp -r "${SRC}" "${DEST}"
```

### Debug Tracing

```bash
# Enable tracing with TRACE=1 mycli.sh
[[ -n "${TRACE:-}" ]] && set -x
```

## Testing

### Testing with bats-core

```bash
# test/mycli.bats
#!/usr/bin/env bats

setup() {
    MYCLI="$BATS_TEST_DIRNAME/../mycli.sh"
    TMPDIR=$(mktemp -d)
    echo "hello world" > "$TMPDIR/input.txt"
}

teardown() {
    rm -rf "$TMPDIR"
}

@test "transforms input to uppercase" {
    run "$MYCLI" "$TMPDIR/input.txt"
    [ "$status" -eq 0 ]
    [ "$output" = "HELLO WORLD" ]
}

@test "writes to output file with -o" {
    run "$MYCLI" "$TMPDIR/input.txt" -o "$TMPDIR/out.txt"
    [ "$status" -eq 0 ]
    [ "$(cat "$TMPDIR/out.txt")" = "HELLO WORLD" ]
}

@test "reads from stdin with -" {
    run bash -c "echo 'hello' | $MYCLI -"
    [ "$status" -eq 0 ]
    [ "$output" = "HELLO" ]
}

@test "fails on missing file" {
    run "$MYCLI" nonexistent.txt
    [ "$status" -eq 1 ]
    [[ "$output" == *"not found"* ]]
}

@test "shows help with -h" {
    run "$MYCLI" -h
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "shows version with -V" {
    run "$MYCLI" -V
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "errors go to stderr" {
    run bash -c "$MYCLI nonexistent.txt 2>/dev/null"
    [ "$status" -eq 1 ]
    [ -z "$output" ]  # stdout should be empty
}

@test "refuses to overwrite without -f" {
    echo "existing" > "$TMPDIR/out.txt"
    run "$MYCLI" "$TMPDIR/input.txt" -o "$TMPDIR/out.txt"
    [ "$status" -eq 1 ]
    [[ "$output" == *"exists"* ]]
}

@test "overwrites with -f" {
    echo "existing" > "$TMPDIR/out.txt"
    run "$MYCLI" "$TMPDIR/input.txt" -f -o "$TMPDIR/out.txt"
    [ "$status" -eq 0 ]
    [ "$(cat "$TMPDIR/out.txt")" = "HELLO WORLD" ]
}

@test "exits 2 on invalid options" {
    run "$MYCLI" --invalid
    [ "$status" -eq 2 ]
}
```

### Running Tests

```bash
# Install bats-core
brew install bats-core        # macOS
apt install bats              # Debian/Ubuntu
npm install -g bats           # via npm

# Run tests
bats test/
bats test/mycli.bats          # Single file
bats --tap test/              # TAP output for CI
```

### Linting with ShellCheck

```bash
# Install
brew install shellcheck       # macOS
apt install shellcheck        # Debian/Ubuntu

# Lint
shellcheck mycli.sh
shellcheck --severity=warning mycli.sh
shellcheck --format=json mycli.sh   # JSON output for CI

# Inline directives to suppress false positives
# shellcheck disable=SC2034
UNUSED_BUT_EXPORTED_VAR="value"
```

### Syntax Check

```bash
# Quick syntax validation (no execution)
bash -n mycli.sh
```

## Distribution

### Make Executable

```bash
chmod +x mycli.sh

# Add shebang (always use env for portability)
#!/usr/bin/env bash
```

### Install Locally

```bash
# Copy to a directory in PATH
cp mycli.sh /usr/local/bin/mycli
chmod +x /usr/local/bin/mycli

# Or symlink for development
ln -sf "$(pwd)/mycli.sh" /usr/local/bin/mycli
```

### Self-Contained Script with Embedded Dependencies

```bash
# Bundle small helper scripts inline rather than requiring separate files
# For complex CLIs, consider using a Makefile or installer script
```

### Version Embedding at Build Time

```bash
# In a Makefile
VERSION := $(shell git describe --tags --always)

dist/mycli: mycli.sh
	sed "s/VERSION=\"dev\"/VERSION=\"$(VERSION)\"/" $< > $@
	chmod +x $@
```

### Portable Bash Practices

```bash
# Use #!/usr/bin/env bash (not #!/bin/bash)
# Target bash 3.2+ for macOS compatibility
# Avoid bash 4+ features if macOS support is needed:
#   - Associative arrays (declare -A)  → bash 4+
#   - readarray/mapfile                → bash 4+
#   - ${var,,} lowercase               → bash 4+
#   - |& (pipe stderr)                 → bash 4+
# macOS ships bash 3.2 unless user installs newer via Homebrew

# Always set strict mode
set -euo pipefail
```

### Dual-Purpose Scripts

Detect if a script is being sourced (for library use) or executed directly:

```bash
# Only run main when executed, not when sourced
[[ "${0}" == "${BASH_SOURCE[0]}" ]] && main "${@}"
```

### Security

- Never use SUID/SGID on shell scripts — use `sudo` for privilege escalation
- Avoid `eval` — it enables command injection and makes debugging difficult
- Use `sudo tee` to write to root-owned files (`echo "x" | sudo tee /etc/file`)
