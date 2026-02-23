#!/bin/bash

# CareBot Deployment Script
# This script deploys the CareBot application to Ubuntu server

set -e

# Configuration
REMOTE_USER="ubuntu"
REMOTE_HOST="192.168.1.125"
REMOTE_PATH="/home/ubuntu/carebot"
IMAGE_NAME="carebot"
CONTAINER_NAME="carebot-app"

echo "🚀 Starting CareBot deployment..."

# Build Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

# Save image to tar file
echo "💾 Saving Docker image..."
docker save $IMAGE_NAME > carebot.tar

# Copy files to remote server
echo "📤 Copying files to remote server..."
scp carebot.tar docker-compose.yml $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

# Copy deployment scripts
scp scripts/remote-deploy.sh $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

# Execute deployment on remote server
echo "🔧 Executing deployment on remote server..."
ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_PATH && chmod +x remote-deploy.sh && ./remote-deploy.sh"

# Cleanup local tar file
rm carebot.tar

echo "✅ Deployment completed successfully!"
echo "🌐 Application should be available at http://$REMOTE_HOST:5555"

# Test connection
echo "🧪 Testing connection..."
if curl -f http://$REMOTE_HOST:5555/health > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed - please check logs"
fi