# Setup

This project supports two free hypervisors. Use whichever matches your OS.

## Linux / Windows / Intel Mac → VirtualBox

VirtualBox is free, cross-platform, and the most widely supported Vagrant
provider. Recommended for everyone except Apple Silicon users.

```bash
# macOS (Intel)
brew install --cask virtualbox vagrant

# Ubuntu / Debian
sudo apt-get install virtualbox vagrant

# Windows
# Download from virtualbox.org and vagrantup.com
```

Then from the repo root:

```bash
vagrant up
vagrant ssh
```

## Apple Silicon Mac (M1/M2/M3/M4) → VMware Fusion

VMware Fusion has been free for personal use since November 2024 and runs
natively on Apple Silicon. Sign up for a free Broadcom account to download.

```bash
# Install Fusion from https://www.vmware.com/products/fusion.html
brew install --cask vagrant
vagrant plugin install vagrant-vmware-desktop
```

Then from the repo root:

```bash
vagrant up                    # auto-detects Fusion
vagrant ssh
```

To make the choice explicit (useful if you ever install both):

```bash
export VAGRANT_DEFAULT_PROVIDER=vmware_desktop
vagrant up
```

## Verify the VM is healthy

After `vagrant up`, inside the VM:

```bash
source /opt/toolkit-venv/bin/activate
cd /vagrant
python3 -m pytest tests/ -v   # should show 24 passing
```

## LocalStack on the host (optional)

LocalStack runs in Docker on your host machine. The Python boto3 scripts in
the VM can reach it across the private network via `AWS_ENDPOINT_URL`:

```bash
# On the host:
docker compose up -d

# Inside the VM:
AWS_ENDPOINT_URL=http://192.168.56.1:4566 \
  AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
  python3 python/ec2_inventory.py --regions us-east-1
```

The IP `192.168.56.1` is the host as seen from a VirtualBox VM. For VMware
Fusion the host IP is typically `192.168.56.1` as well since we're using the
same private network range, but check with `ip route show default` inside
the VM if anything seems off.
