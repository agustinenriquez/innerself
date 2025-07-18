# InnerSelf Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.12+ (for local development)
- MongoDB (production deployment)
- GitHub OAuth App credentials

## Environment Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd innerself
```

2. **Setup environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
# GitHub OAuth (required)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# JWT Secret (generate a strong secret)
JWT_SECRET=your-super-secret-jwt-key

# Database
MONGODB_URL=mongodb://mongodb:27017/innerself
```

## Local Development

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# GitHub Service: http://localhost:8001
# MongoDB: localhost:27017
```

### Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**GitHub Service:**
```bash
cd github-service
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## GitHub OAuth Setup

1. **Create GitHub OAuth App**
   - Go to GitHub Settings > Developer settings > OAuth Apps
   - Click "New OAuth App"
   - Fill in details:
     - Application name: InnerSelf
     - Homepage URL: http://localhost:3000 (or your domain)
     - Authorization callback URL: http://localhost:8000/auth/github/callback

2. **Setup Webhooks (Optional)**
   - Go to your organization/repo settings
   - Add webhook: http://your-domain:8001/webhook
   - Select events: Pull requests, Push, Pull request reviews, Issues
   - Set webhook secret (same as GITHUB_WEBHOOK_SECRET)

## Production Deployment

### Docker Deployment

1. **Update docker-compose.yml for production**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://your-production-mongodb:27017/innerself
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - JWT_SECRET=${JWT_SECRET}
    restart: unless-stopped
    
  frontend:
    build: 
      context: ./frontend
      args:
        - REACT_APP_API_URL=https://your-api-domain.com
    ports:
      - "3000:3000"
    restart: unless-stopped
    
  github-service:
    build: ./github-service
    ports:
      - "8001:8000"
    environment:
      - MONGODB_URL=mongodb://your-production-mongodb:27017/innerself
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
    restart: unless-stopped
```

2. **Deploy with SSL/TLS**
   - Use nginx as reverse proxy
   - Setup SSL certificates (Let's Encrypt recommended)
   - Configure proper CORS settings

### Cloud Deployment Options

**AWS:**
- ECS with Fargate for containers
- DocumentDB for MongoDB
- ALB for load balancing
- Route53 for DNS

**Google Cloud:**
- Cloud Run for containers
- MongoDB Atlas for database
- Cloud Load Balancing
- Cloud DNS

**DigitalOcean:**
- App Platform for easy deployment
- Managed MongoDB
- Load Balancers

## Database Indexes

For optimal performance, create these MongoDB indexes:

```javascript
// Users collection
db.users.createIndex({ "github_profile.github_id": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "essence.overall": -1 })

// Messages collection
db.messages.createIndex({ "channel": 1, "timestamp": -1 })
db.messages.createIndex({ "author_id": 1, "timestamp": -1 })

// Essence logs collection
db.essence_logs.createIndex({ "user_id": 1, "created_at": -1 })
db.essence_logs.createIndex({ "created_at": -1 })

// GitHub activity collections
db.pull_requests.createIndex({ "user_id": 1, "created_at": -1 })
db.commit_activity.createIndex({ "user_id": 1, "commit_time": -1 })
db.code_reviews.createIndex({ "reviewer_id": 1, "created_at": -1 })
```

## Monitoring & Logging

1. **Application Logs**
   - Backend logs to stdout (captured by Docker)
   - Frontend build logs
   - GitHub service webhook logs

2. **Metrics to Monitor**
   - API response times
   - Database connection pool
   - WebSocket connections
   - GitHub webhook success rate
   - Essence calculation accuracy

3. **Health Checks**
   - `/health` endpoint on all services
   - Database connectivity
   - GitHub API rate limits

## Security Considerations

1. **Environment Variables**
   - Never commit secrets to git
   - Use proper secret management in production
   - Rotate GitHub OAuth secrets regularly

2. **Database Security**
   - Enable MongoDB authentication
   - Use SSL/TLS for database connections
   - Regular backups

3. **API Security**
   - Rate limiting on public endpoints
   - Input validation and sanitization
   - CORS configuration
   - JWT token expiration

## Backup Strategy

1. **Database Backups**
   - Daily automated MongoDB dumps
   - Store backups in multiple locations
   - Test restore procedures regularly

2. **Code Backups**
   - Git repository (already handled)
   - Container registry backups
   - Configuration backups

## Troubleshooting

**Common Issues:**

1. **GitHub OAuth not working**
   - Check callback URL matches exactly
   - Verify client ID/secret
   - Check network connectivity

2. **WebSocket connection fails**
   - Verify CORS settings
   - Check proxy configuration
   - Ensure WebSocket support in load balancer

3. **Essence calculations seem wrong**
   - Check GitHub webhook delivery
   - Verify user GitHub profile linking
   - Review essence calculation logs

4. **High memory usage**
   - Check for memory leaks in WebSocket connections
   - Review database query efficiency
   - Monitor essence calculation batch jobs

## Scaling

**Horizontal Scaling:**
- Multiple backend instances behind load balancer
- Separate GitHub service instances
- MongoDB replica set for high availability

**Performance Optimization:**
- Redis for caching frequently accessed data
- CDN for frontend assets
- Database query optimization
- Background job queue for heavy calculations