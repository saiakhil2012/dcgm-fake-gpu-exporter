#!/bin/bash
# Push dcgm-fake-gpu-exporter to GitHub Container Registry (ghcr.io)

set -e

# Configuration
GITHUB_USER="${GITHUB_USER:-saiakhil2012}"
REPO_NAME="dcgm-fake-gpu-exporter"
IMAGE_NAME="dcgm-fake-gpu-exporter"
VERSION="${VERSION:-latest}"

echo "=========================================="
echo "Push to GitHub Container Registry"
echo "=========================================="
echo ""
echo "GitHub User: ${GITHUB_USER}"
echo "Repository:  ${REPO_NAME}"
echo "Image:       ${IMAGE_NAME}"
echo "Version:     ${VERSION}"
echo ""

# Check if image exists locally
if ! docker images | grep -q "${IMAGE_NAME}.*latest"; then
    echo "❌ Error: ${IMAGE_NAME}:latest not found locally"
    echo "Please build the image first with: ./build-optimized.sh"
    exit 1
fi

# Show current image info
echo "Local image info:"
docker images | grep "${IMAGE_NAME}" | head -5
echo ""

# GitHub Container Registry URL
GHCR_URL="ghcr.io/${GITHUB_USER}/${IMAGE_NAME}"

echo "=========================================="
echo "Step 1: Authenticate with GitHub"
echo "=========================================="
echo ""
echo "You need a GitHub Personal Access Token (PAT) with 'write:packages' scope."
echo ""
echo "To create one:"
echo "1. Go to: https://github.com/settings/tokens/new"
echo "2. Note: 'DCGM Exporter Package Access'"
echo "3. Select scopes:"
echo "   ✓ write:packages"
echo "   ✓ read:packages"
echo "   ✓ delete:packages (optional)"
echo "4. Click 'Generate token'"
echo "5. Copy the token"
echo ""
echo "Then run:"
echo "  export GITHUB_TOKEN='your_token_here'"
echo "  echo \$GITHUB_TOKEN | docker login ghcr.io -u ${GITHUB_USER} --password-stdin"
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
echo "Step 2: Tag Image"
echo "=========================================="
echo ""

# Tag with version
echo "Tagging ${IMAGE_NAME}:latest as ${GHCR_URL}:${VERSION}..."
docker tag "${IMAGE_NAME}:latest" "${GHCR_URL}:${VERSION}"

# Also tag with date for versioning
DATE_TAG=$(date +%Y%m%d)
echo "Tagging ${IMAGE_NAME}:latest as ${GHCR_URL}:${DATE_TAG}..."
docker tag "${IMAGE_NAME}:latest" "${GHCR_URL}:${DATE_TAG}"

# Tag with git commit if in git repo
if git rev-parse --git-dir > /dev/null 2>&1; then
    GIT_COMMIT=$(git rev-parse --short HEAD)
    echo "Tagging ${IMAGE_NAME}:latest as ${GHCR_URL}:${GIT_COMMIT}..."
    docker tag "${IMAGE_NAME}:latest" "${GHCR_URL}:${GIT_COMMIT}"
fi

echo "✓ Tagging complete"
echo ""

echo "=========================================="
echo "Step 3: Push to GitHub Container Registry"
echo "=========================================="
echo ""

# Push latest tag
echo "Pushing ${GHCR_URL}:${VERSION}..."
docker push "${GHCR_URL}:${VERSION}"

# Push date tag
echo ""
echo "Pushing ${GHCR_URL}:${DATE_TAG}..."
docker push "${GHCR_URL}:${DATE_TAG}"

# Push git commit tag if exists
if [ -n "$GIT_COMMIT" ]; then
    echo ""
    echo "Pushing ${GHCR_URL}:${GIT_COMMIT}..."
    docker push "${GHCR_URL}:${GIT_COMMIT}"
fi

echo ""
echo "=========================================="
echo "✅ Push Complete!"
echo "=========================================="
echo ""
echo "Your image is now available at:"
echo "  ${GHCR_URL}:latest"
echo "  ${GHCR_URL}:${DATE_TAG}"
if [ -n "$GIT_COMMIT" ]; then
    echo "  ${GHCR_URL}:${GIT_COMMIT}"
fi
echo ""
echo "=========================================="
echo "Step 4: Make Package Public (Important!)"
echo "=========================================="
echo ""
echo "By default, GitHub packages are private. To make it public:"
echo ""
echo "1. Go to: https://github.com/${GITHUB_USER}?tab=packages"
echo "2. Click on '${IMAGE_NAME}'"
echo "3. Click 'Package settings' (right side)"
echo "4. Scroll to 'Danger Zone'"
echo "5. Click 'Change visibility'"
echo "6. Select 'Public' and confirm"
echo ""
echo "=========================================="
echo "Usage in UTM VM (Ubuntu AMD64)"
echo "=========================================="
echo ""
echo "# Pull the image:"
echo "docker pull ${GHCR_URL}:latest"
echo ""
echo "# Run with default settings (4 GPUs, static profile):"
echo "docker run -d -p 9400:9400 ${GHCR_URL}:latest"
echo ""
echo "# Run with custom settings:"
echo "docker run -d -p 9400:9400 \\"
echo "  -e METRIC_PROFILE=spike \\"
echo "  -e NUM_GPUS=8 \\"
echo "  ${GHCR_URL}:latest"
echo ""
echo "# Test the metrics:"
echo "curl http://localhost:9400/metrics | head -20"
echo ""
echo "=========================================="
echo ""
