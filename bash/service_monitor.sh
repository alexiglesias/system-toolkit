#!/usr/bin/env bash
#
# service_monitor.sh — check whether a systemd service is active and alert if not.
#
# Designed to be run from cron (e.g. every 5 minutes). Writes structured log lines
# to /var/log/service_monitor.log and optionally posts to a Slack webhook.
#
# Usage:
#   sudo ./service_monitor.sh <service_name>
#   SLACK_WEBHOOK_URL=https://hooks.slack.com/... sudo ./service_monitor.sh nginx
#   sudo ./service_monitor.sh --restart nginx     # attempt restart on failure
#
# Exit codes:
#   0  service is active
#   1  invalid arguments
#   2  service is not active (and could not be restarted, if --restart was passed)
#   3  service is not active (no restart attempted)

set -euo pipefail

readonly SCRIPT_NAME="${0##*/}"
readonly LOG_FILE="${SERVICE_MONITOR_LOG:-/var/log/service_monitor.log}"
readonly SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

log() {
    local level="$1"; shift
    local line
    line="$(date --iso-8601=seconds) [$level] $*"
    echo "$line"
    # Append to log file if we have permission; silently skip if not.
    echo "$line" >> "$LOG_FILE" 2>/dev/null || true
}

slack_notify() {
    local message="$1"
    if [[ -z "$SLACK_WEBHOOK_URL" ]]; then
        return 0
    fi
    if ! command -v curl &>/dev/null; then
        log WARN "curl not installed; skipping Slack notification"
        return 0
    fi
    # Use --fail to surface HTTP errors, suppress output on success
    curl --silent --fail --show-error \
        -X POST \
        -H 'Content-Type: application/json' \
        --data "{\"text\":\"$message\"}" \
        "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 \
        || log WARN "Slack notification failed"
}

usage() {
    cat <<EOF
Usage:
    sudo $SCRIPT_NAME [--restart] <service_name>

Environment variables:
    SLACK_WEBHOOK_URL    if set, alerts are also posted to Slack
    SERVICE_MONITOR_LOG  log file path (default: /var/log/service_monitor.log)

Examples:
    sudo $SCRIPT_NAME nginx
    sudo $SCRIPT_NAME --restart nginx
    SLACK_WEBHOOK_URL=https://hooks.slack.com/... sudo $SCRIPT_NAME nginx
EOF
}

main() {
    local restart=false
    local service=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --restart) restart=true; shift ;;
            -h|--help) usage; exit 0 ;;
            -*) log ERROR "unknown flag: $1"; usage; exit 1 ;;
            *) service="$1"; shift ;;
        esac
    done

    if [[ -z "$service" ]]; then
        log ERROR "service name required"
        usage
        exit 1
    fi

    if systemctl is-active --quiet "$service"; then
        log INFO "service '$service' is active"
        exit 0
    fi

    log ERROR "service '$service' is DOWN on $(hostname)"
    slack_notify ":rotating_light: service \`$service\` is DOWN on \`$(hostname)\`"

    if [[ "$restart" == "true" ]]; then
        log INFO "attempting restart of '$service'"
        if systemctl restart "$service"; then
            sleep 2
            if systemctl is-active --quiet "$service"; then
                log INFO "service '$service' restarted successfully"
                slack_notify ":white_check_mark: service \`$service\` auto-recovered on \`$(hostname)\`"
                exit 0
            fi
        fi
        log ERROR "restart of '$service' failed"
        slack_notify ":x: service \`$service\` could not be restarted on \`$(hostname)\`"
        exit 2
    fi

    exit 3
}

main "$@"
