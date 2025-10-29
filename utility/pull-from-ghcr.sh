#!/bin/bash
# Pull dcgm-fake-gpu-exporter from GitHub Container Registry (ghcr.io)

set -e

# Configuration
GITHUB_USER="${GITHUB_USER:-saiakhil2012}"
REPO_NAME="dcgm-fake-gpu-exporter"
IMAGE_NAME="dcgm-fake-gpu-exporter"
VERSION="${VERSION:-latest}"

echo "=========================================="
echo "Pull from GitHub Container Registry"
echo "=========================================="
echo ""
echo "GitHub User: ${GITHUB_USER}"
echo "Repository:  ${REPO_NAME}"
echo "Image:       ${IMAGE_NAME}"
echo "Version:     ${VERSION}"
echo ""

# GitHub Container Registry URL
GHCR_URL="ghcr.io/${GITHUB_USER}/${IMAGE_NAME}"
FULL_IMAGE="${GHCR_URL}:${VERSION}"

echo "=========================================="
echo "Step 1: Check Authentication"
echo "=========================================="
echo ""

# Check if package is public or needs authentication
echo "Attempting to pull ${FULL_IMAGE}..."
echo ""

# Try to pull without authentication first (works if package is public)
if docker pull "${FULL_IMAGE}" 2>/dev/null; then
    echo "✓ Successfully pulled (package is public)"
    AUTH_NEEDED=false
else
    echo "⚠ Pull failed - authentication may be required"
    echo ""
    echo "This means either:"
    echo "  1. The package is private (needs authentication)"
    echo "  2. The package doesn't exist yet"
    echo "  3. Network/connectivity issue"
    echo ""
    AUTH_NEEDED=true
fi

if [ "$AUTH_NEEDED" = true ]; then
    echo "=========================================="
    echo "Step 2: Authenticate with GitHub"
    echo "=========================================="
    echo ""
    echo "You need a GitHub Personal Access Token (PAT) with 'read:packages' scope."
    echo ""
    echo "To create one:"
    echo "1. Go to: https://github.com/settings/tokens/new"
    echo "2. Note: 'DCGM Exporter Package Access'"
    echo "3. Select scopes:"
    echo "   ✓ read:packages"
    echo "4. Click 'Generate token'"
    echo "5. Copy the token"
    echo ""
    
    # Check if already logged in
    if docker info 2>/dev/null | grep -q "ghcr.io"; then
        echo "✓ Already logged in to ghcr.io"
    else
        if [ -z "$GITHUB_TOKEN" ]; then
            echo "Enter your GitHub Personal Access Token:"
            read -s GITHUB_TOKEN
            echo ""
        fi
        
        echo "Logging in to ghcr.io..."
        echo "$GITHUB_TOKEN" | docker login ghcr.io -u "${GITHUB_USER}" --password-stdin
        
        if [ $? -eq 0 ]; then
            echo "✓ Login successful"
        else
            echo "❌ Login failed"
            exit 1
        fi
    fi
    
    echo ""
    echo "=========================================="
    echo "Step 3: Pull Image (Authenticated)"
    echo "=========================================="
    echo ""
    
    echo "Pulling ${FULL_IMAGE}..."
    docker pull "${FULL_IMAGE}"
    
    if [ $? -ne 0 ]; then
        echo "❌ Pull failed"
        echo ""
        echo "Possible reasons:"
        echo "  • Package doesn't exist at: ${FULL_IMAGE}"
        echo "  • Insufficient permissions on your token"
        echo "  • Wrong repository/username"
        echo ""
        echo "Available tags can be found at:"
        echo "  https://github.com/${GITHUB_USER}/${REPO_NAME}/pkgs/container/${IMAGE_NAME}"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "✅ Pull Complete!"
echo "=========================================="
echo ""

# Show image info
echo "Image Information:"
docker images | grep "${IMAGE_NAME}" | head -5
echo ""

# Get image size
IMAGE_SIZE=$(docker images "${FULL_IMAGE}" --format "{{.Size}}")
echo "Image size: ${IMAGE_SIZE}"
echo ""

echo "=========================================="
echo "Available Versions"
echo "=========================================="
echo ""
echo "To pull specific versions:"
echo "  VERSION=latest ./pull-from-ghcr.sh     # Latest build"
echo "  VERSION=20251028 ./pull-from-ghcr.sh   # Specific date"
echo "  VERSION=abc123 ./pull-from-ghcr.sh     # Specific commit"
echo ""
echo "Or directly:"
echo "  docker pull ${GHCR_URL}:latest"
echo "  docker pull ${GHCR_URL}:20251028"
echo ""

