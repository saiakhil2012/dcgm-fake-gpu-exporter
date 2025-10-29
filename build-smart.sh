#!/bin/bash
# Smart build script for DCGM Fake GPU Exporter
# Automatically detects which build method to use

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="dcgm-fake-gpu-exporter"
TAG="${TAG:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${TAG}"

echo ""
echo "=========================================="
echo "DCGM Fake GPU Exporter - Smart Build"
echo "=========================================="
echo ""

# Function to check if binaries exist
check_binaries() {
    local dcgm_dir="${DCGM_DIR:-$HOME/Workspace/DCGM/_out/Linux-amd64-debug}"
    
    if [ -d "$dcgm_dir/bin" ] && \
       [ -f "$dcgm_dir/bin/nv-hostengine" ] && \
       [ -d "$dcgm_dir/lib" ] && \
       [ -d "$dcgm_dir/share/dcgm_tests" ]; then
        return 0
    else
        return 1
    fi
}

# Function to check if base image exists
check_base_image() {
    if docker image inspect "${IMAGE_NAME}:latest" &> /dev/null || \
       docker image inspect "${IMAGE_NAME}:base" &> /dev/null || \
       docker image inspect "${IMAGE_NAME}:v1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Auto-detect build method
auto_detect() {
    echo -e "${BLUE}Auto-detecting build method...${NC}"
    echo ""
    
    local has_binaries=false
    local has_image=false
    
    if check_binaries; then
        echo -e "${GREEN}✓ DCGM binaries found${NC}"
        has_binaries=true
    else
        echo -e "${YELLOW}✗ DCGM binaries not found${NC}"
    fi
    
    if check_base_image; then
        echo -e "${GREEN}✓ Base image found${NC}"
        has_image=true
    else
        echo -e "${YELLOW}✗ Base image not found${NC}"
    fi
    
    echo ""
    
    if [ "$has_binaries" = true ]; then
        echo -e "${GREEN}→ Using: Build from binaries${NC}"
        return 1  # binaries
    elif [ "$has_image" = true ]; then
        echo -e "${GREEN}→ Using: Build from existing image${NC}"
        return 2  # image
    else
        echo -e "${RED}✗ Cannot build: No binaries or base image found${NC}"
        echo ""
        echo "Please either:"
        echo "  1. Set DCGM_DIR to your DCGM binaries location"
        echo "  2. Pull/build a base image first"
        echo ""
        return 0  # error
    fi
}

# Build from binaries
build_from_binaries() {
    local dcgm_dir="${DCGM_DIR:-$HOME/Workspace/DCGM/_out/Linux-amd64-debug}"
    
    echo ""
    echo "Building from DCGM binaries..."
    echo "DCGM Directory: $dcgm_dir"
    echo ""
    
    # Create symlinks in current directory
    ln -sf "$dcgm_dir/bin" ./bin 2>/dev/null || true
    ln -sf "$dcgm_dir/lib" ./lib 2>/dev/null || true
    ln -sf "$dcgm_dir/share" ./share 2>/dev/null || true
    
    docker build \
        -f Dockerfile.from-binaries \
        -t "${FULL_IMAGE}" \
        --platform linux/amd64 \
        .
    
    # Clean up symlinks
    rm -f ./bin ./lib ./share
    
    echo ""
    echo -e "${GREEN}✓ Build complete!${NC}"
    echo "  Image: ${FULL_IMAGE}"
}

# Build from existing image
build_from_image() {
    echo ""
    echo "Building from existing image..."
    
    # Find the base image
    local base_image=""
    if docker image inspect "${IMAGE_NAME}:latest" &> /dev/null; then
        base_image="${IMAGE_NAME}:latest"
    elif docker image inspect "${IMAGE_NAME}:base" &> /dev/null; then
        base_image="${IMAGE_NAME}:base"
    elif docker image inspect "${IMAGE_NAME}:v1" &> /dev/null; then
        base_image="${IMAGE_NAME}:v1"
    else
        echo -e "${RED}✗ No base image found${NC}"
        exit 1
    fi
    
    echo "Base Image: $base_image"
    echo ""
    
    docker build \
        -f Dockerfile.from-image \
        -t "${FULL_IMAGE}" \
        --build-arg BASE_IMAGE="$base_image" \
        --platform linux/amd64 \
        .
    
    echo ""
    echo -e "${GREEN}✓ Build complete!${NC}"
    echo "  Image: ${FULL_IMAGE}"
    echo "  Base: $base_image"
}

# Parse command line arguments
MODE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --from-binaries)
            MODE="binaries"
            shift
            ;;
        --from-image)
            MODE="image"
            shift
            ;;
        --auto)
            MODE="auto"
            shift
            ;;
        -t|--tag)
            TAG="$2"
            FULL_IMAGE="${IMAGE_NAME}:${TAG}"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --from-binaries     Build from DCGM binaries (requires binaries)"
            echo "  --from-image        Build from existing Docker image"
            echo "  --auto              Auto-detect best method (default)"
            echo "  -t, --tag TAG       Tag for the new image (default: latest)"
            echo "  -h, --help          Show this help"
            echo ""
            echo "Environment Variables:"
            echo "  DCGM_DIR            Path to DCGM binaries (default: ~/Workspace/DCGM/_out/Linux-amd64-debug)"
            echo ""
            echo "Examples:"
            echo "  $0                           # Auto-detect"
            echo "  $0 --from-binaries           # Build from binaries"
            echo "  $0 --from-image              # Build from existing image"
            echo "  $0 --from-image -t v2.0      # Build from image with custom tag"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Default to auto-detect
if [ -z "$MODE" ]; then
    MODE="auto"
fi

# Execute based on mode
case $MODE in
    auto)
        auto_detect
        result=$?
        if [ $result -eq 1 ]; then
            build_from_binaries
        elif [ $result -eq 2 ]; then
            build_from_image
        else
            exit 1
        fi
        ;;
    binaries)
        if ! check_binaries; then
            echo -e "${RED}✗ DCGM binaries not found${NC}"
            echo "Set DCGM_DIR or use --from-image"
            exit 1
        fi
        build_from_binaries
        ;;
    image)
        if ! check_base_image; then
            echo -e "${RED}✗ No base image found${NC}"
            echo "Build from binaries first or pull a base image"
            exit 1
        fi
        build_from_image
        ;;
esac

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "Run the container:"
echo "  docker run -d -p 9400:9400 ${FULL_IMAGE}"
echo ""
echo "Test different profiles:"
echo "  docker run -d -p 9400:9400 -e METRIC_PROFILE=spike ${FULL_IMAGE}"
echo "  docker run -d -p 9400:9400 -e NUM_FAKE_GPUS=8 ${FULL_IMAGE}"
echo ""
echo "Run tests:"
echo "  ./test-features.sh"
echo ""
