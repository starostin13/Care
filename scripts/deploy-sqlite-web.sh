#!/bin/bash
# Script to deploy CareBot with SQLite Web interface

set -e

echo "🚀 Deploying CareBot with SQLite Web interface..."

# Configuration
REMOTE_HOST="ubuntu@192.168.0.125"
REMOTE_DIR="/home/ubuntu/carebot-production"
LOCAL_DIR="."

echo "📂 Creating remote directory structure..."
ssh $REMOTE_HOST "mkdir -p $REMOTE_DIR/data"

echo "📤 Copying files to remote server..."
# Copy main application files
scp -r CareBot $REMOTE_HOST:$REMOTE_DIR/
scp docker-compose.sqlite-web.yml $REMOTE_HOST:$REMOTE_DIR/docker-compose.yml
scp Dockerfile.production $REMOTE_HOST:$REMOTE_DIR/CareBot/Dockerfile
scp .env $REMOTE_HOST:$REMOTE_DIR/
scp entrypoint.sh $REMOTE_HOST:$REMOTE_DIR/

echo "🔧 Setting up permissions..."
ssh $REMOTE_HOST "chmod +x $REMOTE_DIR/entrypoint.sh"

echo "🛑 Stopping existing services..."
ssh $REMOTE_HOST "cd $REMOTE_DIR && docker-compose down || true"

echo "🏗️ Building and starting services..."
ssh $REMOTE_HOST "cd $REMOTE_DIR && docker-compose build --no-cache"
ssh $REMOTE_HOST "cd $REMOTE_DIR && docker-compose up -d"

echo "⏳ Waiting for services to start..."
sleep 10

echo "🔍 Checking service status..."
ssh $REMOTE_HOST "cd $REMOTE_DIR && docker-compose ps"

echo "🏥 Checking health..."
if ssh $REMOTE_HOST "curl -f http://localhost:5555/health" > /dev/null 2>&1; then
    echo "✅ CareBot is healthy!"
else
    echo "❌ CareBot health check failed"
fi

if ssh $REMOTE_HOST "curl -f http://localhost:8080" > /dev/null 2>&1; then
    echo "✅ SQLite Web is running!"
    echo "🌐 SQLite Web interface available at: http://192.168.0.125:8080"
else
    echo "❌ SQLite Web is not responding"
fi

echo "📊 Service logs:"
echo "--- CareBot logs ---"
ssh $REMOTE_HOST "cd $REMOTE_DIR && docker logs carebot_production --tail=5"
echo "--- SQLite Web logs ---"
ssh $REMOTE_HOST "cd $REMOTE_DIR && docker logs carebot_sqlite_web --tail=5"

echo "✅ Deployment completed!"
echo ""
echo "🔗 Access points:"
echo "   CareBot API: http://192.168.0.125:5555"
echo "   SQLite Web:  http://192.168.0.125:8080"
echo ""
echo "🛠️ Management commands:"
echo "   View logs: ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker-compose logs -f'"
echo "   Restart:   ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker-compose restart'"
echo "   Stop:      ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker-compose down'"