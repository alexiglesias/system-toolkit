# Best practices learned from this toolkit

A short reference of the principles applied across these scripts. Most are
small individually, but together they're the difference between a "tutorial
script" and something you'd schedule on a real server.

## Bash

- **`set -euo pipefail` at the top of every script.**
  - `-e` exits on any unhandled error.
  - `-u` treats unset variables as an error (catches typos).
  - `-o pipefail` makes piped commands fail correctly (otherwise `cmd1 | cmd2`
    returns the status of `cmd2` only).
- **Always quote variable expansions:** `"$username"`, not `$username`.
  Prevents word-splitting bugs the moment someone passes a name with a space.
- **Use `[[ ... ]]` over `[ ... ]`** — safer, no word-splitting inside.
- **Functions for repeated logic**, even tiny ones — easier to grep, easier to
  test.
- **Structured log lines:** `YYYY-MM-DDTHH:MM:SS [LEVEL] message`. Costs
  nothing, makes `grep ERROR` postmortems trivial.
- **Exit codes are an API.** Return 0 for success, distinct non-zero codes for
  distinct failure modes. Cron and monitoring systems read these.
- **Detect missing dependencies before using them:** `command -v curl
  &>/dev/null || ...`.

## Python

- **`argparse` for CLI args**, never raw `sys.argv[1]`. You get `--help`,
  validation, and type conversion for free.
- **`logging` over `print`.** Levels (`DEBUG`, `INFO`, `WARN`, `ERROR`),
  configurable output, no rewrites later.
- **`pathlib.Path` over `os.path`** for new code. Type-safe, more readable.
- **Type hints on function signatures.** Free documentation; catches bugs in
  editors before runtime.
- **Return exit codes from `main()`** and call `sys.exit(main())`. Makes
  scripts testable as functions.
- **Catch the narrow exception**, not bare `except`. `OSError`, `ClientError`,
  `BotoCoreError` — the more specific, the better.

## Testing

- **`moto` over LocalStack for unit tests.** Faster, no external service, runs
  in CI without Docker.
- **Use `tmp_path` fixture** — automatic cleanup, no leaked files.
- **Test exit codes, not just side effects.** `assert main([...]) == 0`.
- **One assertion per test name.** A test called
  `test_archive_file_creates_gzip_and_removes_source` is self-documenting.

## Cron / scheduled jobs

- **Always use absolute paths** in cron — `$PATH` is minimal.
- **Redirect stderr too:** `>> log 2>&1`, not just `>> log`.
- **Send environment variables explicitly:**
  `SLACK_WEBHOOK_URL=... /path/to/script`. Cron doesn't have your shell env.
- **Log to a file the script owns.** Don't fight with logrotate over
  `/var/log/syslog`.

## AWS / boto3

- **Read credentials from the standard AWS chain.** Never hardcode
  `aws_access_key_id`. The chain checks env vars, then `~/.aws/credentials`,
  then instance metadata — works everywhere without code changes.
- **Honor `AWS_ENDPOINT_URL`.** Three lines of code that let the same script
  target LocalStack for development and real AWS for production.
- **Paginate.** `client.get_paginator('describe_instances')`, not
  `describe_instances()`. The non-paginated call truncates silently at 1000
  results.
- **Use IAM roles, not access keys, when running on EC2.** Access keys end up
  in git history. Roles don't.
