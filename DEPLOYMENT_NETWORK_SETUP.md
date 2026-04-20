# Deployment & Network Setup Guide

**Project**: BMW OLAP & Data Mining Website  
**Domain**: kamen-industries.com  
**Deployment Target**: Debian 12 Home Server with Cloudflare + Docker  
**Status**: Pre-deployment planning checklist

---

## Table of Contents
1. [Phase 0A: Prerequisites (Current)](#phase-0a-prerequisites-current)
2. [Phase 0B: Home Network Setup](#phase-0b-home-network-setup)
3. [Phase 0C: Cloudflare Configuration](#phase-0c-cloudflare-configuration)
4. [Phase 0D: Production Docker Setup](#phase-0d-production-docker-setup)
5. [Phase 0E: Debian 12 Deployment](#phase-0e-debian-12-deployment)
6. [Phase 0F: SSL/TLS & Security](#phase-0f-ssltls--security)
7. [Verification Checklist](#verification-checklist)

---

## Phase 0A: Prerequisites (Current)

### What You Have ✅
- ✅ Domain: `kamen-industries.com` (purchased, not configured)
- ✅ Windows Dev: Docker Desktop with WSL2
- ✅ Target: Debian 12 on home server (8GB RAM, 4-core CPU)
- ✅ Docker infrastructure: docker-compose.yml + Dockerfile + requirements.txt ready

### What You Need to Determine

**1. Home Server Internet Connection**
- [ ] Is home internet IP **static** or **dynamic**?
  - **Static**: Same IP always (check with ISP)
  - **Dynamic**: Changes periodically (need DDNS service)
  - **How to check**: Go to `https://whatismyipaddress.com` → note the "IPv4 Address"

**2. Home Server Network Location**
- [ ] Is Debian 12 already set up on the home server machine?
- [ ] What's the LAN IP of that machine? (e.g., `192.168.1.100`)
- [ ] Can you SSH into it from Windows? (test: `ssh user@192.168.1.100`)

**3. Router Access**
- [ ] Do you have admin access to your home router?
- [ ] Can you port-forward from WAN to LAN?
  - (This allows Cloudflare → Internet → Router → Debian)

**ACTION ITEMS FOR PHASE 0A**:
```
[ ] Determine if home IP is static or dynamic
[ ] Find your current public IPv4 address
[ ] Confirm Debian 12 is installed on home server
[ ] Find Debian LAN IP address
[ ] Verify SSH access to Debian
[ ] Verify router admin access (username + password)
```

---

## Phase 0B: Home Network Setup

### B1: If Static IP ✅

**Steps**:
1. Note your current public IPv4 (from whatismyipaddress.com)
2. This IP will be your domain target
3. Skip B2 (DDNS), go to B3 (router port forwarding)

### B2: If Dynamic IP 🔄

**DDNS Setup** (if IP changes frequently):

Popular free DDNS services:
- **Duck DNS** (`duckdns.org`)
- **No-IP** (noip.com)
- **Cloudflare** (can use their API for auto-updates)

**Recommendation**: Use Cloudflare's own DDNS integration (simpler, no 3rd party needed).

**Steps**:
1. Install DDNS client on Debian:
   ```bash
   sudo apt install ddclient
   # OR use Cloudflare API script (simpler)
   ```
2. Configure to update Cloudflare DNS every 5 minutes
3. Document your DDNS update mechanism (which service + credentials)

**ACTION ITEMS FOR PHASE 0B**:
```
[ ] If DYNAMIC IP: Choose DDNS service (recommend Cloudflare API)
[ ] If DYNAMIC IP: Install + test DDNS on Debian
[ ] If DYNAMIC IP: Document DDNS credentials
[ ] Note your primary public IPv4 or DDNS hostname
```

### B3: Router Port Forwarding

**Goal**: Route incoming HTTP/HTTPS traffic (ports 80, 443) to Debian LAN IP

**Steps** (generic, check your router manual):

1. Access router admin panel:
   - URL: Usually `192.168.1.1` or `192.168.0.1` (check router label)
   - Username: Often `admin`, password: Check router label or ISP docs

2. Find "Port Forwarding" or "Virtual Server" section

3. Create TWO forwarding rules:

   **Rule 1 - HTTP**:
   ```
   Protocol: TCP
   External Port: 80
   Internal IP: [Debian LAN IP, e.g., 192.168.1.100]
   Internal Port: 80
   ```

   **Rule 2 - HTTPS**:
   ```
   Protocol: TCP
   External Port: 443
   Internal IP: [Debian LAN IP, e.g., 192.168.1.100]
   Internal Port: 443
   ```

4. Save & reboot router

**Testing port forwarding**:
```bash
# From external network (e.g., phone on 4G):
curl http://[your-public-ip]:80
curl https://[your-public-ip]:443 -k

# Should eventually return webpage (after Cloudflare setup)
```

**ACTION ITEMS FOR PHASE 0B**:
```
[ ] Access router admin panel
[ ] Create port forward rule for port 80 → Debian:80
[ ] Create port forward rule for port 443 → Debian:443
[ ] Test port forwarding (optional now, confirm after Cloudflare)
```

---

## Phase 0C: Cloudflare Configuration

### C1: Cloudflare Account Setup

**Steps**:
1. Log into Cloudflare (`cloudflare.com`)
2. Go to "Domains" → "Add site"
3. Enter: `kamen-industries.com`
4. Select free plan (sufficient for this project)
5. Follow prompts to update nameservers (at domain registrar)

### C2: DNS Records Configuration

**Goal**: Point `kamen-industries.com` → Your home server

**After Cloudflare is set up:**

1. Go to Cloudflare Dashboard → `kamen-industries.com`
2. Click "DNS" in sidebar
3. Add **ONE** A record:

   | Type | Name | Content | TTL | Proxy |
   |------|------|---------|-----|-------|
   | A | @ (or kamen-industries.com) | [Your public IP or DDNS hostname] | 3600 | 🟠 Proxied (Cloudflare) |

   **Example**:
   ```
   Type: A
   Name: @
   Content: 203.0.113.45 (replace with YOUR public IP)
   TTL: Auto
   Proxy: Proxied (orange cloud)
   ```

4. **Optional**: Add www subdomain:
   ```
   Type: CNAME
   Name: www
   Content: kamen-industries.com
   Proxy: Proxied
   ```

### C3: SSL/TLS Configuration

1. Go to Cloudflare Dashboard → "SSL/TLS"
2. **Encryption mode**: Select "Full (strict)"
3. This means:
   - Cloudflare handles public SSL (kamen-industries.com)
   - Debian server needs self-signed cert for Cloudflare→Debian connection

### C4: Page Rules (Optional Security)

1. Go to "Rules" → "Page Rules"
2. Optional, but good for security:
   ```
   Rule 1: https://*.kamen-industries.com/* → Always use HTTPS
   Rule 2: https://kamen-industries.com/* → Always use HTTPS
   ```

**ACTION ITEMS FOR PHASE 0C**:
```
[ ] Create Cloudflare account if not exists
[ ] Add kamen-industries.com to Cloudflare
[ ] Update domain registrar nameservers to Cloudflare
[ ] Create A record pointing to your public IP
[ ] Set SSL/TLS mode to "Full (strict)"
[ ] Wait 24-48 hours for DNS propagation
[ ] Test: ping kamen-industries.com (should resolve to your IP)
```

---

## Phase 0D: Production Docker Setup

### D1: docker-compose.yml for Production

**Current file** (Windows dev): Uses relative paths, localhost port 8080

**Needed changes for Debian**:

1. **Paths**: Change from Windows-relative to absolute Debian paths
2. **Ports**: Switch from 8080 to standard 80/443
3. **Environment**: Add domain, SSL cert paths
4. **Volumes**: Ensure PostgreSQL + DuckDB persist across reboots

**New docker-compose.prod.yml structure**:

```yaml
version: '3.8'

services:
  web:
    build:
      context: /home/user/OLAP-a-DM
      dockerfile: Dockerfile
    container_name: bmw_web
    restart: always
    ports:
      - "80:80"
      - "443:443"
    environment:
      - DB_HOST=postgres
      - DB_NAME=bmw_olap
      - DB_USER=bmw_user
      - DB_PASSWORD=bmw_password
      - DOMAIN=kamen-industries.com
      - TZ=Europe/Prague
    volumes:
      - /home/user/OLAP-a-DM/www:/var/www/html/www
      - /home/user/OLAP-a-DM/src:/var/www/html/src
      - /home/user/OLAP-a-DM/project:/var/www/html/project
      - /var/www/db:/var/www/db  # DuckDB files persist here
      - /etc/letsencrypt:/etc/letsencrypt  # SSL certs
    networks:
      - bmw_network
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:15-alpine
    container_name: bmw_postgres_db
    restart: always
    environment:
      - POSTGRES_DB=bmw_olap
      - POSTGRES_USER=bmw_user
      - POSTGRES_PASSWORD=bmw_password
      - TZ=Europe/Prague
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - bmw_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bmw_user -d bmw_olap"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
    driver: local

networks:
  bmw_network:
    driver: bridge
```

### D2: Apache VirtualHost Configuration for HTTPS

**File**: Create `/home/user/OLAP-a-DM/docker/apache-vhost.conf`

```apache
<VirtualHost *:80>
    ServerName kamen-industries.com
    ServerAlias www.kamen-industries.com
    
    # Redirect all HTTP → HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</VirtualHost>

<VirtualHost *:443>
    ServerName kamen-industries.com
    ServerAlias www.kamen-industries.com
    
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/kamen-industries.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/kamen-industries.com/privkey.pem
    
    DocumentRoot /var/www/html/www
    
    <Directory /var/www/html/www>
        AllowOverride All
        Require all granted
    </Directory>
    
    # PHP handling
    <FilesMatch \.php$>
        SetHandler application/x-httpd-php
    </FilesMatch>
</VirtualHost>
```

**Mount in Dockerfile**:
```dockerfile
COPY docker/apache-vhost.conf /etc/apache2/sites-available/kamen-industries.conf
RUN a2ensite kamen-industries && a2dissite 000-default
```

**ACTION ITEMS FOR PHASE 0D**:
```
[ ] Create docker-compose.prod.yml with absolute paths
[ ] Create Apache vhost config with HTTPS
[ ] Update Dockerfile to include vhost config
[ ] Test locally on Windows first (if possible)
```

---

## Phase 0E: Debian 12 Deployment

### E1: Pre-Deployment Checklist on Debian

1. **System prep**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y docker.io docker-compose git curl wget
   sudo usermod -aG docker $USER  # Run docker without sudo
   ```

2. **Directory structure**:
   ```bash
   # Create persistent volume directories
   sudo mkdir -p /var/www/db
   sudo chmod 777 /var/www/db
   
   # Clone or copy project
   cd /home/user
   git clone https://github.com/your-username/OLAP-a-DM.git
   cd OLAP-a-DM
   ```

3. **Environment variables**:
   ```bash
   # Create .env file for docker-compose
   cat > .env << EOF
   DB_NAME=bmw_olap
   DB_USER=bmw_user
   DB_PASSWORD=bmw_password
   DOMAIN=kamen-industries.com
   TZ=Europe/Prague
   EOF
   ```

### E2: SSL Certificate Setup (Let's Encrypt)

**Option A: Certbot (Automated)**

```bash
# Install
sudo apt install -y certbot python3-certbot-apache

# Generate cert (before starting Docker)
sudo certbot certonly --standalone \
  -d kamen-industries.com \
  -d www.kamen-industries.com \
  --email your-email@example.com \
  --agree-tos -n

# Certificates will be in: /etc/letsencrypt/live/kamen-industries.com/
```

**Option B: Self-Signed (Temporary, for testing)**

```bash
sudo mkdir -p /etc/letsencrypt/live/kamen-industries.com/

sudo openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout /etc/letsencrypt/live/kamen-industries.com/privkey.pem \
  -out /etc/letsencrypt/live/kamen-industries.com/fullchain.pem \
  -subj "/CN=kamen-industries.com"
```

### E3: Start Docker Containers

```bash
# Use production compose file (or rename docker-compose.yml)
docker-compose -f docker-compose.prod.yml up -d

# Verify services are running
docker-compose ps
docker logs bmw_web     # Check web service
docker logs bmw_postgres_db  # Check database
```

### E4: Auto-Start on Boot

```bash
# Enable Docker service
sudo systemctl enable docker

# Create systemd service for auto-start containers
sudo tee /etc/systemd/system/docker-compose-app.service > /dev/null << EOF
[Unit]
Description=BMW OLAP Docker Compose App
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/OLAP-a-DM
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable docker-compose-app
```

**ACTION ITEMS FOR PHASE 0E**:
```
[ ] Install Docker + Docker Compose on Debian
[ ] Clone project to /home/user/OLAP-a-DM
[ ] Create .env with database credentials
[ ] Generate SSL certificate (Certbot or self-signed)
[ ] Place cert at /etc/letsencrypt/live/kamen-industries.com/
[ ] Test docker-compose up locally
[ ] Enable auto-start on boot
[ ] Reboot Debian machine and verify containers still running
```

---

## Phase 0F: SSL/TLS & Security

### F1: Cloudflare Full (Strict) SSL

**What this means**:

```
Client Browser
    ↓ HTTPS (Cloudflare cert)
Cloudflare Edge
    ↓ HTTPS (Your cert)
Debian Server
```

Your server needs a valid cert for the Cloudflare→Server connection.

**Options**:
1. **LetsEncrypt (Recommended)**: Free, auto-renewing, trusted
   - Use Certbot (Phase 0E, Option A)
   - Will auto-renew 30 days before expiry

2. **Self-Signed (Testing only)**: 
   - Browser will show "untrusted" warning on direct access
   - But Cloudflare clients connect fine (they trust your cert via their tunnel)

### F2: Security Hardening

**Firewall Rules**:
```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH (restrict to your IP)
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

**Restrict SSH**:
```bash
# Edit /etc/ssh/sshd_config
sudo nano /etc/ssh/sshd_config

# Uncomment and set:
# Port 2222          # Change default (optional)
# PermitRootLogin no
# PasswordAuthentication no  # Use key-based auth only

sudo systemctl restart ssh
```

**Cloudflare WAF (Web Application Firewall)**:
1. Go to Cloudflare Dashboard → "Security" → "WAF"
2. Enable "Managed Ruleset" (protects against common attacks)
3. Optional: Create custom rules if attacks detected

### F3: Monitoring & Health Checks

**Cloudflare Health Checks** (optional):
1. Go to Cloudflare DNS settings
2. Enable health checks on your A record
3. Cloudflare will alert if site goes down

**Local monitoring**:
```bash
# Script to monitor containers (crontab every 5 min)
cat > /home/user/check-containers.sh << 'EOF'
#!/bin/bash
if ! docker ps | grep -q bmw_web; then
  echo "Web container down!" | mail -s "Alert" user@example.com
fi
EOF

chmod +x /home/user/check-containers.sh

# Add to crontab
crontab -e
# Add: */5 * * * * /home/user/check-containers.sh
```

**ACTION ITEMS FOR PHASE 0F**:
```
[ ] Set up LetsEncrypt (Certbot) OR self-signed cert
[ ] Configure firewall to allow 80, 443, 22 only
[ ] Restrict SSH (disable password auth, use keys)
[ ] Enable Cloudflare WAF
[ ] Test HTTPS access from public IP
[ ] Set up monitoring/alerting (optional)
```

---

## Verification Checklist

### ✅ Before DNS Goes Live

```
[ ] Cloudflare account created and configured
[ ] Domain nameservers updated to Cloudflare
[ ] A record pointing to your public IP
[ ] SSH key-based auth working on Debian
[ ] Docker + docker-compose installed
[ ] SSL certificate generated (Certbot or self-signed)
[ ] Port forwarding 80→Debian, 443→Debian configured
[ ] Firewall set to allow 80, 443, 22
[ ] docker-compose up succeeds without errors
[ ] Containers visible: docker ps
```

### ✅ After DNS Propagates (24-48 hours)

```
[ ] ping kamen-industries.com resolves correctly
[ ] curl -k https://kamen-industries.com returns webpage (or 502 initially)
[ ] Browser access: https://kamen-industries.com (should show padlock)
[ ] Cloudflare dashboard shows "active"
[ ] Database connections working (check logs)
[ ] HTTPS redirects HTTP automatically
```

### ✅ Security Verification

```
[ ] nmap from external shows only 80, 443 open
[ ] SSH works with key, not password
[ ] Cloudflare WAF rules active
[ ] Containers auto-restart if crashed
```

### ✅ Accessibility from Classmates

```
[ ] Classmate on campus WiFi can access https://kamen-industries.com
[ ] Classmate on 4G can access https://kamen-industries.com
[ ] Examiner from any network can access https://kamen-industries.com
```

---

## Implementation Timeline

**Phase 0A** (Prerequisites): 1 hour
- Determine IP type (static/dynamic)
- Gather router access
- SSH into Debian

**Phase 0B** (Home Network): 1-2 hours
- Set up DDNS (if dynamic)
- Configure port forwarding
- Test locally

**Phase 0C** (Cloudflare): 30 minutes + 24-48 hour DNS wait
- Create account
- Add domain
- Configure DNS

**Phase 0D** (Docker Prod): 2 hours
- Create production docker-compose
- Set up Apache vhost
- Test locally

**Phase 0E** (Debian Deploy): 2-3 hours
- Install Docker
- Deploy containers
- Auto-start setup

**Phase 0F** (Security): 1-2 hours
- SSL setup
- Firewall + SSH hardening
- Monitoring

**Total estimated**: 8-15 hours (plus 24-48h DNS wait)

---

## Quick Reference: Key Credentials & Configs

| Item | Value | Where |
|------|-------|-------|
| Domain | kamen-industries.com | Cloudflare |
| Debian LAN IP | [Your IP] | Router, `ip addr` |
| Public IP | [Your IP] | whatismyipaddress.com |
| DB User | bmw_user | .env |
| DB Password | bmw_password | .env (~CHANGE for prod) |
| SSH User | user | Debian |
| Router Admin URL | 192.168.1.1 | Router label |
| Cloudflare API Token | [Generate in account] | Cloudflare → API |

---

## Next Steps

**Immediate** (now):
1. Complete Phase 0A checklist (prerequisites)
2. Determine static vs dynamic IP
3. Document home network info

**Before Deployment** (1-2 weeks):
1. Work through Phases 0B-0E
2. Deploy to Debian
3. Verify DNS + HTTPS working

**After Deployment**:
1. Proceed with Phase 1-8 (backend/frontend/OLAP)
2. Share deployment URL with classmates

---

**Document Status**: Template for deployment  
**Created**: 2026-04-17  
**Updated**: As needed during Phase 0 execution
