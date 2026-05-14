# -*- mode: ruby -*-
# vi: set ft=ruby :

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
    vb.memory = 1024
    vb.cpus = 1
    vb.customize ["modifyvm", :id, "--audio", "none"]
  end

  # ----- VMware Fusion provider (Apple Silicon) -----
  config.vm.provider "vmware_desktop" do |vmware, override|
    override.vm.box = "spox/ubuntu-arm"
    override.vm.box_version = "1.0.0"
    vmware.gui = false
    vmware.allowlist_verified = true
    vmware.memory = 1024
    vmware.cpus = 1
  end

  # ----- Provisioning (runs for both providers) -----
  config.vm.provision "shell", inline: <<-SHELL
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y git curl jq python3 python3-pip python3-venv nginx

    if [ ! -d /opt/toolkit-venv ]; then
      python3 -m venv /opt/toolkit-venv
      /opt/toolkit-venv/bin/pip install --upgrade pip
      /opt/toolkit-venv/bin/pip install -r /vagrant/requirements.txt
    fi

    chmod +x /vagrant/bash/*.sh
    systemctl enable --now nginx
  SHELL
end
