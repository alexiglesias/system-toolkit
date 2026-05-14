#!/usr/bin/env bash
#
# user_manager.sh — create or delete local Linux users, optionally assigning a group.
#
# Usage:
#   sudo ./user_manager.sh create <username> [group]
#   sudo ./user_manager.sh delete <username>
#   sudo ./user_manager.sh list
#
# Exit codes:
#   0  success
#   1  invalid arguments
#   2  user already exists (on create) or does not exist (on delete)
#   3  must run as root
#   4  underlying useradd/userdel/usermod command failed

set -euo pipefail

readonly SCRIPT_NAME="${0##*/}"

log() {
    # Structured log line: timestamp + level + message
    local level="$1"; shift
    printf '%s [%s] %s\n' "$(date --iso-8601=seconds)" "$level" "$*"
}

usage() {
    cat <<EOF
Usage:
    sudo $SCRIPT_NAME create <username> [group]
    sudo $SCRIPT_NAME delete <username>
    sudo $SCRIPT_NAME list

Examples:
    sudo $SCRIPT_NAME create alice
    sudo $SCRIPT_NAME create alice sudo
    sudo $SCRIPT_NAME delete alice
    sudo $SCRIPT_NAME list
EOF
}

require_root() {
    if [[ $EUID -ne 0 ]]; then
        log ERROR "must be run as root (try: sudo $SCRIPT_NAME ...)"
        exit 3
    fi
}

user_exists() {
    id "$1" &>/dev/null
}

group_exists() {
    getent group "$1" &>/dev/null
}

create_user() {
    local username="$1"
    local group="${2:-}"

    if user_exists "$username"; then
        log ERROR "user '$username' already exists"
        exit 2
    fi

    if ! useradd --create-home --shell /bin/bash "$username"; then
        log ERROR "useradd failed for '$username'"
        exit 4
    fi
    log INFO "created user '$username' with home directory"

    if [[ -n "$group" ]]; then
        if ! group_exists "$group"; then
            log ERROR "group '$group' does not exist"
            exit 2
        fi
        if ! usermod --append --groups "$group" "$username"; then
            log ERROR "usermod failed for '$username' -> '$group'"
            exit 4
        fi
        log INFO "added '$username' to group '$group'"
    fi
}

delete_user() {
    local username="$1"

    if ! user_exists "$username"; then
        log ERROR "user '$username' does not exist"
        exit 2
    fi

    if ! userdel --remove "$username"; then
        log ERROR "userdel failed for '$username'"
        exit 4
    fi
    log INFO "deleted user '$username' and home directory"
}

list_users() {
    # Show only human users (UID >= 1000, excluding 'nobody')
    awk -F: '$3 >= 1000 && $1 != "nobody" { printf "%-20s uid=%s home=%s shell=%s\n", $1, $3, $6, $7 }' /etc/passwd
}

main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local action="$1"
    case "$action" in
        create)
            require_root
            if [[ $# -lt 2 ]]; then
                log ERROR "create requires a username"
                usage
                exit 1
            fi
            create_user "$2" "${3:-}"
            ;;
        delete)
            require_root
            if [[ $# -lt 2 ]]; then
                log ERROR "delete requires a username"
                usage
                exit 1
            fi
            delete_user "$2"
            ;;
        list)
            list_users
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            log ERROR "unknown action: $action"
            usage
            exit 1
            ;;
    esac
}

main "$@"
