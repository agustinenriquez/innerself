# InnerSelf

An essence-based messaging system for small development teams that integrates with GitHub to track developer performance and prevent micromanagement.

## Features

- Team messaging with essence scoring
- GitHub integration for PR/commit tracking
- Micromanagement detection and prevention
- Role-based essence weights (PM, Developer, QA)
- "Common sense" discussion quality assessment
- Real-time essence updates and notifications

## Tech Stack

- **Backend**: FastAPI + Python 3.12
- **Database**: MongoDB
- **Frontend**: React + TypeScript
- **GitHub Integration**: GitHub API + Webhooks
- **Real-time**: WebSockets
- **Deployment**: Docker + Docker Compose

## Quick Start

```bash
# Start development environment
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8080
# API Docs: http://localhost:8080/docs
```

## Testing

### Backend Tests

The backend includes comprehensive unit tests for all major functionality including Glassdoor scraping, GitHub integration, and API endpoints.

#### Run All Tests
```bash
# Using Docker (recommended)
docker exec innerself-backend-1 bash -c "cd /app && PYTHONPATH=/app python -m pytest app/tests/ -v"

# Quick summary
docker exec innerself-backend-1 bash -c "cd /app && PYTHONPATH=/app python -m pytest app/tests/ --tb=no -q"
```

#### Run Specific Test Suites
```bash
# Test Glassdoor scraping functionality
docker exec innerself-backend-1 bash -c "cd /app && PYTHONPATH=/app python -m pytest app/tests/test_glassdoor_scraper.py -v"

# Test API endpoints
docker exec innerself-backend-1 bash -c "cd /app && PYTHONPATH=/app python -m pytest app/tests/test_glassdoor_api.py -v"

# Test error handling and edge cases
docker exec innerself-backend-1 bash -c "cd /app && PYTHONPATH=/app python -m pytest app/tests/test_glassdoor_edge_cases.py -v"
```

#### Inside Container Testing
```bash
# Access the backend container
docker exec -it innerself-backend-1 bash

# Run tests from inside container
cd /app
PYTHONPATH=/app python -m pytest app/tests/ -v
```

#### Test Coverage

The test suite includes:
- ✅ **42+ unit tests** covering core functionality  
- ✅ **Glassdoor web scraping** with mock HTML responses
- ✅ **API endpoint testing** with authentication and database mocking
- ✅ **Error handling** for network failures, malformed data, and edge cases
- ✅ **Security testing** against SQL injection and XSS attempts
- ✅ **GitHub API integration** with mock responses
- ✅ **Database operations** with MongoDB mocking
- ✅ **Async/await patterns** and concurrent request handling

### Frontend Tests

```bash
# Run frontend tests (if implemented)
cd frontend
npm test
```

## Project Structure

```
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API routes and endpoints
│   │   ├── models/    # Pydantic data models
│   │   ├── services/  # Business logic and external integrations
│   │   └── tests/     # Unit tests and fixtures
├── frontend/          # React frontend  
├── github-service/    # GitHub integration service
├── docker-compose.yml # Development environment
└── README.md         # This file
```