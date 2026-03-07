# CBT Pro

CBT Pro adalah aplikasi Computer-Based Testing berbasis Django dengan modul utama untuk autentikasi multi-role, bank soal, manajemen ujian, attempt siswa, monitoring anti-cheat, hasil ujian, analitik, impor user/soal, dan branding sistem.

## Hasil analisis proyek

- Stack utama: Django 6, MySQL, Redis, Celery, Nginx, Gunicorn, SCSS via `sass` + `npm`.
- Domain app yang aktif: `accounts`, `users`, `subjects`, `questions`, `exams`, `attempts`, `monitoring`, `results`, `notifications`, `analytics`, `dashboard`, `core`.
- Database runtime mengikuti `config/settings.py` dan `.env.example`, yaitu `django.db.backends.mysql`. Beberapa dokumen di folder `docs/` masih memuat catatan historis seperti PostgreSQL, jadi untuk deployment ikuti konfigurasi kode, bukan dokumen lama tersebut.
- Background job yang benar-benar dipakai saat ini adalah task Celery untuk pengiriman kredensial email hasil import user di `apps/users/tasks.py`. Jika Redis/Celery tidak tersedia, aplikasi masih punya fallback sinkron melalui `apps/core/tasking.py`, tetapi worker tetap direkomendasikan untuk production.
- `celery beat` belum diperlukan saat ini. `django-celery-beat` ada di `requirements.txt`, tetapi belum dipakai pada `INSTALLED_APPS` dan tidak ada periodic task aktif.
- Monitoring real-time saat ini memakai endpoint HTTP polling. Consumer Channels memang ada di `apps/monitoring/consumers.py`, tetapi wiring ASGI/Channels belum lengkap, jadi deployment production saat ini cukup memakai WSGI (`gunicorn`) dan tidak butuh Daphne/Uvicorn/WebSocket gateway.
- File media dipakai untuk branding, import/export, dan screenshot proctoring. Direktori `media/`, `logs/`, dan `staticfiles/` harus writable oleh user service.
- Build CSS wajib dijalankan di server. File hasil compile `static/css/main.css` dipakai oleh template, tetapi folder `static/css/` tidak disimpan di Git.
- Command bootstrap data tersedia di `apps/core/management/commands/seed.py`. Ini cocok untuk staging/demo, bukan production, karena membuat akun default dengan password yang harus segera diganti.

## Topologi deployment yang direkomendasikan

- OS: Ubuntu 24.04 LTS direkomendasikan.
- Python: 3.12+.
- Lokasi project: `/var/www/cbt_pro`.
- Reverse proxy: Nginx.
- App server: Gunicorn di `127.0.0.1:8000`.
- Database: MySQL atau MariaDB kompatibel MySQL.
- Queue broker/result backend: Redis.
- Service manager: systemd.

Contoh di bawah mengasumsikan:

- domain: `cbt.example.com`
- user deploy: `deploy`
- repo: `<URL_REPO_ANDA>`

Ganti semua placeholder tersebut sesuai server Anda.

## 1. Persiapan server

Jika server masih baru, siapkan paket dasar berikut:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  git curl nginx redis-server mysql-server \
  python3 python3-venv python3-dev \
  build-essential pkg-config default-libmysqlclient-dev \
  libffi-dev libmagic1 libcairo2 libpango-1.0-0 \
  libgdk-pixbuf-2.0-0 shared-mime-info \
  nodejs npm
```

Catatan:

- Jika Anda memakai Ubuntu 22.04, siapkan Python 3.12+ terlebih dahulu sebelum membuat virtualenv.
- Jika Anda memakai database/Redis managed service, bagian instalasi `mysql-server` dan `redis-server` boleh dilewati.

Opsional, aktifkan firewall dasar:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 2. Clone repo ke `/var/www/cbt_pro`

Jika user `deploy` belum ada, buat dulu. Jika sudah ada, lewati langkah ini.

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
```

Siapkan direktori aplikasi:

```bash
sudo install -d -o deploy -g deploy /var/www/cbt_pro
```

Login sebagai user deploy, lalu clone repo:

```bash
sudo -iu deploy
git clone <URL_REPO_ANDA> /var/www/cbt_pro
cd /var/www/cbt_pro
```

## 3. Python virtualenv dan dependency aplikasi

```bash
cd /var/www/cbt_pro
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
pip install gunicorn
```

`gunicorn` tidak ada di `requirements.txt`, jadi install terpisah untuk deployment Linux.

## 4. Build asset frontend

Karena `static/css/main.css` tidak ikut tersimpan di Git, build CSS harus dijalankan minimal sekali di server:

```bash
cd /var/www/cbt_pro
npm ci
npm run build:css
```

Jika build gagal, pastikan `nodejs` dan `npm` sudah terpasang serta file `package-lock.json` ikut ter-clone.

## 5. Database MySQL

Amankan instalasi MySQL jika perlu:

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

Jika ingin memakai `localhost` atau host lain, sesuaikan `CREATE USER` dan `.env`.

