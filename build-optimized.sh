#!/bin/bash
# Optimized build script - only copies essential files

set -ex

cd "$(dirname "$0")"

echo "=========================================="
echo "DCGM Fake GPU Exporter - Optimized Build"
echo "=========================================="
echo ""

echo "Extracting DCGM binaries..."
tar -xzf DCGM_subset.tar.gz

echo "Preparing optimized build context..."
rm -rf dcgm_optimized
mkdir -p dcgm_optimized/bin
mkdir -p dcgm_optimized/lib
mkdir -p dcgm_optimized/share/dcgm_tests

echo "Copying only essential binaries..."
# Only nv-hostengine is needed for the manager
cp DCGM/_out/Linux-amd64-debug/bin/nv-hostengine dcgm_optimized/bin/

echo "Copying only essential libraries..."
# Core DCGM library
cp -L DCGM/_out/Linux-amd64-debug/lib/libdcgm.so* dcgm_optimized/lib/ 2>/dev/null || true
# NVML injection library  
cp -L DCGM/_out/Linux-amd64-debug/lib/libnvml_injection.so* dcgm_optimized/lib/ 2>/dev/null || true
# NVML stub
cp -L DCGM/_out/Linux-amd64-debug/lib/libnvidia-ml.so* dcgm_optimized/lib/ 2>/dev/null || true
# Module libraries (excluding CUBLAS proxies)
cp -L DCGM/_out/Linux-amd64-debug/lib/libdcgmmodule*.so* dcgm_optimized/lib/ 2>/dev/null || true

echo "Copying Python bindings and dependencies..."
# Just copy the entire share directory - it's only ~2.5GB and ensures everything works
cp -r DCGM/_out/Linux-amd64-debug/share dcgm_optimized/

echo ""
echo "Size comparison:"
echo "Original DCGM:"
du -sh DCGM/_out/Linux-amd64-debug/
echo "Optimized copy:"
du -sh dcgm_optimized/
echo ""

echo "Building Docker image..."
docker build -f Dockerfile.from-binaries-optimized -t dcgm-fake-gpu-exporter:latest --platform linux/amd64 .

echo ""
echo "Cleaning up..."
rm -rf dcgm_optimized
rm -rf DCGM

echo ""
echo "=========================================="
echo "Build complete!"
echo "=========================================="
echo ""
docker images | grep dcgm-fake-gpu-exporter
