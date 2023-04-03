#!/bin/bash

# Parse command-line arguments
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <image-name>"
    exit 1
fi
image_name="$1"

# Log in to ECR
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 384850799342.dkr.ecr.eu-central-1.amazonaws.com

# Build the Docker image
docker build -t "$image_name" .

# Create ECR repository
#aws ecr create-repository --repository-name "$image_name"

# Tag the Docker image
docker tag "$image_name":latest 384850799342.dkr.ecr.eu-central-1.amazonaws.com/"$image_name":latest

# Push the Docker image to ECR
docker push 384850799342.dkr.ecr.eu-central-1.amazonaws.com/"$image_name":latest

# Delete repository
#  aws ecr delete-repository --repository-name "$image_name" --force