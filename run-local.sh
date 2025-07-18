#!/bin/bash

echo "🚀 Starting InnerSelf Local Development"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please copy .env.example to .env and configure it."
    exit 1
fi

# Load environment variables
export $(cat .env | xargs)

# Check required environment variables
if [ -z "$GITHUB_CLIENT_ID" ] || [ -z "$GITHUB_CLIENT_SECRET" ]; then
    echo "❌ GitHub OAuth credentials not configured!"
    echo "Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env"
    exit 1
fi

echo "✅ Environment configured"

# Start MongoDB if not running
if ! pgrep -x "mongod" > /dev/null; then
    echo "🍃 Starting MongoDB..."
    mongod --dbpath ./data/db --fork --logpath ./data/mongodb.log
    sleep 3
fi

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Stopping services..."
    jobs -p | xargs -r kill
    exit
}
trap cleanup EXIT

# Start Backend
echo "🔧 Starting Backend API..."
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start GitHub Service
echo "🐙 Starting GitHub Service..."
cd github-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &
GITHUB_PID=$!
cd ..

# Start Frontend
echo "⚛️ Starting Frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 InnerSelf is starting up!"
echo ""
echo "📱 Frontend:     http://localhost:3000"
echo "🔧 Backend API:  http://localhost:8000"
echo "📚 API Docs:     http://localhost:8000/docs"
echo "🐙 GitHub API:   http://localhost:8001"
echo ""
echo "💡 Tip: Create a GitHub OAuth app and add credentials to .env"
echo "📖 See docs/deployment.md for detailed setup instructions"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for all background processes
wait