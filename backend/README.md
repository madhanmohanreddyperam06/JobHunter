# Backend — Job Application Command Center

![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat-square&logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat-square&logo=mysql)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red?style=flat-square&logo=sqlalchemy)
![Pytest](https://img.shields.io/badge/Pytest-8.4+-white?style=flat-square&logo=pytest)

## Overview

The backend is a RESTful API built with **FastAPI** and **SQLAlchemy**, providing comprehensive endpoints for managing job applications, interviews, tasks, resumes, skills, and user authentication. It follows clean architecture principles with separation of concerns.

## Technology Stack

- **Runtime**: Python 3.14+
- **API Framework**: FastAPI 0.110+
- **ASGI Server**: Uvicorn 0.28+
- **ORM**: SQLAlchemy 2.0 (Declarative Mapping)
- **Database Driver**: PyMySQL 1.1+ (with Cryptography)
- **Database Engine**: MySQL 8.0+
- **Validation**: Pydantic v2 & Pydantic Settings
- **Authentication**: JWT (PyJWT) + Bcrypt
- **Testing**: Pytest 8.4+ & HTTPX
- **Environment**: python-dotenv

---

## Architecture

The backend implements clean separation of concerns:

```text
HTTP Request
     │
     ▼
┌──────────────────┐
│   API Router     │  (app/routers/ - validation, route handling, HTTP status)
└─────────┬────────┘
          │
          ▼
┌──────────────────┐
│  Service Layer   │  (app/services/ - business rules, workflows, orchestration)
└─────────┬────────┘
          │
          ▼
┌──────────────────┐
│  SQLAlchemy 2.0  │  (app/models/ & app/database/ - ORM entities & sessions)
└─────────┬────────┘
          │
          ▼
┌──────────────────┐
│     MySQL 8      │  (job_command_center database, InnoDB, utf8mb4)
└──────────────────┘
```

---

## Environment Setup

1. Open a terminal in the `backend` directory:
   ```bash
   cd backend
   ```

2. Create the Python virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     source venv/bin/activate
     ```

4. Install the pinned dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your MySQL credentials:

```bash
cp .env.example .env
```

Configuration keys:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `Job Application Command Center` | Display title for API documentation |
| `APP_ENV` | `development` | Runtime mode (`development`, `staging`, `production`) |
| `DEBUG` | `true` | Enables SQLAlchemy SQL echo and verbose logging |
| `DATABASE_HOST` | `localhost` | MySQL host address |
| `DATABASE_PORT` | `3306` | MySQL port |
| `DATABASE_NAME` | `job_command_center` | Target database name |
| `DATABASE_USER` | `root` | Database username |
| `DATABASE_PASSWORD` | `********` | Database password (do not commit to Git) |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed frontend origins |
| `JWT_SECRET_KEY` | `********` | Cryptographically random secret key for signing JWTs |
| `JWT_ALGORITHM` | `HS256` | Symmetric HMAC-SHA256 algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token expiration lifetime in minutes |

---

## Token Storage Security Tradeoffs

In the AngularJS frontend, access tokens are stored in the browser's `sessionStorage` under key `jcc_access_token`:
- **Advantages**: The token persists during tab usage and is automatically wiped once the browser tab or window closes. It is isolated from other tabs and avoids persistent token accumulation.
- **Security Considerations**: Like `localStorage`, data in `sessionStorage` can be accessed by scripts executed within the same origin context (vulnerable to XSS). In an enterprise production deployment, httpOnly, secure, SameSite cookies with CSRF tokens provide the strongest defense against script-based token extraction. For development and SPA decoupling, `sessionStorage` provides a standard, transparent bearer authentication workflow.

---

## Database Setup

1. Connect to MySQL CLI:
   ```bash
   mysql -u root -p
   ```

2. Create the database:
   ```sql
   CREATE DATABASE IF NOT EXISTS job_command_center
     CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
   ```

3. Tables are created automatically when starting the backend via SQLAlchemy metadata reflection (`Base.metadata.create_all(bind=engine)`).

---

## Running the Backend

Start the development server with automatic reload:

```bash
uvicorn app.main:app --reload --port 8000
```

- **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Documentation (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## API Endpoints

### 1. Health Endpoints
- `GET /api/health` — API service operational status
- `GET /api/health/database` — MySQL 8 database connectivity verification

### 2. Authentication Endpoints
- `POST /api/auth/register` — Create new candidate user with bcrypt password hashing
- `POST /api/auth/login` — Authenticate email & password, returns JWT bearer token
- `GET /api/auth/me` — Protected endpoint returning authenticated candidate profile
- `GET /api/auth/protected-test` — Diagnostic protected endpoint

### 3. Application Endpoints
- `GET /api/applications` — List all applications for authenticated user
- `POST /api/applications` — Create new job application
- `GET /api/applications/{id}` — Get specific application details
- `PUT /api/applications/{id}` — Update application
- `DELETE /api/applications/{id}` — Delete application
- `PATCH /api/applications/{id}/status` — Update application status

### 4. Interview Endpoints
- `GET /api/interviews` — List all interviews
- `POST /api/interviews` — Create new interview
- `GET /api/interviews/{id}` — Get specific interview
- `PUT /api/interviews/{id}` — Update interview
- `DELETE /api/interviews/{id}` — Delete interview

### 5. Task Endpoints
- `GET /api/tasks` — List all tasks
- `POST /api/tasks` — Create new task
- `GET /api/tasks/{id}` — Get specific task
- `PUT /api/tasks/{id}` — Update task
- `DELETE /api/tasks/{id}` — Delete task
- `PATCH /api/tasks/{id}/complete` — Mark task as complete

### 6. Resume Endpoints
- `GET /api/resumes` — List all resumes
- `POST /api/resumes` — Create new resume
- `GET /api/resumes/{id}` — Get specific resume
- `PUT /api/resumes/{id}` — Update resume
- `DELETE /api/resumes/{id}` — Delete resume

### 7. Job Description Endpoints
- `GET /api/job-descriptions` — List all job descriptions
- `POST /api/job-descriptions` — Create new job description
- `GET /api/job-descriptions/{id}` — Get specific job description
- `PUT /api/job-descriptions/{id}` — Update job description
- `DELETE /api/job-descriptions/{id}` — Delete job description

### 8. Skills Endpoints
- `GET /api/skills` — List all skills
- `POST /api/skills` — Create new skill
- `GET /api/skills/{id}` — Get specific skill
- `PUT /api/skills/{id}` — Update skill
- `DELETE /api/skills/{id}` — Delete skill
- `POST /api/skills/batch` — Batch create skills

### 9. Analytics Endpoints
- `GET /api/analytics` — Get application analytics and metrics

---

## Running Tests

Execute the automated test suite with pytest:

```bash
pytest -v
```

---

## Current Status

✅ **FULLY FUNCTIONAL - ALL PHASES COMPLETED**

The backend API is fully implemented with all planned features:

- ✅ Authentication & JWT Security
- ✅ Application Management (Full CRUD)
- ✅ Interview Management
- ✅ Task Management
- ✅ Resume Management
- ✅ Job Description Management
- ✅ Skills Management
- ✅ Analytics & Reporting
- ✅ Comprehensive Test Coverage

## Database Models

### Core Models
- **User**: User accounts with authentication
- **Application**: Job applications with status tracking
- **Interview**: Interview scheduling and details
- **Task**: Tasks and reminders
- **Resume**: Resume versions and metadata
- **JobDescription**: Job posting storage
- **Skill**: Skills with proficiency levels
- **Company**: Company information
- **Note**: Notes and comments
- **ActivityLog**: Activity tracking

### Relationship Models
- **ApplicationSkill**: Many-to-many relationship between applications and skills
- **JobDescriptionSkill**: Many-to-many relationship between job descriptions and skills

## Testing

The backend includes comprehensive test coverage for all endpoints:

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=app tests/
```

### Test Files
- `test_auth.py` - Authentication endpoints
- `test_applications.py` - Application CRUD operations
- `test_interviews.py` - Interview management
- `test_tasks.py` - Task management
- `test_resumes.py` - Resume management
- `test_job_descriptions.py` - Job description operations
- `test_skills.py` - Skills management
- `test_health.py` - Health check endpoints
