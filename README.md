# DCGM Fake GPU Exporter

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight Prometheus exporter that simulates NVIDIA GPUs using DCGM's injection framework. Perfect for testing, development, and demos **without requiring real GPU hardware**.

> ⚠️ **Important**: This tool uses pre-built DCGM binaries. Building DCGM from source takes 10+ hours. This repository saves you that time by providing a ready-to-use Docker setup.

## ✨ Features

- 🎯 **No GPU Required** - Runs on any x86-64 Linux system (including VMs and ARM machines via Rosetta/QEMU)
- 📊 **Full DCGM Metrics** - Temperature, power, utilization, memory, clocks, PCIe, NVLink, encoder/decoder
- 🐳 **Docker-based** - One command to run
- 📈 **Prometheus Compatible** - Standard metrics format
- 🔧 **Configurable** - Customize number of GPUs and their behavior
- 🔄 **Dynamic Metrics** - Realistic varying values that update automatically

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- x86-64 Linux host (or ARM Mac with Rosetta 2)
- **Pre-built DCGM binaries** (see [Building DCGM Binaries](#building-dcgm-binaries-optional))

### Option 1: Using Pre-built Docker Image (Recommended)

If someone has published the pre-built image:

```bash
docker run -d \
  --name dcgm-exporter \
  -p 9400:9400 \
  -p 5555:5555 \
  -e NUM_FAKE_GPUS=4 \
  <username>/dcgm-fake-gpu-exporter:latest

# View metrics
curl http://localhost:9400/metrics
```

### Option 2: Building from Source

```bash
# Clone the repository
git clone https://github.com/<username>/dcgm-fake-gpu-exporter.git
cd dcgm-fake-gpu-exporter

# You need DCGM binaries - see "Building DCGM Binaries" section below
# Place your DCGM build at: ~/Workspace/DCGM/_out/Linux-amd64-debug/

# Build and run
./build.sh

# Or use Docker Compose
docker-compose up -d

# View metrics
curl http://localhost:9400/metrics
```

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
| `NUM_FAKE_GPUS` | `4` | Number of fake GPUs to create |
| `EXPORTER_PORT` | `9400` | Prometheus metrics port |
| `DCGM_DIR` | `/root/Workspace/DCGM/_out/Linux-amd64-debug` | Path to DCGM binaries in container |

### Example Configurations

**8 GPUs:**
```bash
docker run -d -p 9400:9400 -e NUM_FAKE_GPUS=8 dcgm-fake-gpu-exporter
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

## ⚠️ Limitations

- **GPU Names/UUIDs**: Show as `<<<NULL>>>` due to DCGM fake entity limitations
- **GPU 0**: Shows zeros (NVML injection artifact) - filter it out in queries
- **Platform**: Linux x86-64 only (DCGM limitation)
- **Metrics**: Simulated values, not real GPU measurements
- **Performance**: Not suitable for performance testing, only monitoring/observability testing

## 📁 Repository Structure

```
.
├── README.md                   # This file
├── LICENSE                     # MIT License
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Compose configuration
├── docker-entrypoint.sh        # Container entrypoint
├── build.sh                    # Build script
├── dcgm_fake_manager.py        # Python manager for fake GPUs
├── dcgm_exporter.py           # Prometheus exporter
├── prometheus.yml              # Sample Prometheus config
└── examples/
    └── grafana-dashboard.json  # Sample Grafana dashboard
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

- **Issues**: [GitHub Issues](https://github.com/<username>/dcgm-fake-gpu-exporter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/<username>/dcgm-fake-gpu-exporter/discussions)

---

**Note**: This is a development/testing tool. For production GPU monitoring with real hardware, use the official [NVIDIA DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter).

## 🗺️ Roadmap

- [ ] Pre-built Docker images on Docker Hub
- [ ] GitHub Actions CI/CD pipeline
- [ ] Grafana dashboard templates
- [ ] Additional metric fields (PCIe, NVLink)
- [ ] Configurable metric patterns (sine waves, random, static)
- [ ] Multi-architecture support (ARM64 via cross-compilation)
- [ ] Helm chart for Kubernetes deployment
