"""
MySQL Database Setup Script for CBT System
Run this script to create the MySQL database and user
"""

import os
import sys
import subprocess
from pathlib import Path


def load_env():
    """Load environment variables from .env file"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found. Please create one from .env.example")
        sys.exit(1)
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars


def create_database_mysql(env_vars):
    """Create MySQL database"""
    db_name = env_vars.get('DB_NAME', 'cbt_database')
    db_user = env_vars.get('DB_USER', 'root')
    db_password = env_vars.get('DB_PASSWORD', '')
    db_host = env_vars.get('DB_HOST', 'localhost')
    
    print(f"📊 Creating database: {db_name}")
    print(f"👤 User: {db_user}")
    print(f"🖥️  Host: {db_host}")
    print()
    
    # SQL commands to create database and user
    sql_commands = f"""
CREATE DATABASE IF NOT EXISTS {db_name}
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '{db_user}'@'{db_host}' IDENTIFIED BY '{db_password}';
GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'{db_host}';
FLUSH PRIVILEGES;

SELECT 'Database and user created successfully!' AS Status;
"""
    
    # Try to execute SQL commands
    try:
        if sys.platform == 'win32':
            # Windows
            result = subprocess.run(
                ['mysql', '-u', 'root', '-p', '-e', sql_commands],
                capture_output=True,
                text=True,
                shell=True
            )
        else:
            # Linux/Mac
            result = subprocess.run(
                ['mysql', '-u', 'root', '-p', '-e', sql_commands],
                capture_output=True,
                text=True
            )
        
        if result.returncode == 0:
            print("✅ Database setup completed successfully!")
            print()
            print("Next steps:")
            print("1. Install requirements: pip install -r requirements.txt")
            print("2. Run migrations: python manage.py migrate")
            print("3. Seed database: python manage.py seed")
            print("4. Create superuser: python manage.py createsuperuser")
            print("5. Run server: python manage.py runserver")
            return True
        else:
            print("❌ Error creating database:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ MySQL command not found. Please make sure MySQL is installed and in PATH.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    print("=" * 50)
    print("CBT System - MySQL Database Setup Script")
    print("=" * 50)
    print()
    
    # Load environment variables
    env_vars = load_env()
    
    # Check if using MySQL
    db_engine = env_vars.get('DB_ENGINE', '')
    if 'mysql' not in db_engine.lower():
        print(f"⚠️  Database engine is set to: {db_engine}")
        print("This script is designed for MySQL. Please check your .env file.")
        sys.exit(1)
    
    # Create database
    success = create_database_mysql(env_vars)
    
    if not success:
        print()
        print("Alternative: You can manually create the database using phpMyAdmin")
        print("or MySQL Workbench with the following settings:")
        print(f"  - Database Name: {env_vars.get('DB_NAME', 'cbt_database')}")
        print(f"  - Character Set: utf8mb4")
        print(f"  - Collation: utf8mb4_unicode_ci")


if __name__ == '__main__':
    main()
