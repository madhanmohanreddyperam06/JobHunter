# Frontend — Job Application Command Center

![AngularJS](https://img.shields.io/badge/AngularJS-1.8.x-orange?style=flat-square&logo=angularjs)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.x-7952B3?style=flat-square&logo=bootstrap)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat-square&logo=javascript)

## Overview

The frontend is a single-page application (SPA) built with **AngularJS 1.8.x** and **Bootstrap 5.3.x**. It provides a modern, responsive interface for managing job applications, interviews, tasks, resumes, and skills through an intuitive dashboard.

## Technology Stack

- **Framework**: AngularJS 1.8.x with `ngRoute` for client-side routing
- **Language**: JavaScript (ES6+)
- **Styling**: Bootstrap 5.3.x with custom Slate/Navy CSS3 theme
- **Icons**: Bootstrap Icons 1.11.3
- **Drag & Drop**: SortableJS 1.15.7 for Kanban board
- **HTTP Server**: http-server 14.1.1 for development
- **Markup**: Semantic HTML5

## Architecture

The frontend follows a clean MVC architecture with separation of concerns:

```text
AngularJS Application
     │
     ├─ Routes (ngRoute)
     │  └─ URL routing to controllers
     │
     ├─ Controllers
     │  └─ Business logic & state management
     │
     ├─ Services
     │  └─ API communication & data fetching
     │
     ├─ Directives
     │  └─ Reusable UI components
     │
     ├─ Filters
     │  └─ Data formatting & transformation
     │
     └─ Views
     └─ HTML templates with data binding
```

## Project Structure

```text
frontend/
├── index.html                 # Main application entry point
├── package.json               # Node.js dependencies
├── app/                       # Application source code
│   ├── app.js                 # AngularJS module declaration
│   ├── routes.js              # Route configuration
│   ├── controllers/           # Page controllers
│   │   ├── dashboard.controller.js
│   │   ├── applications.controller.js
│   │   ├── kanban.controller.js
│   │   ├── interviews.controller.js
│   │   ├── tasks.controller.js
│   │   ├── resumes.controller.js
│   │   ├── job-descriptions.controller.js
│   │   ├── skills.controller.js
│   │   ├── analytics.controller.js
│   │   ├── login.controller.js
│   │   ├── register.controller.js
│   │   └── settings.controller.js
│   ├── services/              # API services
│   │   ├── auth.service.js
│   │   ├── auth-interceptor.service.js
│   │   ├── application.service.js
│   │   ├── interview.service.js
│   │   ├── task.service.js
│   │   ├── resume.service.js
│   │   ├── job-description.service.js
│   │   ├── skill.service.js
│   │   └── analytics.service.js
│   ├── directives/            # Custom directives
│   │   ├── job-card.directive.js
│   │   ├── status-badge.directive.js
│   │   ├── priority-badge.directive.js
│   │   └── kanban-sortable.directive.js
│   ├── filters/               # Custom filters
│   │   └── status.filter.js
│   ├── views/                 # HTML templates
│   │   ├── dashboard.html
│   │   ├── applications.html
│   │   ├── kanban.html
│   │   ├── interviews.html
│   │   ├── tasks.html
│   │   ├── resumes.html
│   │   ├── job-descriptions.html
│   │   ├── skills.html
│   │   ├── analytics.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── settings.html
│   └── components/            # Reusable components
│       ├── navbar/
│       ├── sidebar/
│       └── stat-card/
├── assets/                    # Static assets
│   ├── images/
│   └── icons/
└── styles/                     # CSS stylesheets
    ├── main.css               # Base styles & variables
    ├── layout.css             # Layout & positioning
    ├── components.css         # Component styles
    └── responsive.css         # Media queries
```

## Features Implemented

### Core Pages
- **Dashboard**: Overview with statistics and recent activity
- **Applications**: Full CRUD for job applications with filtering and search
- **Kanban Board**: Drag-and-drop pipeline management
- **Interviews**: Interview scheduling and management
- **Tasks**: Task tracking with priorities and due dates
- **Resumes**: Resume version management
- **Job Descriptions**: Job posting storage and analysis
- **Skills**: Skills inventory and proficiency tracking
- **Analytics**: Application metrics and visualizations
- **Settings**: User preferences and configuration

### Authentication
- Login page with JWT token authentication
- Registration page for new users
- Protected route handling with auth interceptor
- Session management via sessionStorage

### UI Components
- Responsive navigation bar
- Collapsible sidebar
- Status badges with color coding
- Priority indicators
- Stat cards for metrics
- Modal dialogs for forms
- Toast notifications

## Getting Started

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Development

Start the development server:
```bash
npm start
```

The application will be available at [http://localhost:3000](http://localhost:3000)

### Build for Production

Currently using http-server for development. For production deployment, consider:
- Minifying JavaScript and CSS
- Optimizing images
- Using a production web server (nginx, Apache)
- Implementing proper caching strategies

## API Integration

The frontend communicates with the FastAPI backend via REST API:

- **Base URL**: `http://localhost:8000/api`
- **Authentication**: JWT Bearer tokens stored in sessionStorage
- **Content-Type**: `application/json`

### API Endpoints Used

- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `GET /api/applications` - List applications
- `POST /api/applications` - Create application
- `PUT /api/applications/{id}` - Update application
- `DELETE /api/applications/{id}` - Delete application
- `GET /api/interviews` - List interviews
- `POST /api/interviews` - Create interview
- `GET /api/tasks` - List tasks
- `POST /api/tasks` - Create task
- `GET /api/resumes` - List resumes
- `POST /api/resumes` - Create resume
- `GET /api/job-descriptions` - List job descriptions
- `POST /api/job-descriptions` - Create job description
- `GET /api/skills` - List skills
- `POST /api/skills` - Create skill
- `GET /api/analytics` - Get analytics data

## Development Notes

### State Management
- AngularJS scope for component state
- Services for shared application state
- sessionStorage for authentication tokens

### Routing
- ngRoute for client-side routing
- Route parameters for detail views
- Route guards for protected pages

### Styling
- Bootstrap 5 utility classes
- Custom CSS variables for theming
- Responsive design with media queries
- Mobile-first approach

### Performance
- Lazy loading of views
- Optimized HTTP requests
- Efficient DOM manipulation
- Caching strategies for API calls

## Browser Compatibility

- Chrome/Edge (recommended)
- Firefox
- Safari
- Modern browsers with ES6+ support

## Current Status

✅ **FULLY FUNCTIONAL**

All planned frontend features have been implemented and are working with the backend API.
