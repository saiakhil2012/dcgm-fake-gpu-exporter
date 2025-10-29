#!/bin/bash
# Manual build script that extracts and builds in one go

set -ex

cd "$(dirname "$0")"

echo "Extracting DCGM binaries..."
tar -xzf DCGM_subset.tar.gz

echo "Verifying extraction..."
ls -la DCGM/_out/Linux-amd64-debug/

echo "Preparing build context..."
rm -rf dcgm_build
mkdir -p dcgm_build

echo "Copying DCGM files..."
DCGM_SRC="$(pwd)/DCGM/_out/Linux-amd64-debug"
echo "Source: $DCGM_SRC"
echo "Testing if bin exists:"
test -d "$DCGM_SRC/bin" && echo "YES - bin exists" || echo "NO - bin does not exist"
ls -la "$DCGM_SRC/bin"
echo "Now attempting copy..."
cp -v -r "$DCGM_SRC/bin" dcgm_build/
cp -v -r "$DCGM_SRC/lib" dcgm_build/
cp -v -r "$DCGM_SRC/share" dcgm_build/

echo "Renaming dcgm_build to dcgm..."
rm -rf dcgm
mv dcgm_build dcgm

echo "Listing dcgm contents..."
ls -la dcgm/

echo "Building Docker image..."
docker build -t dcgm-fake-gpu-exporter:latest --platform linux/amd64 .

echo "Cleaning up..."
rm -rf dcgm

echo "Build complete!"
docker images | grep dcgm-fake-gpu-exporter
