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

# Run tests
pytest

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Project Structure

```
├── backend/           # FastAPI backend
├── frontend/          # React frontend
├── github-service/    # GitHub integration service
├── docker-compose.yml # Development environment
└── docs/             # Documentation
```