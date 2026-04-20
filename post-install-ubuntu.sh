#!/bin/bash
# Post-Install Ubuntu Server Setup Script
# Instaluje: Docker, Docker Compose, UFW, Fail2Ban, Nginx
# Nastavuje: SSH security, firewall rules, basic hardening

set -e

echo "=== Ubuntu Server Post-Install Setup ==="
echo ""

# Update system
echo "[1/7] Updating system packages..."
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y

# Install essentials
echo "[2/7] Installing essential packages..."
sudo apt install -y \
  curl \
  wget \
  git \
  vim \
  ufw \
  fail2ban \
  ca-certificates \
  gnupg \
  lsb-release

# Install Docker
echo "[3/7] Installing Docker..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
echo "   ✓ User '$USER' added to docker group (log out and back in for changes to take effect)"

# Enable UFW (firewall)
echo "[4/7] Configuring UFW firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp          # SSH
sudo ufw allow 80/tcp          # HTTP
sudo ufw allow 443/tcp         # HTTPS
sudo ufw --force enable
echo "   ✓ UFW enabled with SSH, HTTP, HTTPS allowed"

# Enable Fail2Ban
echo "[5/7] Configuring Fail2Ban..."
sudo systemctl enable fail2ban
sudo systemctl restart fail2ban
echo "   ✓ Fail2Ban enabled and started"

# SSH Security
echo "[6/7] Hardening SSH configuration..."
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

# Create sed commands for SSH hardening
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Add security settings if not present
if ! grep -q "PermitEmptyPasswords" /etc/ssh/sshd_config; then
  echo "PermitEmptyPasswords no" | sudo tee -a /etc/ssh/sshd_config > /dev/null
fi
if ! grep -q "MaxAuthTries" /etc/ssh/sshd_config; then
  echo "MaxAuthTries 3" | sudo tee -a /etc/ssh/sshd_config > /dev/null
fi

# Validate and restart SSH
sudo sshd -t && sudo systemctl restart ssh
echo "   ✓ SSH hardened: PasswordAuthentication disabled, RootLogin disabled"

# Summary
echo "[7/7] Setup complete!"
echo ""
echo "=== Summary ==="
echo "✓ System updated"
echo "✓ Docker installed and ready"
echo "✓ Docker Compose plugin installed"
echo "✓ UFW firewall enabled (SSH, HTTP, HTTPS allowed)"
echo "✓ Fail2Ban enabled"
echo "✓ SSH hardened (key-based auth only, root disabled)"
echo ""
echo "=== Next Steps ==="
echo "1. Log out and back in to use docker without sudo"
echo "2. Test SSH connection from your PC (should work with ed25519 key)"
echo "3. Create docker-compose.yml for your web + Hytale setup"
echo ""
echo "SSH from Windows PowerShell:"
echo "  ssh -i \$env:USERPROFILE\.ssh\id_ed25519 burymuru@192.168.50.144"
echo ""
