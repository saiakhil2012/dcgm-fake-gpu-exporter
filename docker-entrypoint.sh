#!/bin/bash
set -e

echo "=========================================="
echo "DCGM OTel Exporter Container"
echo "=========================================="

# Start nv-hostengine
echo "Starting nv-hostengine..."
/usr/local/dcgm/bin/nv-hostengine -n &
HOSTENGINE_PID=$!
echo "✓ nv-hostengine (PID: $HOSTENGINE_PID)"
sleep 5

# Create fake GPUs using dcgm_fake_manager.py
echo ""
echo "Creating fake GPUs..."
python3 /root/Workspace/DCGM/_out/Linux-amd64-debug/dcgm_fake_manager.py start

if [ $? -ne 0 ]; then
    echo "✗ Failed to create GPUs"
    exit 1
fi

echo ""
echo "Waiting for metrics to be fully available..."
sleep 5

echo ""
echo "=========================================="
echo "Starting Exporter"
echo "=========================================="
exec /root/Workspace/DCGM/_out/Linux-amd64-debug/dcgm_exporter.py
