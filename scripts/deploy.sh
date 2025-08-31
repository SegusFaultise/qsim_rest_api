#!/bin/bash

echo "Starting deployment..."

# Pull the latest code from the main branch
git pull origin main

# Take down any currently running containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.v2.yml down

# Rebuild the Docker image and restart the containers
echo "Building new image and starting containers..."
docker-compose -f docker-compose.prod.v2.yml up --build -d

echo "Deployment complete!"
