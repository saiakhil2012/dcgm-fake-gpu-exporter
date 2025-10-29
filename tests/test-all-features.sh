#!/bin/bash
# Comprehensive test script for dcgm-fake-gpu-exporter
# Tests all 7 metric profiles and various configurations

set -e

IMAGE_NAME="dcgm-fake-gpu-exporter:latest"
PORT=9400
BASE_URL="http://localhost:${PORT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Testing dcgm-fake-gpu-exporter Image ===${NC}\n"

# Check if image exists
if ! docker images | grep -q "dcgm-fake-gpu-exporter"; then
    echo -e "${RED}Error: dcgm-fake-gpu-exporter image not found!${NC}"
    echo "Please build the image first with: ./build-optimized.sh"
    exit 1
fi

# Function to wait for container to be ready
wait_for_ready() {
    local container_name=$1
    local max_attempts=30
    local attempt=0
    
    echo -n "Waiting for container to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "${BASE_URL}/metrics" > /dev/null 2>&1; then
            echo -e " ${GREEN}Ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo -e " ${RED}Failed!${NC}"
    return 1
}

# Function to test metrics endpoint
test_metrics() {
    local profile=$1
    local description=$2
    
    echo -e "\n${YELLOW}Testing Profile: ${profile}${NC} - ${description}"
    
    # Get metrics
    local metrics=$(curl -s "${BASE_URL}/metrics")
    
    if [ -z "$metrics" ]; then
        echo -e "${RED}  ✗ No metrics returned${NC}"
        return 1
    fi
    
    # Check for key metrics
    local checks=(
        "DCGM_FI_DEV_GPU_TEMP"
        "DCGM_FI_DEV_POWER_USAGE"
        "DCGM_FI_DEV_GPU_UTIL"
        "DCGM_FI_DEV_MEM_COPY_UTIL"
        "DCGM_FI_DEV_FB_FREE"
        "DCGM_FI_DEV_FB_USED"
    )
    
    local all_passed=true
    for metric in "${checks[@]}"; do
        if echo "$metrics" | grep -q "$metric"; then
            echo -e "  ${GREEN}✓${NC} $metric found"
        else
            echo -e "  ${RED}✗${NC} $metric missing"
            all_passed=false
        fi
    done
    
    # Show sample values
    echo -e "\n  ${YELLOW}Sample values:${NC}"
    echo "$metrics" | grep "DCGM_FI_DEV_GPU_TEMP" | head -3 | sed 's/^/    /'
    echo "$metrics" | grep "DCGM_FI_DEV_POWER_USAGE" | head -3 | sed 's/^/    /'
    
    if [ "$all_passed" = true ]; then
        echo -e "  ${GREEN}✓ All key metrics present${NC}"
        return 0
    else
        echo -e "  ${RED}✗ Some metrics missing${NC}"
        return 1
    fi
}

# Function to run a test scenario
run_test() {
    local test_name=$1
    local profile=$2
    local num_gpus=$3
    local description=$4
    local gpu_profiles=$5
    
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Test: ${test_name}${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Stop any existing container
    docker stop test-exporter 2>/dev/null || true
    docker rm test-exporter 2>/dev/null || true
    
    # Build docker run command
    local docker_cmd="docker run -d --name test-exporter -p ${PORT}:9400"
    
    if [ -n "$profile" ]; then
        docker_cmd="$docker_cmd -e METRIC_PROFILE=${profile}"
    fi
    
    if [ -n "$num_gpus" ]; then
        docker_cmd="$docker_cmd -e NUM_GPUS=${num_gpus}"
    fi
    
    if [ -n "$gpu_profiles" ]; then
        docker_cmd="$docker_cmd -e GPU_PROFILES=${gpu_profiles}"
    fi
    
    docker_cmd="$docker_cmd ${IMAGE_NAME}"
    
    echo "Running: $docker_cmd"
    eval $docker_cmd
    
    # Wait for container to be ready
    if ! wait_for_ready "test-exporter"; then
        echo -e "${RED}Container failed to start properly${NC}"
        echo "Container logs:"
        docker logs test-exporter
        docker stop test-exporter 2>/dev/null || true
        docker rm test-exporter 2>/dev/null || true
        return 1
    fi
    
    # Show container info
    echo -e "\nContainer status:"
    docker ps | grep test-exporter | sed 's/^/  /'
    
    # Test metrics
    test_metrics "$profile" "$description"
    local result=$?
    
    # Show logs snippet
    echo -e "\n${YELLOW}Container logs (last 10 lines):${NC}"
    docker logs test-exporter 2>&1 | tail -10 | sed 's/^/  /'
    
    # Cleanup
    docker stop test-exporter
    docker rm test-exporter
    
    return $result
}

# Test 1: Static Profile (default)
run_test "Default Static Profile" "static" "4" "Fixed random values that don't change"

# Test 2: Stable Profile
run_test "Stable Profile" "stable" "2" "Realistic values with small variations"

# Test 3: Spike Profile
run_test "Spike Profile" "spike" "2" "Occasional random spikes in metrics"

# Test 4: Wave Profile
run_test "Wave Profile" "wave" "2" "Sinusoidal wave patterns"

# Test 5: Degrading Profile
run_test "Degrading Profile" "degrading" "2" "Performance gradually degrades"

# Test 6: Faulty Profile
run_test "Faulty Profile" "faulty" "2" "Simulates hardware issues"

# Test 7: Chaos Profile
run_test "Chaos Profile" "chaos" "2" "Completely random values"

# Test 8: Large Scale (100 GPUs)
run_test "Large Scale - 100 GPUs" "stable" "100" "Testing scalability"

# Test 9: Mixed Profiles (per-GPU)
run_test "Mixed Profiles per GPU" "" "4" "Different profile for each GPU" "static,spike,wave,chaos"

# Test 10: Default settings (no env vars)
run_test "Default Settings" "" "" "No environment variables set"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}All tests completed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Show image info
echo -e "${YELLOW}Image Information:${NC}"
docker images | grep "dcgm-fake-gpu-exporter" | sed 's/^/  /'

echo -e "\n${GREEN}✓ Testing complete!${NC}\n"
