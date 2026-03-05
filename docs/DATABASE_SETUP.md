# Database Configuration Guide

## MySQL Database Setup

### 1. Install Dependencies

```bash
pip install django python-dotenv mysqlclient
```

**Note:** If you encounter issues with `mysqlclient` on Windows, install Visual C++ Build Tools first, or use:
```bash
pip install pymysql
pip install django pymysql
```

Then add this to your `config/settings.py` (at the top):
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and update the database configuration:

```bash
cp .env.example .env
```

Edit `.env` file with your MySQL credentials:

```env
DB_ENGINE=django.db.backends.mysql
DB_NAME=cbt_database
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_OPTIONS={'charset': 'utf8mb4'}
```

### 3. Create MySQL Database

#### Option A: Using Setup Script (Recommended)

**On Windows:**

```bash
python scripts/setup_mysql.py
```

**On Linux/Mac:**

```bash
bash scripts/setup_mysql.sh
```

#### Option B: Manual Creation

Open MySQL command line or phpMyAdmin and run:

```sql
CREATE DATABASE cbt_database
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

CREATE USER 'cbt_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON cbt_database.* TO 'cbt_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Seed Initial Data

```bash
python manage.py seed
```

This will create:

- Admin user: `admin` / `admin123` (change in production!)
- Sample subjects (Mathematics, Physics, Chemistry, etc.)
- Default system settings

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

## PostgreSQL Configuration (Alternative)

To use PostgreSQL instead of MySQL, update your `.env`:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=cbt_database
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

Install PostgreSQL driver:

```bash
pip install psycopg
```

## Database Schema

The system includes the following main tables:

### User Management

- `users` - User accounts with roles (admin, teacher, student)
- `user_profiles` - Extended user information
- `user_activity_logs` - User activity tracking

### Question Bank

- `subjects` - Subject/course information
- `question_categories` - Question categorization
- `questions` - Question bank with multiple types
- `question_options` - Multiple choice options
- `question_answers` - Essay/short answer correct answers

### Exam Management

- `exams` - Exam configurations
- `exam_questions` - Question assignment to exams
- `classes` - Student class groups
- `exam_assignments` - Exam assignments to classes/students

### Exam Execution

- `exam_attempts` - Student exam attempts
- `student_answers` - Student responses
- `essay_gradings` - Manual essay grading
- `exam_violations` - Anti-cheat violations
- `proctoring_screenshots` - Screenshot proctoring

### Results & Analytics

- `exam_results` - Exam results summary
- `question_statistics` - Question performance metrics
- `exam_statistics` - Aggregated exam statistics
- `certificates` - Exam certificates

### System

- `notifications` - User notifications
- `system_settings` - Application settings
- `system_logs` - System event logs

## Troubleshooting

### Error: "mysqlclient" not found

**Windows:**

1. Download MySQL Connector/C from MySQL website
2. Or use: `pip install mysqlclient` with Visual C++ Build Tools installed

**Linux:**

```bash
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

**Mac:**

```bash
brew install mysql
pip install mysqlclient
```

### Error: "Access denied for user"

1. Check your MySQL root password in `.env`
2. Ensure MySQL service is running
3. Try creating the database manually

### Error: "Unknown database"

Run the setup script or create the database manually before running migrations.

### Error: "Character set issues"

Make sure your database uses `utf8mb4` character set for full Unicode support (including emojis).

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| DB_ENGINE | Database backend | django.db.backends.mysql |
| DB_NAME | Database name | cbt_database |
| DB_USER | Database user | root |
| DB_PASSWORD | Database password | - |
| DB_HOST | Database host | localhost |
| DB_PORT | Database port | 3306 |
| DB_OPTIONS | Database options | {'charset': 'utf8mb4'} |
| SECRET_KEY | Django secret key | - |
| DEBUG | Debug mode | True |
| ALLOWED_HOSTS | Allowed hosts | localhost,127.0.0.1 |
| TIME_ZONE | Timezone | Asia/Jakarta |
