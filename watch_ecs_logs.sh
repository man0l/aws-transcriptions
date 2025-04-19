#!/bin/bash

# Configuration
CLUSTER_NAME="bobi-transcribe-demo-cluster"
SERVICE_NAME="bobi-transcribe-demo-worker"
LOG_GROUP_NAME="/ecs/bobi-transcribe-demo-worker"
PROFILE="bobimoskov"
REGION="eu-central-1"

# Colors for better visibility
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Watching logs for ECS service ${SERVICE_NAME}${NC}"
echo -e "${BLUE}Log Group: ${LOG_GROUP_NAME}${NC}"
echo -e "${YELLOW}Fetching all logs from the last hour...${NC}"
echo -e "${BLUE}Press Ctrl+C to exit${NC}"

# Get the latest logs without filtering by task ID
aws logs tail $LOG_GROUP_NAME \
    --profile $PROFILE \
    --region $REGION \
    --since 1h \
    --follow 