# DCGM Fake GPU Exporter

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Container Registry](https://img.shields.io/badge/ghcr.io-images-blue)](https://github.com/saiakhil2012/dcgm-fake-gpu-exporter/pkgs/container/dcgm-fake-gpu-exporter)

A powerful Prometheus exporter that simulates realistic NVIDIA GPU behavior using DCGM's injection framework. Test GPU monitoring, dashboards, and alerting systems **without expensive hardware** - from single GPUs to entire data center clusters.

## 🎯 Why This Tool?

- **💰 Save Costs**: No need for expensive GPU instances during development
- **🧪 Test at Scale**: Simulate 1 to 1000+ GPUs instantly
- **🎭 Realistic Scenarios**: 7 behavior profiles from stable workloads to chaos engineering
- **⚡ Quick Setup**: One command to get running - no 10+ hour DCGM builds
- **🔄 Production-Ready**: Compatible with real DCGM metrics for seamless migration

> **Perfect for**: Dashboard development, alerting system testing, chaos engineering, CI/CD pipelines, training, and demos

## ✨ Features

- 🎯 **No GPU Required** - Runs on any x86-64 Linux system (including VMs and ARM machines via Rosetta/QEMU)
- 📊 **Full DCGM Metrics** - Temperature, power, utilization, memory, clocks, PCIe, NVLink, encoder/decoder
- 🐳 **Docker-based** - One command to run
- 📈 **Prometheus Compatible** - Standard metrics format
- 🔧 **Configurable** - Customize number of GPUs and their behavior
- 🔄 **Dynamic Metrics** - Realistic varying values that update automatically
- 🎭 **Metric Profiles** - Simulate different GPU behaviors (stable, spike, degrading, faulty, chaos, wave)
- 📐 **Scalable** - Test with 1 to 1000+ GPUs
- 🎛️ **Per-GPU Control** - Different behavior profiles for each GPU

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- x86-64 Linux host (or ARM Mac with Rosetta 2)
- **Pre-built DCGM binaries** (see [Building DCGM Binaries](#building-dcgm-binaries-optional))

### Option 1: Using Pre-built Docker Image (Recommended)

Pull the pre-built image from GitHub Container Registry:

```bash
docker run -d \
  --name dcgm-exporter \
  -p 9400:9400 \
  -p 5555:5555 \
  -e NUM_FAKE_GPUS=4 \
  ghcr.io/saiakhil2012/dcgm-fake-gpu-exporter:latest

# View metrics
curl http://localhost:9400/metrics
```

### Option 2: Building from Source

**Two build methods available:**

#### Method A: From Existing Image (Recommended for Dev Machines)
If you have a previous version of the image but not the DCGM binaries:

```bash
# Clone the repository
git clone https://github.com/saiakhil2012/dcgm-fake-gpu-exporter.git
cd dcgm-fake-gpu-exporter

# Smart build (auto-detects best method)
./build-smart.sh

# Or explicitly from existing image
./build-smart.sh --from-image

# Run
docker run -d -p 9400:9400 dcgm-fake-gpu-exporter:latest
```

**Benefits:**
- ✅ No DCGM binaries needed
- ✅ Fast build (10-30 seconds)
- ✅ Perfect for updating code on new machines
- ✅ Ideal for development iterations

#### Method B: From DCGM Binaries (Initial Setup)
If you have DCGM binaries or building for the first time:

```bash
# Clone the repository
git clone https://github.com/saiakhil2012/dcgm-fake-gpu-exporter.git
cd dcgm-fake-gpu-exporter

# You need DCGM binaries - see "Building DCGM Binaries" section below
# Place your DCGM build at: ~/Workspace/DCGM/_out/Linux-amd64-debug/

# Build and run
./build-smart.sh --from-binaries
# Or use legacy script
./build.sh

# Or use Docker Compose
docker-compose up -d

# View metrics
curl http://localhost:9400/metrics
```

**Benefits:**
- ✅ Complete build from scratch
- ✅ Reproducible builds
- ✅ Creates base image for other machines
- ✅ Suitable for CI/CD pipelines

📚 **[See detailed build methods guide](docs/BUILD_METHODS.md)** for choosing the right method.

## 📊 Available Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `dcgm_gpu_temp` | GPU temperature | Celsius |
| `dcgm_power_usage` | Power consumption | Watts |
| `dcgm_gpu_utilization` | GPU utilization | percentage |
| `dcgm_mem_copy_utilization` | Memory utilization | percentage |
| `dcgm_sm_clock` | SM clock speed | MHz |
| `dcgm_mem_clock` | Memory clock speed | MHz |
| `dcgm_fb_total` | Total framebuffer | MB |
| `dcgm_fb_used` | Used framebuffer | MB |
| `dcgm_fb_free` | Free framebuffer | MB |

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NUM_FAKE_GPUS` | `4` | Number of fake GPUs to create (1-1000+) |
| `METRIC_PROFILE` | `static` | Metric behavior profile (see profiles below) |
| `GPU_PROFILES` | - | Comma-separated profiles per GPU (overrides METRIC_PROFILE) |
| `METRIC_UPDATE_INTERVAL` | `30` | Seconds between metric updates |
| `GPU_START_INDEX` | `1` | Starting GPU index (for cluster simulation) |
| `EXPORTER_PORT` | `9400` | Prometheus metrics port |
| `DCGM_DIR` | `/root/Workspace/DCGM/_out/Linux-amd64-debug` | Path to DCGM binaries in container |

### Metric Profiles

Simulate different GPU behaviors for testing dashboards and alerting:

| Profile | Description | Use Case |
|---------|-------------|----------|
| `static` | Fixed random values (backward compatible) | Existing setups, predictable metrics |
| `stable` | Minimal variation, steady state | Production-like steady workloads |
| `spike` | Random sudden spikes (20% chance) | Testing spike detection, auto-scaling |
| `wave` | Sine wave patterns | Batch jobs, cyclical workloads |
| `degrading` | Gradual performance decline | Hardware aging, thermal throttling |
| `faulty` | Intermittent failures (10% chance) | Fault detection, alerting systems |
| `chaos` | Completely random values | Stress testing, chaos engineering |

📚 **[See full profile documentation](docs/PROFILES.md)** for detailed behavior, use cases, and examples.

### Example Configurations

**8 GPUs with spike profile:**
```bash
docker run -d -p 9400:9400 \
  -e NUM_FAKE_GPUS=8 \
  -e METRIC_PROFILE=spike \
  dcgm-fake-gpu-exporter
```

**Per-GPU profiles (mixed behavior):**
```bash
docker run -d -p 9400:9400 \
  -e NUM_FAKE_GPUS=4 \
  -e GPU_PROFILES=stable,spike,faulty,degrading \
  dcgm-fake-gpu-exporter
```

**Large-scale testing (100 GPUs):**
```bash
docker run -d -p 9400:9400 \
  -e NUM_FAKE_GPUS=100 \
  -e METRIC_PROFILE=wave \
  dcgm-fake-gpu-exporter
```

**Fast updates for testing:**
```bash
docker run -d -p 9400:9400 \
  -e METRIC_UPDATE_INTERVAL=10 \
  -e METRIC_PROFILE=chaos \
  dcgm-fake-gpu-exporter
```

**Cluster simulation (multiple nodes):**
```bash
# Node 1: GPUs 1-8
docker run -d -p 9401:9400 \
  -e NUM_FAKE_GPUS=8 \
  -e GPU_START_INDEX=1 \
  dcgm-fake-gpu-exporter

# Node 2: GPUs 9-16
docker run -d -p 9402:9400 \
  -e NUM_FAKE_GPUS=8 \
  -e GPU_START_INDEX=9 \
  dcgm-fake-gpu-exporter
```

**Custom port:**
```bash
docker run -d -p 9401:9400 dcgm-fake-gpu-exporter
```

## 📈 Integration Examples

### Prometheus

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'dcgm'
    static_configs:
      - targets: ['localhost:9400']
    scrape_interval: 10s
```

Or use the included docker-compose with Prometheus:

```bash
docker-compose --profile with-prometheus up -d
```

Then access Prometheus at `http://localhost:9090`

### OpenTelemetry Collector

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'dcgm'
          static_configs:
            - targets: ['localhost:9400']

exporters:
  otlp:
    endpoint: your-otel-collector:4317

service:
  pipelines:
    metrics:
      receivers: [prometheus]
      exporters: [otlp]
```

### Grafana

Sample metrics queries:

```promql
# GPU Temperature
dcgm_gpu_temp{gpu!="0"}

# GPU Utilization
dcgm_gpu_utilization{gpu!="0"}

# Power Usage (convert from milliwatts to watts)
dcgm_power_usage{gpu!="0"} / 1000

# Memory Usage Percentage
(dcgm_fb_used / dcgm_fb_total) * 100
```

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   Docker Container                  │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │ nv-hostengine│  │  Exporter   │ │
│  │   (DCGM)     │←─│   (Python)  │ │
│  └──────┬───────┘  └──────┬──────┘ │
│         │                 │        │
│    Fake GPUs        HTTP :9400     │
│    (Injected)        Metrics       │
└─────────────────────────────────────┘
```

**Components:**

1. **nv-hostengine**: DCGM daemon with NVML injection enabled
2. **Fake GPUs**: Created via `dcgmCreateFakeEntities` API with injected attributes
3. **Metric Injection**: Realistic GPU metrics injected every 30 seconds
4. **Python Exporter**: Reads DCGM metrics via `dcgmi` CLI and exposes in Prometheus format

## 🔨 Building DCGM Binaries (Optional)

> ⚠️ **Warning**: Building DCGM from source takes 20-28 hours and requires significant resources.

If you want to build DCGM yourself:

```bash
# On Ubuntu 22.04 x86-64 system
git clone https://github.com/NVIDIA/DCGM.git
cd DCGM

# Build (this will take ~20 hours)
make -j$(nproc)

# The binaries will be in:
# ./_out/Linux-amd64-debug/
```

Once built, set the path:

```bash
export DCGM_DIR="$HOME/Workspace/DCGM/_out/Linux-amd64-debug"
./build.sh
```

## 🎯 Use Cases

- **Development**: Test GPU monitoring dashboards without hardware
- **CI/CD**: Validate GPU-aware applications in pipelines
- **Demos**: Show GPU metrics visualizations without real GPUs
- **Testing**: Test Prometheus/Grafana/OTEL setups for GPU monitoring
- **Training**: Learn DCGM, GPU metrics, and observability tools
- **Cost Savings**: Avoid spinning up expensive GPU instances for development
- **Alerting**: Test alert rules with different GPU behavior patterns
- **Chaos Engineering**: Simulate GPU failures and degradation
- **Load Testing**: Test monitoring systems with 100+ GPUs
- **Dashboard Development**: Build and iterate on Grafana dashboards quickly

## 🚀 Migration to Production

When you're ready to move from fake GPUs to real hardware:

### Step 1: Replace the Exporter

```yaml
# docker-compose.yml - Development (Fake GPUs)
services:
  dcgm-exporter:
    image: your-registry/dcgm-fake-gpu-exporter
    ports:
      - "9400:9400"
    environment:
      - NUM_FAKE_GPUS=4
      - METRIC_PROFILE=stable
```

```yaml
# docker-compose.yml - Production (Real GPUs)
services:
  dcgm-exporter:
    image: nvcr.io/nvidia/k8s/dcgm-exporter:latest
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    ports:
      - "9400:9400"
    cap_add:
      - SYS_ADMIN
```

### Step 2: Keep Your Monitoring Stack

✅ **No changes needed** to:
- Prometheus scrape configs
- Grafana dashboards
- Alert rules
- Metric names and labels

The metrics are compatible between fake and real exporters!

### Step 3: Update Queries (Optional)

If you filtered out GPU 0 in fake mode, you can remove that filter:

```promql
# Fake GPU queries (filter GPU 0)
dcgm_gpu_temp{gpu!="0"}

# Real GPU queries (all GPUs valid)
dcgm_gpu_temp
```

## 🐛 Troubleshooting

### Container keeps restarting

```bash
docker logs dcgm-exporter
```

Check if nv-hostengine is starting properly. Common issues:
- Missing DCGM binaries
- Incorrect file permissions
- Port 5555 already in use

### No metrics showing

```bash
# Check health endpoint
curl http://localhost:9400/health

# Exec into container
docker exec -it dcgm-exporter bash

# Check DCGM directly
/usr/local/bin/dcgm_fake_manager.py status

# View metrics manually
/root/Workspace/DCGM/_out/Linux-amd64-debug/share/dcgm_tests/apps/amd64/dcgmi dmon -e 150,155,203,204
```

### GPU 0 shows zeros

This is expected behavior. GPU 0 is an artifact of NVML injection and can be filtered out:

```promql
# In Prometheus queries
dcgm_gpu_temp{gpu!="0"}
```

### Port already in use

```bash
# Use different port
docker run -p 9401:9400 -e EXPORTER_PORT=9400 dcgm-fake-gpu-exporter
```

### Running on ARM Mac (M1/M2/M3)

The container uses x86-64 binaries. On ARM Macs, Docker will automatically use Rosetta 2 or QEMU:

```bash
# Specify platform explicitly
docker build --platform linux/amd64 -t dcgm-fake-gpu-exporter .
docker run --platform linux/amd64 -p 9400:9400 dcgm-fake-gpu-exporter
```

## 🧪 Testing

### Quick Test

```bash
# Start container
docker-compose up -d

# Wait for startup (15 seconds)
sleep 15

# Check metrics
curl -s http://localhost:9400/metrics | grep dcgm_gpu_temp

# Should see output like:
# dcgm_gpu_temp{gpu="1",device="nvidia1"} 51
# dcgm_gpu_temp{gpu="2",device="nvidia2"} 58
# dcgm_gpu_temp{gpu="3",device="nvidia3"} 65
# dcgm_gpu_temp{gpu="4",device="nvidia4"} 73
```

### Testing Different Profiles

```bash
# Test spike profile
docker run -d -p 9400:9400 -e METRIC_PROFILE=spike dcgm-fake-gpu-exporter
watch -n 5 'curl -s http://localhost:9400/metrics | grep dcgm_gpu_temp'

# Test wave profile
docker run -d -p 9400:9400 -e METRIC_PROFILE=wave dcgm-fake-gpu-exporter

# Test with 100 GPUs
docker run -d -p 9400:9400 -e NUM_FAKE_GPUS=100 -e METRIC_PROFILE=stable dcgm-fake-gpu-exporter
```

### With Prometheus

```bash
# Start with Prometheus
docker-compose --profile with-prometheus up -d

# Wait for startup
sleep 20

# Open Prometheus UI
open http://localhost:9090

# Try a query:
dcgm_gpu_temp{gpu!="0"}
```

### Testing Multiple Profiles

Use the examples docker-compose:

```bash
# Test all profiles at once
cd examples
docker-compose -f docker-compose.profiles.yml up -d

# Each profile on different port:
# Stable:  http://localhost:9400/metrics
# Spike:   http://localhost:9401/metrics (with --profile spike)
# Mixed:   http://localhost:9402/metrics (with --profile mixed)
# Scale:   http://localhost:9403/metrics (with --profile scale)
# Chaos:   http://localhost:9404/metrics (with --profile chaos)
```

## ⚠️ Limitations

- **GPU Names/UUIDs**: Show as `<<<NULL>>>` due to DCGM fake entity limitations
- **GPU 0**: Shows zeros (NVML injection artifact) - filter it out in queries
- **Platform**: Linux x86-64 only (DCGM limitation)
- **Metrics**: Simulated values, not real GPU measurements
- **Performance**: Not suitable for performance testing, only monitoring/observability testing

## 📁 Repository Structure

```
.
├── README.md                        # This file
├── LICENSE                          # MIT License
├── Dockerfile                       # Default Dockerfile (points to from-binaries)
├── Dockerfile.from-binaries         # Build from DCGM binaries (initial setup)
├── Dockerfile.from-image            # Build from existing image (dev machines)
├── docker-compose.yml               # Compose configuration
├── docker-compose-smart.yml         # Smart compose with auto-detection
├── docker-entrypoint.sh             # Container entrypoint
├── build.sh                         # Legacy build script (from binaries)
├── build-smart.sh                   # Smart build script (auto-detects method)
├── test-features.sh                 # Automated test suite
├── dcgm_fake_manager.py             # Python manager for fake GPUs (with profiles)
├── dcgm_exporter.py                 # Prometheus exporter
├── prometheus.yml                   # Sample Prometheus config
├── CHANGELOG.md                     # Version history
├── IMPLEMENTATION.md                # Implementation details
├── docs/
│   ├── PROFILES.md                  # Detailed profile documentation
│   └── BUILD_METHODS.md             # Build methods guide
└── examples/
    ├── docker-compose.profiles.yml  # Profile examples
    ├── prometheus-profiles.yml      # Multi-instance Prometheus config
    ├── docker-compose.otel.yml      # OpenTelemetry example
    ├── grafana-dashboard.json       # Sample Grafana dashboard
    └── otel-collector-config.yaml   # OTEL collector config
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

- **This project**: MIT License
- **DCGM binaries** (included in Docker image): Apache 2.0 License
  - Source: https://github.com/NVIDIA/DCGM
  - Copyright: NVIDIA CORPORATION

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built using [NVIDIA DCGM](https://github.com/NVIDIA/DCGM)'s injection framework
- Inspired by [NVIDIA DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter)
- Created to avoid the 20+ hour DCGM build process

## 📮 Support

- **Issues**: [GitHub Issues](https://github.com/saiakhil2012/dcgm-fake-gpu-exporter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/saiakhil2012/dcgm-fake-gpu-exporter/discussions)

---

**Note**: This is a development/testing tool. For production GPU monitoring with real hardware, use the official [NVIDIA DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter).

## 🗺️ Roadmap

- [x] Configurable metric patterns (stable, spike, wave, degrading, faulty, chaos)
- [x] Per-GPU profile configuration
- [x] Scalable GPU counts (1-1000+)
- [x] Environment-based configuration
- [ ] Pre-built Docker images on Docker Hub
- [ ] GitHub Actions CI/CD pipeline
- [ ] Grafana dashboard templates for each profile
- [ ] Additional metric fields (PCIe, NVLink)
- [ ] Multi-architecture support (ARM64 via cross-compilation)
- [ ] Helm chart for Kubernetes deployment
- [ ] JSON policy files for complex scenarios
- [ ] Time-based profile switching (simulate day/night cycles)
