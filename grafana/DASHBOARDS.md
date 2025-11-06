# Grafana Dashboards

This directory contains pre-built Grafana dashboards for the DCGM Fake GPU Exporter.

## Available Dashboards

### 1. DCGM GPU Overview (`dcgm-gpu-overview.json`)
**Single GPU monitoring dashboard**

Basic dashboard for monitoring a single GPU or general GPU metrics.

**Panels:**
- GPU Temperature (time series)
- GPU Utilization (time series)
- Power Usage (gauge)
- Memory Usage (gauge)
- Clock Speeds (time series)

**Use Case:**
- Production monitoring of real GPUs
- Simple metric visualization
- Basic alerting setup

---

### 2. DCGM Multi-Profile Demo ⭐ (`dcgm-multi-profile-demo.json`)
**Comprehensive 4-GPU showcase with different profiles**

**Default dashboard** for `docker-compose-demo.yml` - showcases all capabilities of the fake GPU exporter.

**Panels:**

#### Top Row - Main Comparison
- **🌡️ GPU Temperature Across All Profiles** (24-wide timeseries)
  - Shows all 4 GPUs: wave (blue), spike (red), stable (green), degrading (orange)
  - Color-coded by profile for easy identification
  - Displays last, max, min, mean values in legend table
  - Thresholds: Yellow at 75°C, Red at 85°C

#### Middle Row - Detailed Analysis
- **🔥 GPU Utilization Heatmap** (12-wide heatmap)
  - Visualizes utilization patterns across all GPUs
  - Spectral color scheme (dark-orange gradient)
  - Shows temporal patterns and anomalies
  - Great for identifying spike vs wave behavior

- **⚡ Power Usage Trends** (12-wide timeseries)
  - Power consumption for all 4 GPUs (Watts)
  - Range: 0-350W with thresholds
  - Shows power efficiency differences between profiles
  - Legend displays last, max, mean values

#### Gauge Row - Quick Status
- **GPU 1 Temp (wave)** - 0-100°C gauge with color thresholds
- **GPU 2 Temp (spike)** - 0-100°C gauge with color thresholds
- **GPU 3 Temp (stable)** - 0-100°C gauge with color thresholds
- **GPU 4 Temp (degrading)** - 0-100°C gauge with color thresholds

#### Bottom Row - Advanced Metrics
- **💾 GPU Memory Usage** (12-wide timeseries)
  - Framebuffer memory used for all GPUs
  - Shows memory allocation patterns
  - Legend: last, max values

- **📊 GPU Utilization Comparison** (12-wide timeseries)
  - Side-by-side utilization % for all profiles
  - Range: 0-100% with smooth interpolation
  - Perfect for comparing profile behaviors
  - Legend: last, max, mean values

#### Summary Row
- **📈 Profile Distribution** (8-wide pie chart)
  - Visual breakdown of 4 profiles
  - Shows count and percentage
  - Quick overview of GPU allocation

- **📊 Fleet-Wide Averages** (16-wide stats)
  - Average Temperature (°C) - with color thresholds
  - Average Power (W)
  - Average Utilization (%)
  - Updated in real-time

**Features:**
- 🔄 Auto-refresh every 5 seconds
- 📅 Default time range: Last 15 minutes
- 🎨 Dark theme optimized
- 🏷️ Tagged: dcgm, gpu, multi-profile, demo
- 📊 11 total panels with rich visualizations

**Profile Details:**
1. **Wave** (GPU 1) - Sinusoidal pattern, moderate temps (60-75°C)
2. **Spike** (GPU 2) - Random spikes, high temps (70-90°C)
3. **Stable** (GPU 3) - Consistent performance, low temps (50-60°C)
4. **Degrading** (GPU 4) - Declining performance, variable temps (65-80°C)

**Use Case:**
- **Demos and presentations** - Shows all exporter capabilities
- **Profile testing** - Compare behavior of different metric profiles
- **Educational** - Learn GPU monitoring patterns
- **Development** - Test dashboard designs and queries
- **Marketing** - Showcase the "Swiss Army Knife" nature of the exporter

---

## Accessing Dashboards

### Via Docker Compose Demo

```bash
cd deployments
docker-compose -f docker-compose-demo.yml up -d

# Wait for services to start
sleep 30

# Open Grafana
open http://localhost:3000
# Login: admin / admin
```

The **DCGM Multi-Profile Demo** dashboard will auto-load as the default home dashboard.

### Switching Dashboards

In Grafana UI:
1. Click the **Dashboards** icon (left sidebar)
2. Select from available dashboards:
   - DCGM Multi-Profile Demo ⭐ (default)
   - DCGM GPU Overview

Or use the dashboard switcher dropdown in the top bar.

---

## Dashboard Configuration

### Auto-Provisioning

Dashboards are automatically provisioned via:
```yaml
# grafana/provisioning/dashboards/dashboard-provider.yml
apiVersion: 1
providers:
  - name: 'DCGM Dashboards'
    folder: ''
    type: file
    path: /etc/grafana/provisioning/dashboards
```

