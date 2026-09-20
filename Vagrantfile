# -*- mode: ruby -*- 
# vi: set ft=ruby :
#
# Vagrantfile for the sysadmin-toolkit lab VM.
#
# Supports two providers:
#   - VirtualBox       (free, works on Linux/Windows/Intel Mac)
#   - VMware Fusion    (free for personal use as of 2024, works on Apple Silicon)
#
# Vagrant auto-detects which provider is installed. To force one explicitly:
#   vagrant up --provider=virtualbox
#   vagrant up --provider=vmware_desktop
#
# Or set it persistently in your shell:
#   export VAGRANT_DEFAULT_PROVIDER=vmware_desktop

Vagrant.configure("2") do |config|
  config.vm.hostname = "sysadmin-toolkit"
  config.vm.network "private_network", ip: "192.168.56.10"
  config.vm.synced_folder ".", "/vagrant"

  # ----- VirtualBox provider (default for Linux/Windows/Intel Mac) -----
  config.vm.provider "virtualbox" do |vb, override|
    override.vm.box = "ubuntu/jammy64"
    vb.name = "sysadmin-toolkit"
    vb.memory = 2048
    vb.cpus = 2
    vb.customize ["modifyvm", :id, "--audio", "none"]
  end

  # ----- VMware Fusion provider (Apple Silicon) -----
  config.vm.provider "vmware_desktop" do |vmware, override|
    override.vm.box = "bento/ubuntu-22.04"
    vmware.allowlist_verified = true
    vmware.memory = 2048
    vmware.cpus = 2
  end

# ----- Provisioning (runs for both providers) -----
config.vm.provision "shell", inline: <<-SHELL
  set -euo pipefail
  export DEBIAN_FRONTEND=noninteractive

  apt-get update
  apt-get install -y \
    git curl jq ca-certificates gnupg \
    python3.10 python3.10-venv python3.10-dev \
    python3-pip \
    nginx

  # ----- Install Docker from official repo -----
  install -m 0755 -d /etc/apt/keyrings
  if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
  fi

  UBUNTU_CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
  ARCH=$(dpkg --print-architecture)
  echo "deb [arch=$ARCH signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $UBUNTU_CODENAME stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  usermod -aG docker vagrant
  systemctl enable --now docker

  # ----- Python venv -----
  if [ ! -d /opt/toolkit-venv ]; then
    python3.10 -m venv /opt/toolkit-venv
  fi
  /opt/toolkit-venv/bin/pip install --upgrade pip
  /opt/toolkit-venv/bin/pip install -r /vagrant/requirements-dev.txt

  chmod +x /vagrant/bash/*.sh
  systemctl enable --now nginx

  # ----- Install cron jobs -----
  crontab -u vagrant /vagrant/docs/crontab
  echo "Cron jobs installed and active"
SHELL

