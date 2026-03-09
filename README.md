# CBT Pro

README ini khusus untuk deployment production `CBT Pro` di VPS `Ubuntu Server 22.04`.

## Asumsi deployment

- OS server: `Ubuntu Server 22.04 LTS`
- Direktori aplikasi: `/var/www/cbt_pro`
- User deploy: `deploy`
- Domain: `cbt.example.com`
- Reverse proxy: `Nginx`
- App server: `Gunicorn`
- Database: `MySQL`
- Queue broker: `Redis`

Sesuaikan seluruh placeholder di bawah dengan lingkungan server target.

## 1. Install paket sistem

Ubuntu 22.04 masih memakai Python bawaan `3.10`, jadi install `Python 3.12` dari `deadsnakes` terlebih dahulu.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

sudo apt install -y \
  git curl nginx redis-server mysql-server \
  certbot python3-certbot-nginx \
  build-essential pkg-config default-libmysqlclient-dev \
  libffi-dev libmagic1 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
  libpangoft2-1.0-0 libharfbuzz-subset0 \
  libgdk-pixbuf-2.0-0 shared-mime-info \
  python3.12 python3.12-venv python3.12-dev
```

Install Node.js LTS dari NodeSource agar kompatibel dengan `sass` yang dipakai project:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

Opsional firewall dasar:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 2. Buat user deploy dan clone repository

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
sudo install -d -o deploy -g deploy /var/www/cbt_pro
```

Clone repo:

```bash
sudo -iu deploy
git clone <URL_REPO_ANDA> /var/www/cbt_pro
cd /var/www/cbt_pro
```

## 3. Buat virtualenv dan install dependency Python

```bash
cd /var/www/cbt_pro
python3.12 -m venv .venv
source .venv/bin/activate
python --version
pip install --upgrade pip wheel
pip install -r requirements.txt
```

Jika sebelumnya `.venv` terbuat dari Python yang salah, hapus lalu buat ulang:

```bash
rm -rf /var/www/cbt_pro/.venv
```

## 4. Build asset frontend

File `static/css/main.css` tidak disimpan di Git, jadi CSS wajib dibuild di server.

```bash
cd /var/www/cbt_pro
npm ci
npm run build:css
```

Catatan:

- Sebagian asset frontend masih dimuat dari CDN publik saat runtime browser, termasuk Bootstrap JS, Alpine.js, Remix Icon, Axios, Chart.js, TinyMCE, dan Google Fonts.
- Untuk deployment intranet atau jaringan tanpa akses internet publik, asset tersebut perlu divendor ke `static/`.

## 5. Siapkan MySQL

Amankan instalasi MySQL:

```bash
sudo mysql_secure_installation
```

Buat database dan user aplikasi:

```bash
sudo mysql
```

```sql
CREATE DATABASE cbt_pro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cbt_user'@'127.0.0.1' IDENTIFIED BY 'ganti-password-yang-kuat';
GRANT ALL PRIVILEGES ON cbt_pro.* TO 'cbt_user'@'127.0.0.1';
FLUSH PRIVILEGES;
EXIT;
```

## 6. Aktifkan Redis

```bash
sudo systemctl enable redis-server --now
redis-cli ping
```

Output yang benar adalah `PONG`.

## 7. Siapkan direktori writable

```bash
cd /var/www/cbt_pro
mkdir -p logs media staticfiles
chmod 755 logs media staticfiles
```

## 8. Buat file environment production

Salin template:

```bash
cd /var/www/cbt_pro
cp .env.example .env
```

Isi `.env` minimal seperti berikut:

