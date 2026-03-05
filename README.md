# Advanced CBT (Computer-Based Testing) System

A comprehensive Django-based Computer-Based Testing system with advanced features including real-time monitoring, anti-cheat mechanisms, and detailed analytics.

## Features

### User Management
- Multi-role system (Admin, Teacher, Student)
- User profiles with role-specific information
- Activity logging

### Question Bank
- Multiple question types (Multiple Choice, Essay, Short Answer)
- Question categorization and tagging
- Difficulty levels
- Import/Export functionality

### Exam Management
- Flexible exam scheduling
- Question randomization
- Custom navigation settings per exam/question
- Class-based or individual student assignments

### Exam Execution
- Real-time exam monitoring
- Anti-cheat detection (tab switch, fullscreen exit, etc.)
- Screenshot proctoring
- Auto-save and auto-submit
- WebSocket-based real-time updates

### Results & Analytics
- Comprehensive result analysis
- Question performance statistics
- Item analysis (difficulty, discrimination index)
- Certificate generation

## Quick Start

### Prerequisites

- Python 3.11+
- MySQL 8.0+ or PostgreSQL 13+
- Redis (for Celery and WebSockets)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cbt_project
   ```

2. **Install dependencies**
   ```bash
   pip install django python-dotenv

   # Database driver (MySQL)
   pip install mysqlclient
   # OR use pymysql if mysqlclient fails on Windows:
   # pip install pymysql

   # For PostgreSQL instead of MySQL:
   # pip install psycopg

   # Django packages
   pip install djangorestframework django-cors-headers django-environ django-extensions
   pip install django-crispy-forms crispy-bootstrap5 django-allauth django-import-export
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Setup database**
   
   **Option A: Using setup script**
   ```bash
   # Windows
   python scripts/setup_mysql.py
   
   # Linux/Mac
   bash scripts/setup_mysql.sh
   ```
   
   **Option B: Manual setup**
   See [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) for detailed instructions.

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Seed initial data**
   ```bash
   python manage.py seed
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open browser: http://127.0.0.1:8000
   - Admin: http://127.0.0.1:8000/admin
   - Default admin: `admin` / `admin123`

## Project Structure

```
cbt_project/
├── apps/                      # Django applications
│   ├── accounts/              # User management
│   ├── questions/             # Question bank
│   ├── exams/                 # Exam management
│   ├── attempts/              # Exam taking
│   ├── results/               # Results & analytics
│   ├── notifications/         # Notifications
│   └── ...
├── config/                    # Project configuration
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── static/                    # Static files
├── templates/                 # HTML templates
├── .env                       # Environment variables
└── manage.py                  # Django management script
```

## Documentation

- [Database Setup Guide](docs/DATABASE_SETUP.md)
- [API Documentation](docs/api/)
- [Architecture Documentation](docs/architecture/)

## Technology Stack

- **Backend:** Django 5.2, Django REST Framework
- **Database:** MySQL 8.0+ / PostgreSQL 13+ (agnostic)
- **Cache & Queue:** Redis, Celery
- **Real-time:** Django Channels, WebSockets
- **Frontend:** HTMX, Alpine.js, Tailwind CSS
- **Testing:** pytest

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Build Bootstrap Theme (SCSS)
```bash
npm install
npm run build:css
```

SCSS source files:
- `static/dashboard/scss/theme.scss` (khusus override Bootstrap 5)
- `static/dashboard/scss/custom.scss` (style aplikasi)

Untuk mode watch:
```bash
npm run watch:css
```

### Creating Migrations
```bash
python manage.py makemigrations
```

## License

This project is licensed under the MIT License.

## Support

For issues and feature requests, please use the GitHub issue tracker.
