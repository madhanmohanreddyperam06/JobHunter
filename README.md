# Job Application Command Center

![AngularJS](https://img.shields.io/badge/AngularJS-1.8.x-orange?style=flat-square&logo=angularjs)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.x-7952B3?style=flat-square&logo=bootstrap)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=flat-square&logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat-square&logo=mysql)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## Overview

A personal job-search operating system built with **AngularJS (1.8.x)** frontend and **FastAPI** backend. The system enables users to track job applications, interviews, technical assessments, offers, tasks, resume versions, job descriptions, skills, reminders, and comprehensive application analytics through an intuitive SaaS-grade dashboard.

This project represents a complete full-stack application demonstrating modern web development practices while intentionally using legacy technologies (AngularJS 1.8.x) for the frontend to maintain compatibility with specific requirements.

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

**Last Updated:** September 23, 2026

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
- **Kanban Pipeline**: Drag-and-drop pipeline stages (Saved, Applied, Assessment, Interview, Offer, Rejected, Withdrawn) using SortableJS
- **Interview Management**: Preparation notes, question bank, schedule alerts, and outcome tracking
- **Tasks & Reminders**: Follow-ups, technical challenge deadlines, and recruiter check-ins with priority management
- **Resume Version Tracking**: Version control, target keywords, and role-specific CV attachments
- **Job Description Analysis**: Store and analyze job descriptions with skill extraction
- **Skills Management**: Comprehensive skill tracking with proficiency levels and categories
- **Analytics & Reporting**: Conversion funnels, response times, offer probabilities, and application metrics
- **Company Management**: Track company information and application history per company
- **Activity Logging**: Track user activities and system events (partially implemented)

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

## Known Limitations

- **Frontend Testing**: No automated testing framework is currently set up for the AngularJS frontend
- **Resume Analytics**: The resume match statistics endpoint (`/api/analytics/resumes`) is not yet implemented in the backend
- **Activity Logs**: Activity logging infrastructure exists but is not fully integrated with user actions
- **Note System**: Note management for applications and interviews is planned but not yet implemented
- **Email Notifications**: No email notification system for reminders or alerts
- **File Upload**: Basic file upload functionality exists but lacks advanced validation and security features
- **Search**: Limited search capabilities across applications and job descriptions
- **Mobile Optimization**: While responsive, the UI is primarily optimized for desktop use

## Deployment Status

**Development Environment**: ✅ Fully functional
- Backend runs on `http://localhost:8000` with auto-reload
- Frontend runs on `http://localhost:3000` with hot-reload
- Full CORS configuration for cross-origin requests
- Interactive API documentation via Swagger UI

**Production Environment**: ❌ Not configured
- No Docker containerization
- No CI/CD pipeline
- No production database configuration
- No SSL/HTTPS configuration
- No monitoring or logging setup
- No backup strategy

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
│   ├── .env                      # Actual environment configuration (not in git)
│   ├── app/                      # Application source code
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── core/                 # Core configuration and security
│   │   │   ├── config.py         # Application settings and configuration
│   │   │   └── security.py      # JWT and password hashing utilities
│   │   ├── database/             # Database session management
│   │   │   ├── database.py       # Database connection and session factory
│   │   │   └── base.py           # Base ORM model class
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── user.py           # User authentication model
│   │   │   ├── application.py    # Job application model
│   │   │   ├── company.py        # Company information model
│   │   │   ├── interview.py      # Interview scheduling model
│   │   │   ├── task.py           # Task and reminder model
│   │   │   ├── resume.py         # Resume version model
│   │   │   ├── job_description.py # Job description storage model
│   │   │   ├── skill.py          # Skills catalog model
│   │   │   ├── application_skill.py # Many-to-many application-skill relationship
│   │   │   ├── job_description_skill.py # Many-to-many JD-skill relationship
│   │   │   ├── activity_log.py   # User activity tracking model
│   │   │   └── note.py           # Notes and annotations model
│   │   ├── schemas/              # Pydantic validation schemas
│   │   │   ├── user.py           # User input/output schemas
│   │   │   ├── application.py    # Application validation schemas
│   │   │   ├── company.py        # Company validation schemas
│   │   │   ├── interview.py      # Interview validation schemas
│   │   │   ├── task.py           # Task validation schemas
│   │   │   ├── resume.py         # Resume validation schemas
│   │   │   ├── job_description.py # JD validation schemas
│   │   │   ├── skill.py          # Skill validation schemas
│   │   │   └── common.py         # Shared schema utilities
│   │   ├── routers/              # API route handlers
│   │   │   ├── auth.py           # Authentication endpoints (register, login, me)
│   │   │   ├── applications.py  # Application CRUD operations
│   │   │   ├── interviews.py     # Interview management endpoints
│   │   │   ├── tasks.py          # Task management endpoints
│   │   │   ├── resumes.py        # Resume upload and management
│   │   │   ├── job_descriptions.py # JD storage and analysis
│   │   │   ├── skills.py         # Skills catalog and management
│   │   │   ├── analytics.py      # Analytics and reporting endpoints
│   │   │   └── health.py         # System health check endpoint
│   │   ├── services/             # Business logic layer
│   │   │   ├── application_service.py # Application business logic
│   │   │   ├── interview_service.py   # Interview scheduling logic
│   │   │   ├── task_service.py        # Task priority and management
│   │   │   ├── resume_service.py      # Resume file handling and analysis
│   │   │   ├── job_description_service.py # JD parsing and analysis
│   │   │   └── skill_service.py       # Skill matching and recommendations
│   │   └── utils/                # Utility functions
│   ├── tests/                    # Automated test suite
│   │   ├── test_auth.py          # Authentication endpoint tests
│   │   ├── test_applications.py  # Application CRUD tests
│   │   ├── test_interviews.py    # Interview management tests
│   │   ├── test_tasks.py         # Task management tests
│   │   ├── test_resumes.py       # Resume handling tests
│   │   ├── test_job_descriptions.py # JD analysis tests
│   │   ├── test_skills.py        # Skills management tests
│   │   └── test_health.py        # Health check tests
│   ├── storage/                  # File storage for uploads
│   │   └── .gitkeep              # Placeholder for storage directory
│   └── venv/                     # Python virtual environment (not in git)
├── database/                     # Database schemas and migrations
│   └── README.md                 # Database documentation
├── docs/                         # Architecture documentation & design guides
│   └── README.md                 # Documentation index and structure
├── scratch/                      # Development scratchpad
│   └── README.md                 # Scratchpad notes and experiments
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
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

## Current Implementation Details

### Backend Architecture (FastAPI)
- **FastAPI Application**: Main application with auto-generated OpenAPI documentation
- **CORS Configuration**: Full CORS support for frontend-backend communication
- **Database Models**: 13 SQLAlchemy models covering all entities
  - User, Application, Company, Interview, Task, Resume
  - JobDescription, Skill, ApplicationSkill, JobDescriptionSkill
  - ActivityLog, Note
- **API Routers**: 9 modular routers with comprehensive endpoints
  - Authentication (register, login, user profile)
  - Applications (CRUD operations, status management)
  - Interviews (scheduling, preparation, outcomes)
  - Tasks (priority management, due dates)
  - Resumes (version tracking, file uploads)
  - Job Descriptions (storage, skill extraction)
  - Skills (catalog management, proficiency levels)
  - Analytics (dashboard metrics, funnel analysis, skills analytics)
  - Health (system health checks)
- **Business Logic Layer**: Service layer for complex operations
  - Application service (pipeline management)
  - Interview service (scheduling logic)
  - Resume service (file handling, keyword analysis)
  - Skill service (matching and recommendation)
  - Job description service (parsing and analysis)
  - Task service (priority sorting, notifications)
- **Security**: JWT-based authentication with bcrypt password hashing
- **Testing**: Comprehensive test suite with pytest covering all major endpoints

### Frontend Architecture (AngularJS)
- **AngularJS Module**: `jobCommandCenter` with dependency injection
- **Routing**: ngRoute-based SPA with 12 routes
  - Dashboard, Applications, Kanban, Interviews, Tasks
  - Resumes, Job Descriptions, Skills, Analytics
  - Login, Register, Settings
- **Controllers**: 12 controllers managing application state
- **Services**: 9 promise-based services for API communication
  - All services include fallback mock data for development
  - Auth interceptor for automatic token injection
- **Directives**: 4 reusable UI directives
  - Job Card (application display)
  - Status Badge (visual status indicators)
  - Priority Badge (task priority visualization)
  - Kanban Sortable (drag-and-drop pipeline)
- **Components**: Modular component structure
  - Navbar (top navigation)
  - Sidebar (collapsible navigation)
  - Stat Card (dashboard metrics)
- **Styling**: Custom CSS3 architecture with Bootstrap 5.3
  - Modern slate/navy color scheme
  - Responsive design for mobile/tablet/desktop
  - Modular CSS files (main, layout, components, responsive)

### Database Schema
- **MySQL 8.0+** database with utf8mb4 character set
- **Relational design** with proper foreign key constraints
- **Many-to-many relationships** for skills and applications
- **Audit fields** (created_at, updated_at) on all entities
- **User isolation** - all data scoped to authenticated users

### API Endpoints
All endpoints are prefixed with `/api` and require JWT authentication except:
- POST `/api/auth/register` - User registration
- POST `/api/auth/login` - User authentication
- GET `/api/health` - Health check

Protected endpoints include:
- Applications: `/api/applications` (CRUD + status updates)
- Interviews: `/api/interviews` (CRUD + scheduling)
- Tasks: `/api/tasks` (CRUD + priority management)
- Resumes: `/api/resumes` (CRUD + file upload)
- Job Descriptions: `/api/job-descriptions` (CRUD + skill linking)
- Skills: `/api/skills` (CRUD + proficiency management)
- Analytics: `/api/analytics/*` (dashboard, funnel, skills metrics)

### API Documentation
The backend provides interactive API documentation via:
- **Swagger UI**: Available at `http://localhost:8000/docs` when backend is running
- **ReDoc**: Available at `http://localhost:8000/redoc` when backend is running
- **OpenAPI Schema**: Available at `http://localhost:8000/openapi.json` when backend is running

### Authentication Flow
1. User registers via `/api/auth/register` with email and password
2. Password is hashed using bcrypt before storage
3. User logs in via `/api/auth/login` with credentials
4. Server generates JWT access token (expires in 60 minutes by default)
5. Token is stored in frontend and sent in Authorization header
6. Protected routes validate token and extract user identity
7. Token expiration triggers re-authentication requirement

## Future Tasks & Enhancements

### High Priority
- **Resume Match Analytics**: Implement `/api/analytics/resumes` endpoint for resume-job matching statistics
- **Activity Logging**: Implement activity tracking for user actions and system events
- **Note Management**: Complete notes system for applications and interviews
- **Email Notifications**: Add email alerts for task reminders and interview schedules
- **File Upload Validation**: Enhance file upload security and validation

### Medium Priority
- **Advanced Analytics**: 
  - Response time analysis
  - Offer conversion probability
  - Company-wise success rates
  - Skill gap analysis
- **Search & Filtering**: Advanced search across applications, skills, and job descriptions
- **Data Export**: Export functionality for applications and analytics (CSV, PDF)
- **Calendar Integration**: Sync tasks and interviews with external calendars
- **Mobile App**: Consider native mobile application development

### Low Priority
- **Social Features**: Sharing anonymized success stories and tips
- **Machine Learning**: 
  - Automated skill extraction from job descriptions
  - Resume optimization suggestions
  - Interview question prediction
- **API Rate Limiting**: Implement rate limiting for API endpoints
- **Advanced Security**: 
  - Two-factor authentication
  - Session management
  - Password reset functionality
- **Performance Optimization**: 
  - Database query optimization
  - Frontend caching strategies
  - Image optimization for uploads

### Technical Debt
- **Frontend Modernization**: Consider migration to modern framework (Angular 2+, React, or Vue)
- **TypeScript Migration**: Add TypeScript for better type safety
- **Docker Containers**: Create Docker setup for easier deployment
- **CI/CD Pipeline**: Set up automated testing and deployment
- **Documentation**: Expand inline documentation and API docs
- **Error Handling**: Improve error messages and user feedback

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (v16+) and `npm` for frontend
- [Python](https://www.python.org/) (3.14+) for backend
- [MySQL](https://www.mysql.com/) (8.0+) for database

**Note**: The project uses Python 3.14+ which may require specific installation steps depending on your operating system. Ensure you have the correct Python version before proceeding.

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
   # Edit .env with your MySQL credentials and JWT secret
   ```

   Required environment variables:
   - `DATABASE_HOST`: MySQL server host (default: localhost)
   - `DATABASE_PORT`: MySQL server port (default: 3306)
   - `DATABASE_NAME`: Database name (default: job_command_center)
   - `DATABASE_USER`: MySQL username
   - `DATABASE_PASSWORD`: MySQL password
   - `JWT_SECRET_KEY`: Secret key for JWT token signing (generate a strong random string)
   - `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 60)

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

The frontend uses `http-server` for static file serving and includes:
- AngularJS 1.8.3 with ngRoute for SPA functionality
- Bootstrap 5.3.3 for responsive UI components
- SortableJS 1.15.7 for drag-and-drop Kanban functionality
- Bootstrap Icons 1.11.3 for iconography

### Running Tests

Backend tests:
```bash
cd backend
pytest -v
```

Note: Frontend testing is not currently implemented. Consider adding a testing framework like Jasmine or Karma for AngularJS unit tests.

## Troubleshooting

### Common Issues

**Backend won't start:**
- Ensure MySQL is running and accessible
- Check that database credentials in `.env` are correct
- Verify the database `job_command_center` exists
- Check that Python 3.14+ is installed and virtual environment is activated

**Frontend can't connect to backend:**
- Ensure backend is running on `http://localhost:8000`
- Check CORS configuration in backend (`app/main.py`)
- Verify API_CONFIG in frontend services points to correct backend URL
- Check browser console for CORS errors

**Authentication errors:**
- Verify JWT_SECRET_KEY is set in `.env`
- Check token expiration time (default 60 minutes)
- Ensure token is being sent in Authorization header
- Clear browser localStorage and re-login

**Database connection issues:**
- Verify MySQL service is running
- Check database credentials and host/port in `.env`
- Ensure user has proper permissions on the database
- Check firewall settings if MySQL is on remote server

## Development Guidelines

### Code Style
- **Backend**: Follow PEP 8 style guide for Python code
- **Frontend**: Use consistent JavaScript conventions, JSDoc comments for functions
- **Git**: Use conventional commit messages (feat:, fix:, docs:, etc.)

### Adding New Features
1. **Backend**: Create model → schema → router → service → tests
2. **Frontend**: Create service → controller → view → update routes
3. **Database**: Add migrations if schema changes are needed
4. **Testing**: Write tests for new backend endpoints
5. **Documentation**: Update README and inline code comments

### API Development
- Use FastAPI's dependency injection for database sessions
- Implement proper error handling with HTTPException
- Add comprehensive docstrings for all endpoints
- Use Pydantic schemas for request/response validation
- Follow RESTful conventions for API design

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with modern web technologies while maintaining legacy compatibility
- Inspired by the need for comprehensive job application tracking
- Uses open-source libraries and frameworks that make modern web development possible