echo "=========================================="
echo "Quick Start - Run the Container"
echo "=========================================="
echo ""
echo "Run with default settings (4 GPUs, static profile):"
echo "  docker run -d -p 9400:9400 ${FULL_IMAGE}"
echo ""
echo "Run with custom settings:"
echo "  docker run -d -p 9400:9400 \\"
echo "    -e METRIC_PROFILE=spike \\"
echo "    -e NUM_GPUS=8 \\"
echo "    ${FULL_IMAGE}"
echo ""
echo "Available profiles:"
echo "  • static     - Fixed random values (default)"
echo "  • stable     - Realistic with small variations"
echo "  • spike      - Occasional random spikes"
echo "  • wave       - Sinusoidal wave patterns"
echo "  • degrading  - Performance gradually degrades"
echo "  • faulty     - Simulates hardware issues"
echo "  • chaos      - Completely random values"
echo ""

echo "=========================================="
echo "Test the Container"
echo "=========================================="
echo ""
echo "# Start container"
echo "docker run -d --name dcgm-test -p 9400:9400 ${FULL_IMAGE}"
echo ""
echo "# Wait for startup"
echo "sleep 10"
echo ""
echo "# Check if running"
echo "docker ps | grep dcgm-test"
echo ""
echo "# View logs"
echo "docker logs dcgm-test"
echo ""
echo "# Fetch metrics"
echo "curl http://localhost:9400/metrics | head -30"
echo ""
echo "# Check specific metrics"
echo "curl -s http://localhost:9400/metrics | grep 'DCGM_FI_DEV_GPU_TEMP'"
echo "curl -s http://localhost:9400/metrics | grep 'DCGM_FI_DEV_POWER_USAGE'"
echo ""
echo "# Stop and remove"
echo "docker stop dcgm-test && docker rm dcgm-test"
echo ""

echo "=========================================="
echo "Test Different Profiles"
echo "=========================================="
echo ""
echo "# Spike profile (occasional spikes in metrics):"
echo "docker run -d --name gpu-spike -p 9401:9400 \\"
echo "  -e METRIC_PROFILE=spike -e NUM_GPUS=4 ${FULL_IMAGE}"
echo ""
echo "# Wave profile (sinusoidal patterns):"
echo "docker run -d --name gpu-wave -p 9402:9400 \\"
echo "  -e METRIC_PROFILE=wave -e NUM_GPUS=2 ${FULL_IMAGE}"
echo ""
echo "# Large scale (100 GPUs):"
echo "docker run -d --name gpu-scale -p 9403:9400 \\"
echo "  -e METRIC_PROFILE=stable -e NUM_GPUS=100 ${FULL_IMAGE}"
echo ""
echo "# Mixed profiles (different profile per GPU):"
echo "docker run -d --name gpu-mixed -p 9404:9400 \\"
echo "  -e NUM_GPUS=4 -e GPU_PROFILES=static,spike,wave,chaos ${FULL_IMAGE}"
echo ""

echo "=========================================="
echo "Environment Variables"
echo "=========================================="
echo ""
echo "  METRIC_PROFILE         - Default profile (default: static)"
echo "  NUM_GPUS              - Number of fake GPUs (default: 4)"
echo "  GPU_PROFILES          - Comma-separated per-GPU profiles"
echo "  METRIC_UPDATE_INTERVAL - Update interval in seconds (default: 30)"
echo "  GPU_START_INDEX       - Starting GPU index (default: 0)"
echo "  EXPORTER_PORT         - Metrics port (default: 9400)"
echo ""

echo "=========================================="
echo "Troubleshooting"
echo "=========================================="
echo ""
echo "Container won't start:"
echo "  docker logs <container_name>"
echo "  # Check if port 9400 is already in use"
echo "  # Try different port: -p 9401:9400"
echo ""
echo "No metrics returned:"
echo "  docker exec <container_name> curl http://localhost:9400/metrics"
echo "  docker exec <container_name> ps aux | grep nv-hostengine"
echo ""
echo "Update to latest version:"
echo "  docker pull ${GHCR_URL}:latest"
echo "  docker stop <container_name> && docker rm <container_name>"
echo "  docker run -d -p 9400:9400 ${GHCR_URL}:latest"
echo ""

echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Run the container:"
echo "   docker run -d -p 9400:9400 ${FULL_IMAGE}"
echo ""
echo "2. Test metrics endpoint:"
echo "   curl http://localhost:9400/metrics"
echo ""
echo "3. Set up Prometheus to scrape metrics"
echo ""
echo "4. Import Grafana dashboard for visualization"
echo ""
echo "5. Test different profiles and scale scenarios"
echo ""
echo "📚 Documentation:"
echo "   https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "=========================================="
echo ""
