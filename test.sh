#!/bin/bash
# Test script for DCGM Fake GPU Exporter

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED_TESTS=0
PASSED_TESTS=0

log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED_TESTS++))
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED_TESTS++))
}

log_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

echo "=========================================="
echo "DCGM Fake GPU Exporter - Test Suite"
echo "=========================================="
echo ""

# Test 1: Container is running
log_info "Test 1: Checking if container is running..."
if docker ps | grep -q dcgm-exporter; then
    log_pass "Container is running"
else
    log_fail "Container is not running"
    exit 1
fi

# Test 2: Health endpoint
log_info "Test 2: Checking health endpoint..."
if curl -sf http://localhost:9400/health > /dev/null 2>&1; then
    log_pass "Health endpoint responds"
else
    log_fail "Health endpoint does not respond"
fi

# Test 3: Metrics endpoint
log_info "Test 3: Checking metrics endpoint..."
if curl -sf http://localhost:9400/metrics > /dev/null 2>&1; then
    log_pass "Metrics endpoint responds"
else
    log_fail "Metrics endpoint does not respond"
fi

# Test 4: Metrics contain GPU temperature
log_info "Test 4: Checking for GPU temperature metrics..."
if curl -s http://localhost:9400/metrics | grep -q "dcgm_gpu_temp"; then
    log_pass "GPU temperature metrics found"
else
    log_fail "GPU temperature metrics not found"
fi

# Test 5: Metrics contain GPU utilization
log_info "Test 5: Checking for GPU utilization metrics..."
if curl -s http://localhost:9400/metrics | grep -q "dcgm_gpu_utilization"; then
    log_pass "GPU utilization metrics found"
else
    log_fail "GPU utilization metrics not found"
fi

# Test 6: Metrics contain power usage
log_info "Test 6: Checking for power usage metrics..."
if curl -s http://localhost:9400/metrics | grep -q "dcgm_power_usage"; then
    log_pass "Power usage metrics found"
else
    log_fail "Power usage metrics not found"
fi

# Test 7: Multiple GPUs present
log_info "Test 7: Checking for multiple GPUs..."
gpu_count=$(curl -s http://localhost:9400/metrics | grep 'dcgm_gpu_temp{gpu="[^0]' | wc -l)
if [ "$gpu_count" -ge 2 ]; then
    log_pass "Multiple GPUs found ($gpu_count GPUs)"
else
    log_fail "Not enough GPUs found (expected 2+, got $gpu_count)"
fi

# Test 8: GPU 0 is excluded
log_info "Test 8: Checking that GPU 0 is present..."
if curl -s http://localhost:9400/metrics | grep -q 'dcgm_gpu_temp{gpu="0"'; then
    log_pass "GPU 0 present (expected for NVML injection)"
else
    log_fail "GPU 0 not found"
fi

# Test 9: Metric values are numeric
log_info "Test 9: Checking metric values are numeric..."
temp_value=$(curl -s http://localhost:9400/metrics | grep 'dcgm_gpu_temp{gpu="1"' | head -1 | awk '{print $2}')
if [[ "$temp_value" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
    log_pass "Metric values are numeric (temperature: $temp_value°C)"
else
    log_fail "Metric values are not numeric"
fi

# Test 10: Container logs have no errors
log_info "Test 10: Checking container logs for errors..."
error_count=$(docker logs dcgm-exporter 2>&1 | grep -ci error || true)
if [ "$error_count" -lt 3 ]; then
    log_pass "No critical errors in logs ($error_count errors found)"
else
    log_fail "Too many errors in logs ($error_count errors)"
fi

# Test 11: nv-hostengine is running in container
log_info "Test 11: Checking if nv-hostengine is running..."
if docker exec dcgm-exporter pgrep nv-hostengine > /dev/null 2>&1; then
    log_pass "nv-hostengine process is running"
else
    log_fail "nv-hostengine process is not running"
fi

# Test 12: Python exporter is running
log_info "Test 12: Checking if Python exporter is running..."
if docker exec dcgm-exporter pgrep -f dcgm_exporter.py > /dev/null 2>&1; then
    log_pass "Python exporter is running"
else
    log_fail "Python exporter is not running"
fi

# Test 13: Port 5555 is listening
log_info "Test 13: Checking if port 5555 is listening..."
if docker exec dcgm-exporter netstat -tln 2>/dev/null | grep -q ":5555" || \
   docker exec dcgm-exporter ss -tln 2>/dev/null | grep -q ":5555"; then
    log_pass "Port 5555 (DCGM) is listening"
else
    log_fail "Port 5555 (DCGM) is not listening"
fi

# Test 14: Prometheus can scrape metrics
log_info "Test 14: Testing Prometheus format..."
if curl -s http://localhost:9400/metrics | head -20 | grep -q "# TYPE"; then
    log_pass "Prometheus format is correct"
else
    log_fail "Prometheus format is incorrect"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    echo ""
    echo "Debugging information:"
    echo "Container status:"
    docker ps | grep dcgm-exporter
    echo ""
    echo "Recent logs:"
    docker logs --tail 20 dcgm-exporter
    exit 1
fi
