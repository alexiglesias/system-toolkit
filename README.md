# sysadmin-toolkit

> Bash and Python automation scripts for everyday Linux sysadmin and DevOps tasks.
> Local Ubuntu VM via Vagrant + VirtualBox. Cloud scripts work against LocalStack
> or real AWS. Tested with pytest and moto.

[![tests](https://img.shields.io/badge/tests-24%20passing-brightgreen)](./tests)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

## What's in here

Six small but production-style automation scripts grouped by language. Every
script uses structured logging, proper argument parsing, and meaningful exit
codes.

| Script | Purpose |
|---|---|
| `bash/user_manager.sh` | Create, delete, and list local users, with group assignment |
| `bash/service_monitor.sh` | Check a systemd service, alert to Slack, optionally auto-restart |
| `bash/disk_usage_alert.sh` | Warn when filesystems cross a usage threshold |
| `python/log_cleaner.py` | Archive log files older than N days (with gzip compression) |
| `python/log_parser.py` | Parse Nginx/Apache access logs: top IPs, URLs, status codes |
| `python/ec2_inventory.py` | List EC2 instances across regions (real AWS or LocalStack) |

## Architecture

```mermaid
flowchart LR
    HOST["host machine"]

    subgraph VM["VAGRANT VM"]
        CRON["cron"]
        BASH["bash / scripts<br/>user · service · disk"]
        PYTHON["python / scripts<br/>logs · EC2 inventory"]
    end

    SLACK["Slack webhook"]
    LS["LocalStack"]
    AWS["Real AWS"]

    HOST -->|vagrant up| CRON
    CRON -->|scheduled| BASH
    CRON -->|scheduled| PYTHON
    BASH -->|optional| SLACK
    PYTHON -->|optional| LS
    PYTHON -->|optional| AWS

    classDef bash   fill:#fff0e6,stroke:#e65100,color:#bf360c
    classDef py     fill:#f1f8e9,stroke:#43a047,color:#1b5e20
    classDef slack  fill:#fffde7,stroke:#f9a825,color:#5d4037
    classDef cloud  fill:#7b1fa2,stroke:#6a1b9a,color:#ffffff
    classDef host   fill:#e8f5e9,stroke:#388e3c,color:#1b5e20
    classDef cron   fill:#f5f5f5,stroke:#9e9e9e,color:#424242

    class HOST host
    class CRON cron
    class BASH bash
    class PYTHON py
    class SLACK slack
    class LS,AWS cloud

    linkStyle 0 stroke:#1976d2,stroke-dasharray:5 3
    linkStyle 1 stroke:#9e9e9e
    linkStyle 2 stroke:#9e9e9e
    linkStyle 3 stroke:#e65100
    linkStyle 4 stroke:#43a047
    linkStyle 5 stroke:#43a047
```

The VM is the runtime. LocalStack runs on the host (or inside the VM) and
emulates the AWS API so the boto3 scripts work offline at zero cost.

## Quick start

```bash
# 1. Bring up the VM (VirtualBox by default — no paid software)
vagrant up
vagrant ssh
cd /vagrant
source /opt/toolkit-venv/bin/activate

# 2. Run a script
sudo ./bash/user_manager.sh create alice sudo
sudo ./bash/service_monitor.sh nginx

# 3. Run the tests
python3 -m pytest tests/ -v
```

Or with the Makefile:

```bash
make vm-up        # bring up the VM
make test         # run the tests
make localstack-up  # start LocalStack for ec2_inventory.py
```

## Usage examples

### user_manager.sh

```bash
$ sudo ./bash/user_manager.sh create alice sudo
2026-05-14T07:30:12+00:00 [INFO] created user 'alice' with home directory
2026-05-14T07:30:12+00:00 [INFO] added 'alice' to group 'sudo'

$ sudo ./bash/user_manager.sh list
alice                uid=1001 home=/home/alice shell=/bin/bash
```

### service_monitor.sh

```bash
$ sudo ./bash/service_monitor.sh nginx
2026-05-14T07:31:05+00:00 [INFO] service 'nginx' is active

$ SLACK_WEBHOOK_URL=https://hooks.slack.com/... \
    sudo ./bash/service_monitor.sh --restart nginx
# Auto-recovers if nginx is down, posts to Slack on both failure and recovery
```

### log_parser.py

```bash
$ python3 python/log_parser.py --log /var/log/nginx/access.log --top 5
Lines processed: 14523/14523

Top IPs:
       312  1.2.3.4
       287  5.6.7.8
       ...

Top URLs:
      4012  /api/v1/users
      3891  /index.html
      ...

Status codes:
  200: 13104
  404: 982
  500: 437
```

### ec2_inventory.py (against LocalStack)

```bash
$ make localstack-up
$ AWS_ENDPOINT_URL=http://localhost:4566 \
  AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
  python3 python/ec2_inventory.py --regions us-east-1 --format json
```

## Scheduling with cron

Cron jobs are **automatically installed** during `vagrant up`. The schedule is defined in [`docs/crontab`](docs/crontab).

To view active jobs:
```bash
vagrant ssh
crontab -l
```

### Slack alerts (optional)

If you want `service_monitor.sh` to post alerts to Slack, set your webhook URL before provisioning:

**Option 1: Environment variable (persistent)**
```bash
# In your shell before vagrant up
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
vagrant up
```

**Option 2: Edit the crontab file directly**
```bash
# Edit docs/crontab and add your webhook URL:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

*/5 * * * * /vagrant/bash/service_monitor.sh --restart nginx
```

Then re-provision:
```bash
vagrant up --provision
```

Without a webhook URL, scripts still run normally—they just won't post to Slack.

### View cron logs

```bash
vagrant ssh
sudo tail -f /var/log/toolkit-*.log
```

### Modify the schedule

Edit [`docs/crontab`](docs/crontab) and re-provision:
```bash
vagrant up --provision
```

## LocalStack and AWS: Seamless transition

All scripts work identically against LocalStack or real AWS. To pivot between them just change the endpoint:

### LocalStack (free, local)
```bash
AWS_ENDPOINT_URL=http://localhost:4566 \
AWS_ACCESS_KEY_ID=test \
AWS_SECRET_ACCESS_KEY=test \
python3 python/ec2_inventory.py --regions us-east-1
```

### Production (Real AWS)
```bash
# Point to real AWS 
AWS_ACCESS_KEY_ID=AKIA... \
AWS_SECRET_ACCESS_KEY=... \
AWS_DEFAULT_REGION=us-east-1 \
python3 python/ec2_inventory.py --regions us-east-1 us-west-2
```

Same code, same API calls, zero environment-specific logic. This is the pattern for safe cloud automation.

## Testing

24 tests covering the Python scripts, with moto mocking the AWS calls so the
tests run offline and never touch a real account.

```bash
$ python3 -m pytest tests/ -v
============================= test session starts ==============================
collected 24 items

tests/test_ec2_inventory.py::test_list_instances_returns_empty_when_no_instances PASSED
tests/test_ec2_inventory.py::test_list_instances_returns_running_instance PASSED
...
============================== 24 passed in 4.80s ==============================
```

## Project layout

```
sysadmin-toolkit/
├── Vagrantfile            # VirtualBox-based Ubuntu VM (free, cross-platform)
├── docker-compose.yml     # LocalStack for AWS emulation
├── Makefile               # vm-up, test, localstack-up, ...
├── requirements.txt
├── requirements-dev.txt
├── bash/
│   ├── user_manager.sh
│   ├── service_monitor.sh
│   └── disk_usage_alert.sh
├── python/
│   ├── log_cleaner.py
│   ├── log_parser.py
│   └── ec2_inventory.py
├── tests/
│   ├── test_log_cleaner.py
│   ├── test_log_parser.py
│   └── test_ec2_inventory.py
└── docs/
    ├── crontab
    └── setup.md
```

## Requirements

- **Vagrant 2.4+**
- **One of the following hypervisors:**
  - **VirtualBox 7+** — free, works on Linux, Windows, and Intel Mac
  - **VMware Fusion** — free for personal use since 2024, works on Apple Silicon Mac
- **Python 3.10+** on the host (only needed to run tests outside the VM)
- **Docker** (optional, only for LocalStack)

Vagrant auto-detects whichever hypervisor you have installed. See
[`docs/setup.md`](docs/setup.md) for per-OS install instructions.

## License

MIT — see [LICENSE](./LICENSE).
