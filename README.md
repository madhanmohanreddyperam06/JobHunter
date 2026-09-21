# Job Application Command Center

![AngularJS](https://img.shields.io/badge/AngularJS-1.8.x-orange?style=flat-square&logo=angularjs)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.x-7952B3?style=flat-square&logo=bootstrap)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat-square&logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat-square&logo=mysql)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## Overview

A personal job-search operating system built with **AngularJS (1.8.x)** frontend and **FastAPI** backend. The system enables users to track job applications, interviews, technical assessments, offers, tasks, resume versions, job descriptions, skills, reminders, and comprehensive application analytics through an intuitive SaaS-grade dashboard.

## Current Status

**✅ PROJECT COMPLETED - FULLY FUNCTIONAL**

All planned features have been implemented and are fully operational:

- ✅ Phase 1: Frontend Architecture & Layout (AngularJS)
- ✅ Phase 2: Backend API & Database Schema (FastAPI + MySQL)
- ✅ Phase 3: Authentication & JWT Security
- ✅ Phase 4: Application Management (Full CRUD + Kanban)
- ✅ Phase 5: Interview & Task Management
- ✅ Phase 6: Resume Management & Analysis
- ✅ Phase 7: Analytics Dashboard & Visualizations
- ✅ Phase 8: Skills Management & Job Description Analysis

## Technology Stack

### Frontend
- **Framework**: AngularJS 1.8.x (`ngRoute`)
- **Language**: JavaScript (ES6+)
- **Styling**: Bootstrap 5.3.x & Custom Modern Slate/Navy CSS3
- **Icons**: Bootstrap Icons
- **Drag & Drop**: SortableJS
- **Markup**: Semantic HTML5

### Backend
- **Runtime**: Python 3.14+
- **API Framework**: FastAPI 0.110+
- **ASGI Server**: Uvicorn
- **ORM**: SQLAlchemy 2.0
- **Database**: MySQL 8.0+
- **Authentication**: JWT (JSON Web Tokens) + Bcrypt
- **Validation**: Pydantic v2
- **Testing**: Pytest + HTTPX

*(Note: Modern Angular 2+, React, Vue, and TypeScript are explicitly excluded by design.)*

## Implemented Features

### Core Functionality
- **Application Tracking**: Centralized repository of all applied, interviewing, and offered positions with full CRUD operations
- **Kanban Pipeline**: Drag-and-drop pipeline stages (Saved, Applied, Assessment, Interview, Offer, Rejected) using SortableJS
- **Interview Management**: Preparation notes, question bank, schedule alerts, and outcome tracking
- **Tasks & Reminders**: Follow-ups, technical challenge deadlines, and recruiter check-ins with priority management
- **Resume Version Tracking**: Version control, target keywords, and role-specific CV attachments
- **Job Description Analysis**: Store and analyze job descriptions with skill extraction
- **Skills Management**: Comprehensive skill tracking with proficiency levels and categories
- **Analytics & Reporting**: Conversion funnels, response times, offer probabilities, and application metrics

### Authentication & Security
- **User Registration & Login**: Secure authentication with email/password
- **JWT Token Management**: Secure token-based authentication with configurable expiration
- **Protected Routes**: API endpoint protection with JWT validation
- **Password Security**: Bcrypt hashing for secure password storage

### User Interface
- **Responsive Dashboard**: Modern SaaS-grade interface with Bootstrap 5
- **Interactive Components**: Reusable directives and components for consistent UI
- **Real-time Updates**: Dynamic data binding with AngularJS
- **Mobile-Friendly**: Responsive design for tablets and mobile devices

## Project Structure

```text
job-application-command-center/
├── frontend/                     # AngularJS 1.8.x client application
│   ├── index.html                # Main application entrypoint
│   ├── package.json              # Frontend package configuration
│   ├── app/                      # Application source code
│   │   ├── app.js                # Core AngularJS module declaration
│   │   ├── routes.js             # Route definitions with ngRoute
│   │   ├── controllers/          # State & presentation controllers
│   │   │   ├── dashboard.controller.js
│   │   │   ├── applications.controller.js
│   │   │   ├── kanban.controller.js
│   │   │   ├── interviews.controller.js
│   │   │   ├── tasks.controller.js
│   │   │   ├── resumes.controller.js
│   │   │   ├── job-descriptions.controller.js
│   │   │   ├── skills.controller.js
│   │   │   ├── analytics.controller.js
│   │   │   ├── login.controller.js
│   │   │   ├── register.controller.js
│   │   │   └── settings.controller.js
│   │   ├── services/             # Promise-based data & business logic services
│   │   │   ├── application.service.js
│   │   │   ├── interview.service.js
│   │   │   ├── task.service.js
│   │   │   ├── resume.service.js
│   │   │   ├── job-description.service.js
│   │   │   ├── skill.service.js
│   │   │   ├── analytics.service.js
│   │   │   ├── auth.service.js
│   │   │   └── auth-interceptor.service.js
│   │   ├── directives/           # Reusable UI directives
│   │   │   ├── job-card.directive.js
│   │   │   ├── status-badge.directive.js
│   │   │   ├── priority-badge.directive.js
│   │   │   └── kanban-sortable.directive.js
│   │   ├── filters/              # Formatting filters
│   │   │   └── status.filter.js
│   │   ├── views/                # Route partial templates
│   │   │   ├── dashboard.html
│   │   │   ├── applications.html
│   │   │   ├── kanban.html
│   │   │   ├── interviews.html
│   │   │   ├── tasks.html
│   │   │   ├── resumes.html
│   │   │   ├── job-descriptions.html
│   │   │   ├── skills.html
│   │   │   ├── analytics.html
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   └── settings.html
│   │   └── components/           # Modular UI components
│   │       ├── navbar/           # Top navigation bar
│   │       ├── sidebar/          # Collapsible navigation sidebar
│   │       └── stat-card/        # Dashboard metric KPI card
│   ├── assets/                   # Images and static assets
│   │   ├── images/
│   │   └── icons/
│   └── styles/                   # Modular stylesheet system
│       ├── main.css              # Variables, base resets, typography
│       ├── layout.css            # Shell, grid, flex, sidebar & navbar positioning
│       ├── components.css        # Card, badge, table, and form component styling
│       └── responsive.css        # Media queries for tablet & mobile views
├── backend/                      # FastAPI backend application
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment variables template
│   ├── app/                      # Application source code
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── core/                 # Core configuration and security
│   │   ├── database/             # Database session management
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── application.py
│   │   │   ├── interview.py
│   │   │   ├── task.py
│   │   │   ├── resume.py
│   │   │   ├── job_description.py
│   │   │   ├── skill.py
│   │   │   └── ...
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── routers/              # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── applications.py
│   │   │   ├── interviews.py
│   │   │   ├── tasks.py
│   │   │   ├── resumes.py
│   │   │   ├── job_descriptions.py
│   │   │   ├── skills.py
│   │   │   └── analytics.py
│   │   ├── services/             # Business logic layer
│   │   └── utils/                # Utility functions
│   ├── tests/                    # Automated test suite
│   │   ├── test_auth.py
│   │   ├── test_applications.py
│   │   ├── test_interviews.py
│   │   ├── test_tasks.py
│   │   ├── test_resumes.py
│   │   ├── test_job_descriptions.py
│   │   └── test_skills.py
│   └── storage/                  # File storage for uploads
├── database/                     # Database schemas and migrations
├── docs/                         # Architecture documentation & design guides
└── scratch/                      # Development scratchpad
```

## Development Roadmap

✅ **Phase 1 — Project Foundation & AngularJS Architecture** - **COMPLETED**
✅ **Phase 2 — Backend API & Database Schema (FastAPI + MySQL)** - **COMPLETED**
✅ **Phase 3 — Authentication & JWT Security** - **COMPLETED**
✅ **Phase 4 — Applications & Pipeline Management (Full CRUD + Kanban)** - **COMPLETED**
✅ **Phase 5 — Interview & Task Management** - **COMPLETED**
✅ **Phase 6 — Resume Management & Analysis** - **COMPLETED**
✅ **Phase 7 — Analytics Dashboard & Visualizations** - **COMPLETED**
✅ **Phase 8 — Skills Management & Job Description Analysis** - **COMPLETED**

**🎉 ALL PHASES COMPLETED - PROJECT IS FULLY FUNCTIONAL**

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (v16+) and `npm` for frontend
- [Python](https://www.python.org/) (3.14+) for backend
- [MySQL](https://www.mysql.com/) (8.0+) for database

### Backend Setup

1. Open a terminal in the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate Python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\Activate.ps1
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your MySQL credentials
   ```

5. Create MySQL database:
   ```sql
   CREATE DATABASE job_command_center
     CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
   ```

6. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend Setup

1. Open a terminal in the `frontend` directory:
   ```bash
   cd frontend
   npm install
   ```

2. Start the frontend development server:
   ```bash
   npm start
   ```

3. Open your browser and navigate to:
   ```text
   http://localhost:3000
   ```

### Running Tests

Backend tests:
```bash
cd backend
pytest -v
```
