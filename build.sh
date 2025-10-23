#!/bin/bash
# Build script for DCGM Fake GPU Exporter

set -e

DCGM_DIR="${DCGM_DIR:-$HOME/Workspace/DCGM/_out/Linux-amd64-debug}"
IMAGE_NAME="${IMAGE_NAME:-dcgm-fake-gpu-exporter}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "=========================================="
echo "DCGM Fake GPU Exporter - Build Script"
echo "=========================================="
echo ""

# Check if DCGM directory exists
if [ ! -d "$DCGM_DIR" ]; then
    echo "Error: DCGM directory not found: $DCGM_DIR"
    echo ""
    echo "Please set DCGM_DIR environment variable to your DCGM build directory"
    echo "Example: export DCGM_DIR=~/Workspace/DCGM/_out/Linux-amd64-debug"
    exit 1
fi

# Create dcgm directory for Docker build context
echo "Preparing build context..."
rm -rf dcgm
mkdir -p dcgm

# Copy DCGM files
echo "Copying DCGM binaries..."
cp -r "$DCGM_DIR/bin" dcgm/
cp -r "$DCGM_DIR/lib" dcgm/
cp -r "$DCGM_DIR/share" dcgm/

# Build Docker image
echo ""
echo "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

# Cleanup
echo ""
echo "Cleaning up..."
rm -rf dcgm

echo ""
echo "=========================================="
echo "Build complete!"
echo "=========================================="
echo ""
echo "Run with:"
echo "  docker-compose up -d"
echo ""
echo "Or:"
echo "  docker run -d -p 9400:9400 ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""