# Deploy to a VPS (Ubuntu/Debian)

Assumes you SSH into the server as a user with `sudo`.

## 1. Copy code to the server

**Option A — Git (recommended)**

On the server:

```bash
sudo mkdir -p /var/www
sudo chown $USER:$USER /var/www
cd /var/www
git clone YOUR_REPO_URL serendipity
cd serendipity
```

**Option B — rsync from your laptop**

```bash
rsync -avz --exclude .venv --exclude __pycache__ --exclude .git \
  /Users/n.meskar/Desktop/OtherProjects/serendipity/ \
  user@YOUR_SERVER_IP:/var/www/serendipity/
```

## 2. Python + dependencies

```bash
cd /var/www/serendipity
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Environment variables (`.env` on the server)

Create `/var/www/serendipity/.env` on the server with your **production** values:

```env
AVALAI_API_KEY=sk-your-real-key
AVALAI_BASE_URL=https://api.avalai.ir/v1
DEFAULT_MODEL=gpt-5.6-luna
MAX_HISTORY_TURNS=20
MAX_OUTPUT_TOKENS=500
```

Tips:

- Do **not** commit `.env` to git.
- No quotes around values (or the app strips them, but plain `KEY=value` is safest).
- After changing `.env`, restart the service (step 5).

Lock down permissions:

```bash
chmod 600 /var/www/serendipity/.env
sudo chown www-data:www-data /var/www/serendipity/.env
```

## 4. systemd service (runs on boot)

```bash
sudo cp /var/www/serendipity/deploy/serendipity.service /etc/systemd/system/
sudo chown -R www-data:www-data /var/www/serendipity
sudo systemctl daemon-reload
sudo systemctl enable serendipity
sudo systemctl start serendipity
sudo systemctl status serendipity
```

Logs:

```bash
sudo journalctl -u serendipity -f
```

## 5. Update code or env later

**New code:**

```bash
cd /var/www/serendipity
git pull          # or rsync again
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart serendipity
```

**Only env changed:**

```bash
nano /var/www/serendipity/.env
sudo systemctl restart serendipity
```

## 6. Nginx (optional, public HTTP)

```bash
sudo apt install -y nginx
sudo cp /var/www/serendipity/deploy/nginx-serendipity.conf /etc/nginx/sites-available/serendipity
# Edit server_name in that file
sudo ln -s /etc/nginx/sites-available/serendipity /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Open firewall if needed:

```bash
sudo ufw allow 80
sudo ufw allow 22
```

Test:

```bash
curl http://YOUR_SERVER_IP/health
```

## 7. What your Laravel app calls

Point the backend to:

- `http://YOUR_SERVER_IP/health`
- `http://YOUR_SERVER_IP/v1/bots/...`

(Or `https://api.yourdomain.com/...` once you add TLS with Certbot.)

## Quick checklist

- [ ] Code on server at `/var/www/serendipity`
- [ ] `.venv` + `pip install -r requirements.txt`
- [ ] `.env` with new `AVALAI_*` and model settings
- [ ] `systemctl start serendipity`
- [ ] `curl .../health` returns `{"status":"ok"}`
