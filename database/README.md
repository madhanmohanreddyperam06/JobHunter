# Database — Job Application Command Center

![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat-square&logo=mysql)

## Overview

This directory contains database schemas, DDL scripts, and migration files for the Job Application Command Center. The database is **MySQL 8.0+** and is managed through SQLAlchemy ORM in the backend application.

## Database Schema

### Database Name
`job_command_center`

### Character Set
- Character Set: `utf8mb4`
- Collation: `utf8mb4_unicode_ci`

### Tables

#### Core Tables
- **users** - User accounts and authentication
- **applications** - Job applications and status tracking
- **interviews** - Interview scheduling and details
- **tasks** - Tasks and reminders
- **resumes** - Resume versions and metadata
- **job_descriptions** - Job posting storage
- **skills** - Skills with proficiency levels
- **companies** - Company information
- **notes** - Notes and comments
- **activity_logs** - Activity tracking

#### Relationship Tables
- **application_skills** - Many-to-many: applications ↔ skills
- **job_description_skills** - Many-to-many: job_descriptions ↔ skills

## Database Management

### Automatic Schema Creation

The database schema is automatically created by SQLAlchemy when the backend starts:

```python
from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)
```

### Manual Database Setup

1. Connect to MySQL:
   ```bash
   mysql -u root -p
   ```

2. Create the database:
   ```sql
   CREATE DATABASE IF NOT EXISTS job_command_center
     CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
   ```

3. Grant privileges (if needed):
   ```sql
   GRANT ALL PRIVILEGES ON job_command_center.* TO 'your_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

## Migration Strategy

Currently using SQLAlchemy's automatic schema creation. For production deployment, consider implementing:

- **Alembic** for database migrations
- Version-controlled schema changes
- Rollback capabilities
- Data migration scripts

## Database Relationships

### User Relationships
- One-to-Many: User → Applications
- One-to-Many: User → Interviews
- One-to-Many: User → Tasks
- One-to-Many: User → Resumes
- One-to-Many: User → Job Descriptions

### Application Relationships
- Many-to-One: Application → User
- Many-to-One: Application → Company
- Many-to-Many: Application ↔ Skills
- One-to-Many: Application → Activity Logs

### Job Description Relationships
- Many-to-One: Job Description → User
- Many-to-Many: Job Description ↔ Skills

## Backup and Restore

### Backup
```bash
mysqldump -u root -p job_command_center > backup.sql
```

### Restore
```bash
mysql -u root -p job_command_center < backup.sql
```

## Current Status

✅ **DATABASE SCHEMA COMPLETED**

All database models are implemented and working with the backend API. Tables are automatically created on application startup.