### Setting Default Dashboard

Edit `docker-compose-demo.yml`:
```yaml
environment:
  - GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/etc/grafana/provisioning/dashboards/dcgm-multi-profile-demo.json
```

Change filename to switch default dashboard:
- `dcgm-multi-profile-demo.json` - Multi-profile showcase (current default)
- `dcgm-gpu-overview.json` - Basic single-GPU monitoring

---

## Customizing Dashboards

### Via Grafana UI

1. Open dashboard in Grafana
2. Click ⚙️ (gear icon) → Settings
3. Make changes to panels, queries, thresholds
4. Click **Save dashboard**
5. Export JSON: Settings → JSON Model → Copy to clipboard

### Via JSON Files

Direct editing of JSON files in `grafana/provisioning/dashboards/`:

```bash
# Edit dashboard
vim grafana/provisioning/dashboards/dcgm-multi-profile-demo.json

# Restart Grafana to reload
docker-compose -f deployments/docker-compose-demo.yml restart grafana

# Wait 10 seconds for reload
sleep 10
```

**Tips:**
- Use Grafana UI to build panels, then export JSON
- Keep `"id": null` for provisioned dashboards
- Set `"uid"` for stable dashboard URLs
- Use `updateIntervalSeconds: 10` for quick reloads during development

---

## Creating New Dashboards

### Method 1: Grafana UI + Export

1. Create new dashboard in Grafana UI
2. Add panels with PromQL queries
3. Configure visualizations and thresholds
4. Settings → JSON Model → Copy
5. Save to `grafana/provisioning/dashboards/my-dashboard.json`
6. Restart Grafana

### Method 2: Copy and Modify

```bash
cd grafana/provisioning/dashboards

# Copy existing dashboard
cp dcgm-multi-profile-demo.json my-custom-dashboard.json

# Edit JSON
vim my-custom-dashboard.json

# Change these fields:
# - "title": "My Custom Dashboard"
# - "uid": "my-custom-uid"
# - Modify panels as needed

# Restart to load
docker-compose -f ../../deployments/docker-compose-demo.yml restart grafana
```

---

## PromQL Query Examples

Useful queries for building custom panels:

### Temperature
```promql
# Single GPU
dcgm_gpu_temp{gpu="1"}

# All GPUs
dcgm_gpu_temp{gpu=~"1|2|3|4"}

# Average across fleet
avg(dcgm_gpu_temp)

# Max temperature
max(dcgm_gpu_temp)
```

### Utilization
```promql
# GPU utilization percentage
dcgm_gpu_utilization{gpu="1"}

# High utilization (>80%)
dcgm_gpu_utilization > 80
```

### Power
```promql
# Power usage in Watts
dcgm_power_usage{gpu="1"}

# Total power consumption
sum(dcgm_power_usage)

# Power efficiency (work per watt)
dcgm_gpu_utilization / dcgm_power_usage
```

### Memory
```promql
# Memory used (MB)
dcgm_fb_used{gpu="1"}

# Memory free
dcgm_fb_free{gpu="1"}

# Memory utilization percentage
(dcgm_fb_used / (dcgm_fb_used + dcgm_fb_free)) * 100
```

### Rate Calculations
```promql
# Temperature change rate (°C/min)
rate(dcgm_gpu_temp[5m]) * 60

# Power consumption rate
rate(dcgm_power_usage[1m])
```

---

## Troubleshooting

### Dashboard Not Loading

**Check provisioning:**
```bash
# View Grafana logs
docker logs grafana-demo

# Should see:
# "Loaded dashboard" dcgm-multi-profile-demo.json
```

**Verify files mounted:**
```bash
docker exec grafana-demo ls -la /etc/grafana/provisioning/dashboards/
# Should list both .json files and dashboard-provider.yml
```

### No Data in Panels

**Check Prometheus scraping:**
```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Should show dcgm-exporter as UP
```

**Check metrics:**
```bash
# Test metrics endpoint
curl http://localhost:9400/metrics | grep dcgm_gpu_temp
```

**Check datasource:**
1. Grafana → Configuration → Data Sources
2. Click "Prometheus"
3. Click "Test" button
4. Should show "Data source is working"

### Panels Show "No Data"

**Verify time range:**
- Dashboard time range should be "Last 15 minutes" or similar
- Metrics update every 5 seconds with demo config

**Check PromQL queries:**
1. Click panel title → Edit
2. Look at Query section
3. Verify metric names match (case-sensitive)
4. Try query in Prometheus UI: http://localhost:9090/graph

---

## See Also

- [Prometheus Configuration](../examples/prometheus.yml) - Scrape config
- [Alert Rules](provisioning/alerts/) - Prometheus alerting
- [Deployment Guide](../deployments/README.md) - Full stack setup
- [Metric Profiles](../internal/PROFILES.md) - Profile documentation
