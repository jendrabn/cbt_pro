#!/bin/bash

echo "=========================================="
echo "CBT System - MySQL Database Setup Script"
echo "=========================================="
echo ""

# Check if MySQL is installed
if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL is not installed. Please install MySQL first."
    exit 1
fi

echo "✅ MySQL is installed"
echo ""

# Get database credentials from .env
DB_NAME=$(grep DB_NAME .env | cut -d '=' -f2)
DB_USER=$(grep DB_USER .env | cut -d '=' -f2)
DB_PASSWORD=$(grep DB_PASSWORD .env | cut -d '=' -f2)
DB_HOST=$(grep DB_HOST .env | cut -d '=' -f2)

echo "Creating database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST"
echo ""

# Create database
echo "Creating database..."
mysql -u root -p -e "
CREATE DATABASE IF NOT EXISTS $DB_NAME 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Create user if not exists and grant privileges
CREATE USER IF NOT EXISTS '$DB_USER'@'$DB_HOST' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'$DB_HOST';
FLUSH PRIVILEGES;

SELECT 'Database and user created successfully!' AS Status;
"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Run migrations: python manage.py migrate"
    echo "2. Seed database: python manage.py seed"
    echo "3. Create superuser: python manage.py createsuperuser"
else
    echo ""
    echo "❌ Database setup failed!"
    echo "Please check your MySQL root password and try again."
fi
