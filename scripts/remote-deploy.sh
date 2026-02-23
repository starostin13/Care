#!/bin/bash

# Remote deployment script that runs on Ubuntu server
# This script loads the Docker image and starts the application

set -e

IMAGE_NAME="carebot"
CONTAINER_NAME="carebot-app"

echo "🔧 Starting remote deployment..."

# Stop existing container if running
echo "🛑 Stopping existing container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Load new image
echo "📥 Loading Docker image..."
docker load < carebot.tar

# Create data directory if it doesn't exist
mkdir -p data
mkdir -p config

# Start new container
echo "🚀 Starting new container..."
docker-compose up -d

# Wait a moment for container to start
sleep 5

# Check if container is running
if docker ps | grep -q $CONTAINER_NAME; then
    echo "✅ Container started successfully!"
else
    echo "❌ Container failed to start!"
    echo "📋 Container logs:"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Show container status
echo "📊 Container status:"
docker ps | grep carebot

# Cleanup old images
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Remote deployment completed!"