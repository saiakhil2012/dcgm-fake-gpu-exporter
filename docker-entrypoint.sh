#!/bin/bash
set -e

echo "=========================================="
echo "DCGM OTel Exporter Container"
echo "=========================================="
echo ""

# Create fake GPUs using dcgm_fake_manager.py
# This will start nv-hostengine and create the fake GPUs
echo "Initializing DCGM with fake GPUs..."
python3 /root/Workspace/DCGM/_out/Linux-amd64-debug/dcgm_fake_manager.py start

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Failed to initialize DCGM fake GPUs"
    echo "Check logs above for details"
    exit 1
fi

echo ""
echo "✓ DCGM fake GPUs created successfully"
echo ""
echo "Waiting for metrics to be fully available..."
sleep 5

echo ""
echo "=========================================="
echo "Starting Exporter"
echo "=========================================="
exec /root/Workspace/DCGM/_out/Linux-amd64-debug/dcgm_exporter.py
