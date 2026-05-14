#!/usr/bin/env bash
#
# disk_usage_alert.sh — check filesystem usage and alert when a threshold is crossed.
#
# Usage:
#   ./disk_usage_alert.sh                       # all mounts, default 80% threshold
#   ./disk_usage_alert.sh --threshold 90        # 90% threshold
#   ./disk_usage_alert.sh --mount /             # check only the root mount
#
# Exit codes:
#   0  all monitored mounts below threshold
#   1  invalid arguments
#   2  one or more mounts at or above threshold

set -euo pipefail

readonly SCRIPT_NAME="${0##*/}"
readonly SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

log() {
    local level="$1"; shift
    printf '%s [%s] %s\n' "$(date --iso-8601=seconds)" "$level" "$*"
}

slack_notify() {
    local message="$1"
    [[ -z "$SLACK_WEBHOOK_URL" ]] && return 0
    command -v curl &>/dev/null || return 0
    curl --silent --fail -X POST \
        -H 'Content-Type: application/json' \
        --data "{\"text\":\"$message\"}" \
        "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
}

usage() {
    cat <<EOF
Usage:
    $SCRIPT_NAME [--threshold PCT] [--mount PATH]

Options:
    --threshold PCT   alert when usage >= PCT (default: 80)
    --mount PATH      check only this mount (default: all real filesystems)

Examples:
    $SCRIPT_NAME
    $SCRIPT_NAME --threshold 90
    $SCRIPT_NAME --mount / --threshold 75
EOF
}

main() {
    local threshold=80
    local mount=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --threshold) threshold="$2"; shift 2 ;;
            --mount) mount="$2"; shift 2 ;;
            -h|--help) usage; exit 0 ;;
            *) log ERROR "unknown argument: $1"; usage; exit 1 ;;
        esac
    done

    if ! [[ "$threshold" =~ ^[0-9]+$ ]] || (( threshold < 1 || threshold > 99 )); then
        log ERROR "threshold must be 1-99, got: $threshold"
        exit 1
    fi

    # df with -x filters out pseudo filesystems
    local df_output
    if [[ -n "$mount" ]]; then
        df_output=$(df -h --output=source,pcent,target "$mount" | tail -n +2)
    else
        df_output=$(df -h -x tmpfs -x devtmpfs -x squashfs --output=source,pcent,target | tail -n +2)
    fi

    local alerted=false
    while read -r source pcent target; do
        # pcent looks like "82%" — strip the %
        local pct="${pcent%\%}"
        if (( pct >= threshold )); then
            log WARN "$target ($source) at ${pct}% (threshold: ${threshold}%)"
            slack_notify ":warning: disk \`$target\` on \`$(hostname)\` at ${pct}% (threshold ${threshold}%)"
            alerted=true
        else
            log INFO "$target ($source) at ${pct}% — ok"
        fi
    done <<< "$df_output"

    if [[ "$alerted" == "true" ]]; then
        exit 2
    fi
    exit 0
}

main "$@"
