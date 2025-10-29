#!/bin/bash
# Quick test script for dcgm-fake-gpu-exporter
# Tests basic functionality with static profile

set -e

IMAGE_NAME="dcgm-fake-gpu-exporter:latest"
CONTAINER_NAME="test-dcgm-exporter"
PORT=9401

echo "🧪 Quick Test: dcgm-fake-gpu-exporter"
echo "====================================="

# Clean up any existing container
echo "Cleaning up existing containers..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# Start container with static profile and 4 GPUs
echo -e "\n🚀 Starting container with STATIC profile and 4 GPUs..."
docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${PORT}:9400 \
  -e METRIC_PROFILE=static \
  -e NUM_GPUS=4 \
  ${IMAGE_NAME}

# Wait for container to be ready
echo -n "⏳ Waiting for metrics endpoint to be ready"
for i in {1..30}; do
  if curl -s http://localhost:${PORT}/metrics > /dev/null 2>&1; then
    echo -e " ✓"
    break
  fi
  echo -n "."
  sleep 1
done

# Show container status
echo -e "\n📊 Container Status:"
docker ps | grep ${CONTAINER_NAME}

# Fetch metrics
echo -e "\n📈 Fetching metrics..."
METRICS=$(curl -s http://localhost:${PORT}/metrics)

# Count GPUs in metrics
GPU_COUNT=$(echo "$METRICS" | grep -o 'gpu="[0-9]*"' | sort -u | wc -l | tr -d ' ')
echo "✓ Found metrics for ${GPU_COUNT} GPUs"

# Check for key metrics
echo -e "\n🔍 Key Metrics Check:"
echo "$METRICS" | grep "DCGM_FI_DEV_GPU_TEMP" | head -4
echo "$METRICS" | grep "DCGM_FI_DEV_POWER_USAGE" | head -4
echo "$METRICS" | grep "DCGM_FI_DEV_GPU_UTIL" | head -4

# Show container logs
echo -e "\n📝 Container Logs:"
docker logs ${CONTAINER_NAME} 2>&1 | tail -15

echo -e "\n✅ Test complete!"
echo -e "\n💡 Useful commands:"
echo "  • View metrics: curl http://localhost:${PORT}/metrics"
echo "  • View logs:    docker logs ${CONTAINER_NAME}"
echo "  • Stop:         docker stop ${CONTAINER_NAME}"
echo "  • Clean up:     docker rm ${CONTAINER_NAME}"
echo ""
