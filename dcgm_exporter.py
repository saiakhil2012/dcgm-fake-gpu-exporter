#!/usr/bin/env python3
"""DCGM OpenTelemetry/Prometheus Exporter using dcgmi CLI"""
import os, sys, time, subprocess, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Lock

metrics_cache = ""
metrics_lock = Lock()
DCGMI_PATH = "/usr/local/dcgm/share/dcgm_tests/apps/amd64/dcgmi"

# Map DCGM field IDs to metric names
FIELD_MAPPING = {
    '150': ('dcgm_gpu_temp', 'GPU temperature in Celsius'),
    '155': ('dcgm_power_usage', 'Power usage in watts'),
    '203': ('dcgm_gpu_utilization', 'GPU utilization percentage'),
    '204': ('dcgm_mem_copy_utilization', 'Memory utilization percentage'),
    '210': ('dcgm_sm_clock', 'SM clock in MHz'),
    '211': ('dcgm_mem_clock', 'Memory clock in MHz'),
    '251': ('dcgm_fb_total', 'Total framebuffer in MB'),
    '252': ('dcgm_fb_used', 'Used framebuffer in MB'),
    '253': ('dcgm_fb_free', 'Free framebuffer in MB'),
}

def parse_dcgmi_output(output):
    metrics = {}
    lines = output.strip().split('\n')
    for i, line in enumerate(lines):
        if line.startswith('GPU '):
            parts = line.split()
            if len(parts) >= 2:
                gpu_id = parts[1]
                if gpu_id == '0':
                    continue
                values = parts[2:]
                if gpu_id not in metrics:
                    metrics[gpu_id] = {}
                field_ids = list(FIELD_MAPPING.keys())
                for idx, val in enumerate(values):
                    if idx < len(field_ids):
                        field_id = field_ids[idx]
                        if val != 'N/A':
                            try:
                                metrics[gpu_id][field_id] = float(val)
                            except ValueError:
                                pass
    return metrics

def collect_metrics():
    try:
        field_ids = ','.join(FIELD_MAPPING.keys())
        result = subprocess.run(
            [DCGMI_PATH, 'dmon', '-e', field_ids, '-c', '1'],
            capture_output=True,
            text=True,
            timeout=5,
            env=os.environ.copy()
        )
        if result.returncode != 0:
            print(f"dcgmi error: {result.stderr}", flush=True)
            return "# Error: dcgmi command failed\n"
        gpu_metrics = parse_dcgmi_output(result.stdout)
        lines = []
        for gpu_id, fields in gpu_metrics.items():
            labels = f'gpu="{gpu_id}",device="nvidia{gpu_id}"'
            for field_id, value in fields.items():
                if field_id in FIELD_MAPPING:
                    metric_name, _ = FIELD_MAPPING[field_id]
                    lines.append(f'{metric_name}{{{labels}}} {value}')
        output = []
        for field_id, (name, help_text) in FIELD_MAPPING.items():
            output.append(f"# HELP {name} {help_text}")
            output.append(f"# TYPE {name} gauge")
        output.extend(sorted(lines))
        return '\n'.join(output) + '\n'
    except subprocess.TimeoutExpired:
        print("dcgmi timeout", flush=True)
        return "# Error: dcgmi timeout\n"
    except Exception as e:
        print(f"Error collecting metrics: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return "# Error: collection failed\n"

def update_metrics_cache():
    global metrics_cache
    while True:
        try:
            with metrics_lock:
                metrics_cache = collect_metrics()
        except Exception as e:
            print(f"Cache update error: {e}", flush=True)
        time.sleep(5)

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            with metrics_lock:
                response = metrics_cache
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(response.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK\n')
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *args): pass

if __name__ == '__main__':
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)
    print("DCGM OpenTelemetry Exporter (CLI-based)", flush=True)
    if not os.path.exists(DCGMI_PATH):
        print(f"✗ dcgmi not found at {DCGMI_PATH}", flush=True)
        sys.exit(1)
    print(f"✓ Using dcgmi at {DCGMI_PATH}", flush=True)
    print("Testing dcgmi...", flush=True)
    try:
        test_result = collect_metrics()
        print("Sample output:", flush=True)
        print(test_result[:500], flush=True)
    except Exception as e:
        print(f"✗ Test failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
    Thread(target=update_metrics_cache, daemon=True).start()
    port = int(os.environ.get('EXPORTER_PORT', '9400'))
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)
    print(f"✓ Started on port {port}", flush=True)
    print(f"  Metrics: http://localhost:{port}/metrics", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