```dotenv
CBT_SITE_NAME="CBT Sekolah"
SECRET_KEY=ganti-dengan-secret-key-random
DEBUG=False
ALLOWED_HOSTS=cbt.example.com,www.cbt.example.com
CSRF_TRUSTED_ORIGINS=https://cbt.example.com,https://www.cbt.example.com
TIME_ZONE=Asia/Jakarta
LANGUAGE_CODE=id
USE_TZ=True

HTTPS_ENABLED=True
USE_X_FORWARDED_HOST=True
SECURE_PROXY_SSL_HEADER_ENABLED=True

DB_ENGINE=django.db.backends.mysql
DB_NAME=cbt_pro
DB_USER=cbt_user
DB_PASSWORD=password-database-anda
DB_HOST=127.0.0.1
DB_PORT=3306
DB_OPTIONS={"charset":"utf8mb4"}
DB_CONN_MAX_AGE=600
DB_CONN_HEALTH_CHECKS=True

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=akun-smtp@domainanda.com
EMAIL_HOST_PASSWORD=password-smtp-anda
DEFAULT_FROM_EMAIL="CBT Sekolah <noreply@cbt.example.com>"

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
CELERY_TIMEZONE=Asia/Jakarta
CELERY_TASK_SYNC_FALLBACK=True

MEDIA_URL=/media/
MEDIA_ROOT=media/
STATIC_URL=/static/
STATIC_ROOT=staticfiles/

TINYMCE_API_KEY=

USER_IMPORT_MAX_ROWS=5000
USER_IMPORT_CHUNK_SIZE=250
QUESTION_IMPORT_MAX_ROWS=10000
QUESTION_IMPORT_CHUNK_SIZE=200

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
X_FRAME_OPTIONS=DENY

LOG_LEVEL=INFO

ENABLE_SCREENSHOT_PROCTORING=False
SCREENSHOT_INTERVAL_SECONDS=300
MAX_VIOLATIONS_ALLOWED=3
```

Generate `SECRET_KEY`:

```bash
cd /var/www/cbt_pro
source .venv/bin/activate
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Jika HTTPS belum aktif, set sementara:

```dotenv
HTTPS_ENABLED=False
USE_X_FORWARDED_HOST=False
SECURE_PROXY_SSL_HEADER_ENABLED=False
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
```

Setelah HTTPS aktif, ubah lagi ke mode production aman.

## 9. Jalankan migrasi dan collectstatic

```bash
cd /var/www/cbt_pro
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
python manage.py createsuperuser
```

Opsional untuk staging/demo:

```bash
python manage.py seed
```

Jangan jalankan `seed` di production tanpa review karena command ini membuat akun default dan data contoh.

## 10. Buat service Gunicorn

Buat file `/etc/systemd/system/cbt_pro-gunicorn.service`:

```ini
[Unit]
Description=CBT Pro Gunicorn
After=network.target mysql.service redis-server.service

[Service]
User=deploy
Group=deploy
WorkingDirectory=/var/www/cbt_pro
EnvironmentFile=/var/www/cbt_pro/.env
ExecStart=/var/www/cbt_pro/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 11. Buat service Celery worker

Buat file `/etc/systemd/system/cbt_pro-celery.service`:

```ini
[Unit]
Description=CBT Pro Celery Worker
After=network.target redis-server.service mysql.service

[Service]
User=deploy
Group=deploy
WorkingDirectory=/var/www/cbt_pro
EnvironmentFile=/var/www/cbt_pro/.env
ExecStart=/var/www/cbt_pro/.venv/bin/celery -A config worker --loglevel=INFO
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Aktifkan service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cbt_pro-gunicorn --now
sudo systemctl enable cbt_pro-celery --now
sudo systemctl status cbt_pro-gunicorn
sudo systemctl status cbt_pro-celery
```

## 12. Konfigurasi Nginx

Buat file `/etc/nginx/sites-available/cbt_pro`:

```nginx
server {
    listen 80;
    server_name cbt.example.com www.cbt.example.com;

    client_max_body_size 25M;

    location /static/ {
        alias /var/www/cbt_pro/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location /media/ {
        alias /var/www/cbt_pro/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }
}
```

