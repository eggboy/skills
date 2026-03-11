#!/usr/bin/env bash
# Template: Bash CLI with getopts
# Implements clig.dev guidelines: help, errors, stdin/stdout, exit codes, signals, color
set -euo pipefail

readonly VERSION="0.1.0"
VERBOSE=false
FORCE=false
JSON=false
OUTPUT=""

# --- Colors (respect NO_COLOR: https://no-color.org) ---
if [[ -t 2 ]] && [[ -z "${NO_COLOR:-}" ]] && [[ "${TERM:-}" != "dumb" ]]; then
    readonly RED='\033[0;31m'; readonly GREEN='\033[0;32m'; readonly YELLOW='\033[0;33m'; readonly RESET='\033[0m'
else
    readonly RED=''; readonly GREEN=''; readonly YELLOW=''; readonly RESET=''
fi

# --- Output Helpers ---
function error() { printf "${RED}Error: %s${RESET}\n" "${1}" >&2; }
function warn()  { printf "${YELLOW}Warning: %s${RESET}\n" "${1}" >&2; }
function info()  { printf "${GREEN}%s${RESET}\n" "${1}" >&2; }
function log()   { [[ "${VERBOSE}" == true ]] && printf '%s\n' "$*" >&2 || true; }

function die() {
    error "${1}"
    exit "${2:-1}"
}

# --- Usage ---
function usage() {
    cat <<'USAGE'
Usage: mycli [OPTIONS] <input>

One-line description of what this tool does.

Arguments:
  <input>          Input file to process (use - for stdin)

Options:
  -o <file>        Output file (default: stdout)
  -v               Verbose output
  -f               Overwrite existing files
  --json           Output as JSON
  -h               Show this help
  -V               Show version

Environment Variables:
  NO_COLOR         Disable color output (any non-empty value)

Examples:
  mycli data.txt
  mycli -v data.txt -o result.txt
  cat data.txt | mycli -
USAGE
}

# --- Signal Handling ---
TMPDIR_CREATED=""
function cleanup() {
    local exit_code="${?}"
    [[ -n "${TMPDIR_CREATED}" ]] && rm -rf "${TMPDIR_CREATED}"
    exit "${exit_code}"
}
trap cleanup EXIT
trap 'printf "\nInterrupted.\n" >&2; exit 130' INT TERM

# --- Main ---
function main() {
    # Argument Parsing
    while [[ $# -gt 0 ]]; do
        case "${1}" in
            -o)       [[ -n "${2:-}" ]] || die "Option -o requires an argument" 2; OUTPUT="${2}"; shift 2 ;;
            -v)       VERBOSE=true; shift ;;
            -f)       FORCE=true; shift ;;
            --json)   JSON=true; shift ;;
            -h)       usage; exit 0 ;;
            -V)       printf '%s\n' "${VERSION}"; exit 0 ;;
            --)       shift; break ;;
            -*)       die "Unknown option: ${1}. Use -h for help" 2 ;;
            *)        break ;;
        esac
    done

    local input="${1:-}"
    if [[ -z "${input}" ]]; then
        usage >&2
        exit 2
    fi

    # Read Input
    local content
    if [[ "${input}" == "-" ]]; then
        if [[ -t 0 ]]; then
            die "No input on stdin. Pipe data or provide a file." 2
        fi
        content=$(cat)
    elif [[ -f "${input}" ]]; then
        content=$(<"${input}")
    else
        die "File not found: ${input}"
    fi

    log "Processing ${input}..."

    # Process (replace with your logic)
    local result
    result=$(printf '%s' "${content}" | tr '[:lower:]' '[:upper:]')

    # Output
    if [[ "${JSON}" == true ]]; then
        local escaped
        escaped=$(printf '%s' "${result}" | sed 's/\\/\\\\/g; s/"/\\"/g')
        printf '{"result":"%s","length":%d}\n' "${escaped}" "${#result}"
    elif [[ -n "${OUTPUT}" ]]; then
        if [[ -e "${OUTPUT}" && "${FORCE}" != true ]]; then
            die "${OUTPUT} exists. Use -f to overwrite"
        fi
        printf '%s' "${result}" > "${OUTPUT}"
        info "Written to ${OUTPUT}"
    else
        printf '%s\n' "${result}"
    fi
}

main "${@}"
