#!/bin/bash
set -e

# Ensure Docker is running
sudo systemctl start docker

cd /home/ubuntu

# Fetch deployment files from S3
aws s3 cp s3://sentiment-analysis-docker-compose-bucket/docker-compose.yaml /home/ubuntu/docker-compose.yaml
aws s3 cp s3://sentiment-analysis-docker-compose-bucket/.env /home/ubuntu/.env

sudo chown ubuntu:ubuntu /home/ubuntu/docker-compose.yaml /home/ubuntu/.env
chmod 600 /home/ubuntu/.env


# Login to AWS ECR
aws ecr get-login-password --region eu-north-1 | sudo docker login \
  --username AWS \
  --password-stdin 660838764267.dkr.ecr.eu-north-1.amazonaws.com

# Pull latest API image defined under the "api" service in docker-compose.yaml
sudo docker compose pull api

# Stop existing app stack if it exists
sudo docker compose down --remove-orphans

# Clean up any old single-container deployment, if created earlier
sudo docker rm -f sentiment-analysis-api 2>/dev/null || true

# Start full app stack: api + postgres + redis
sudo docker compose up -d

# Optional cleanup
sudo docker image prune -f