Aktifkan site:

```bash
sudo ln -sfn /etc/nginx/sites-available/cbt_pro /etc/nginx/sites-enabled/cbt_pro
sudo nginx -t
sudo systemctl enable nginx --now
sudo systemctl restart nginx
```

## 13. Aktifkan HTTPS dengan Let's Encrypt

```bash
sudo certbot --nginx -d cbt.example.com -d www.cbt.example.com
```

Sesudah sertifikat aktif:

- pastikan `.env` memakai `https://` di `CSRF_TRUSTED_ORIGINS`
- aktifkan kembali semua flag keamanan HTTPS di `.env`
- restart service

```bash
sudo systemctl restart cbt_pro-gunicorn cbt_pro-celery nginx
```

## 14. Verifikasi pasca deploy

```bash
curl -I -H "Host: cbt.example.com" http://127.0.0.1
curl -I https://cbt.example.com
sudo systemctl status nginx cbt_pro-gunicorn cbt_pro-celery redis-server mysql
```

Yang perlu berhasil:

- halaman login terbuka
- CSS termuat normal
- `admin/` bisa diakses
- upload media berjalan
- import user berjalan
- email keluar bila SMTP sudah diisi

Lihat log jika ada masalah:

```bash
sudo journalctl -u cbt_pro-gunicorn -f
sudo journalctl -u cbt_pro-celery -f
tail -f /var/www/cbt_pro/logs/django.log
```

## 15. Update deploy berikutnya

Setiap kali repository production menerima update baru, server juga harus ikut diperbarui. Jangan cukup `git pull` saja; jalankan seluruh langkah berikut agar dependency, migration, static file, dan service tetap sinkron dengan kode terbaru.

```bash
sudo -iu deploy
cd /var/www/cbt_pro
git pull
source .venv/bin/activate
pip install -r requirements.txt
npm ci
npm run build:css
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
exit
sudo systemctl restart cbt_pro-gunicorn cbt_pro-celery
```

Jika update hanya mengubah file Python atau template, langkah di atas tetap aman dipakai. Jika update membawa perubahan dependency, asset frontend, atau migration database, langkah ini menjadi wajib.

## 16. Troubleshooting singkat

- `Unable to locate package python3.12`: pastikan server benar `Ubuntu 22.04` dan repo `ppa:deadsnakes/ppa` sudah ditambahkan.
- `Could not find a version that satisfies the requirement autobahn==25.12.2`: virtualenv dibuat dari Python lama. Hapus `.venv`, lalu buat ulang dengan `python3.12 -m venv .venv`.
- `mysqlclient` gagal install: pastikan `build-essential`, `pkg-config`, `default-libmysqlclient-dev`, dan `python3.12-dev` sudah terpasang.
- `npm ci` gagal karena versi Node.js terlalu tua: pastikan Node.js dipasang dari NodeSource, bukan paket bawaan `Ubuntu 22.04`.
- CSS tidak muncul: jalankan `npm ci`, `npm run build:css`, lalu `python manage.py collectstatic --noinput`.
- UI terlihat rusak atau beberapa fitur frontend tidak berjalan di jaringan tertutup: browser klien kemungkinan tidak bisa memuat asset CDN yang masih dipakai aplikasi.
- `DisallowedHost`: isi `ALLOWED_HOSTS` belum sesuai domain.
- `CSRF verification failed`: cek `CSRF_TRUSTED_ORIGINS`, HTTPS, dan header `X-Forwarded-Proto` di Nginx.
- Redirect loop HTTP/HTTPS: biasanya flag `SECURE_SSL_REDIRECT=True` aktif saat HTTPS atau proxy belum siap.
- PDF sertifikat gagal dibuat: cek library sistem `libcairo2`, `libpango-1.0-0`, `libpangocairo-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz-subset0`, `libgdk-pixbuf-2.0-0`, dan `shared-mime-info`.