## 6. Redis

Aktifkan Redis:

```bash
sudo systemctl enable redis-server --now
redis-cli ping
```

Jika output-nya `PONG`, Redis sudah aktif.

## 7. Siapkan direktori writable

```bash
cd /var/www/cbt_pro
mkdir -p logs media staticfiles
chmod 755 logs media staticfiles
```

Jika nanti user service berbeda dari user deploy, pastikan owner direktori tersebut ikut disesuaikan.

## 8. Buat file `.env` production

Salin dari template:

```bash
cd /var/www/cbt_pro
cp .env.example .env
```

Lalu edit `.env` menjadi seperti contoh berikut:

```dotenv
CBT_SITE_NAME="CBT Sekolah"
SECRET_KEY=isi-dengan-secret-key-random-yang-panjang
DEBUG=False
ALLOWED_HOSTS=cbt.example.com,www.cbt.example.com
CSRF_TRUSTED_ORIGINS=https://cbt.example.com,https://www.cbt.example.com
TIME_ZONE=Asia/Jakarta
LANGUAGE_CODE=id
USE_TZ=True

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
EMAIL_HOST_PASSWORD=app-password-atau-smtp-password
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

Catatan penting:

- Generate `SECRET_KEY` dengan:

```bash
cd /var/www/cbt_pro
source .venv/bin/activate
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

- Jika SSL belum dipasang, set sementara `SECURE_SSL_REDIRECT=False`, lalu aktifkan kembali setelah Certbot/Nginx HTTPS selesai.
- Jika SMTP belum siap, Anda bisa memakai `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` sementara. Email akan masuk ke log aplikasi, bukan terkirim ke user.

## 9. Migrasi, static files, dan user admin

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

Jangan jalankan `seed` di production tanpa review, karena command ini membuat akun dan data contoh. Jika terpakai, ganti seluruh password default segera.

## 10. Service systemd untuk Gunicorn

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

## 11. Service systemd untuk Celery worker

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

Aktifkan kedua service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cbt_pro-gunicorn --now
sudo systemctl enable cbt_pro-celery --now
sudo systemctl status cbt_pro-gunicorn
sudo systemctl status cbt_pro-celery
```

Catatan operasional:

- `celery beat` belum perlu dijalankan untuk codebase saat ini.
- Jika Redis mati, beberapa task masih fallback ke mode sinkron, tetapi worker tetap disarankan agar import user + email tidak membebani request web.

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
sudo ln -s /etc/nginx/sites-available/cbt_pro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 13. HTTPS dengan Let's Encrypt

Install Certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d cbt.example.com -d www.cbt.example.com
```

Setelah HTTPS aktif:

- pastikan `.env` berisi `CSRF_TRUSTED_ORIGINS=https://cbt.example.com,https://www.cbt.example.com`
- pastikan `SECURE_SSL_REDIRECT=True`
- restart service:

```bash
sudo systemctl restart cbt_pro-gunicorn cbt_pro-celery nginx
```

## 14. Verifikasi pasca deploy

Jalankan pemeriksaan berikut:

```bash
curl -I -H "Host: cbt.example.com" http://127.0.0.1:8000
curl -I https://cbt.example.com
sudo systemctl status nginx cbt_pro-gunicorn cbt_pro-celery redis-server
```

Cek log jika ada masalah:

```bash
sudo journalctl -u cbt_pro-gunicorn -f
sudo journalctl -u cbt_pro-celery -f
tail -f /var/www/cbt_pro/logs/django.log
```

Hal yang perlu berhasil:

- halaman login bisa dibuka
- `admin/` bisa diakses
- file CSS termuat
- upload/import file berjalan
- screenshot proctoring bisa menulis ke `media/` jika fitur diaktifkan
- email test bisa dikirim bila SMTP diisi

## 15. Update deploy berikutnya

Setiap ada update kode:

```bash
sudo -iu deploy
cd /var/www/cbt_pro
git pull
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
npm ci
npm run build:css
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
exit
sudo systemctl restart cbt_pro-gunicorn cbt_pro-celery
```

## 16. Troubleshooting singkat

- `DisallowedHost`: isi `ALLOWED_HOSTS` belum benar.
- `CSRF verification failed`: cek `CSRF_TRUSTED_ORIGINS`, domain HTTPS, dan header `X-Forwarded-Proto` di Nginx.
- Redirect loop HTTP/HTTPS: biasanya `SECURE_SSL_REDIRECT=True` tetapi SSL belum aktif atau header proxy belum benar.
- `mysqlclient` gagal install: paket `python3-dev`, `pkg-config`, dan `default-libmysqlclient-dev` belum lengkap.
- CSS tidak muncul: jalankan `npm ci`, `npm run build:css`, lalu `python manage.py collectstatic --noinput`.
- Import user terasa lambat: pastikan Redis dan service `cbt_pro-celery` aktif.
- Media/proctoring gagal disimpan: cek permission `media/` dan user systemd yang menjalankan aplikasi.
