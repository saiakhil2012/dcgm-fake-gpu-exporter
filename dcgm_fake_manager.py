#!/usr/bin/env python3
"""
DCGM Fake GPU Manager
Production-grade manager for DCGM with fake GPUs
"""

import os
import sys
import time
import subprocess
import signal
import argparse
import socket
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def log(msg, color=Colors.GREEN):
    print(f"{color}[{time.strftime('%Y-%m-%d %H:%M:%S')}]{Colors.NC} {msg}")

def log_error(msg):
    log(msg, Colors.RED)

def log_warn(msg):
    log(msg, Colors.YELLOW)

def log_info(msg):
    log(msg, Colors.BLUE)


class DCGMFakeManager:
    def __init__(self, dcgm_dir=None, num_gpus=4):
        self.dcgm_dir = dcgm_dir or os.path.expanduser('~/Workspace/DCGM/_out/Linux-amd64-debug')
        self.num_gpus = num_gpus
        self.pid_file = '/tmp/dcgm-fake-gpu.pid'
        self.log_file = '/tmp/dcgm-fake.log'
        self.hostengine_pid = None

        # Validate DCGM directory
        if not os.path.isdir(self.dcgm_dir):
            raise FileNotFoundError(f"DCGM directory not found: {self.dcgm_dir}")

        # Setup environment
        self.env = os.environ.copy()
        self.env['LD_LIBRARY_PATH'] = f"{self.dcgm_dir}/lib:{self.env.get('LD_LIBRARY_PATH', '')}"
        self.env['LD_PRELOAD'] = f"{self.dcgm_dir}/lib/libnvml_injection.so.1.0.0"
        self.env['NVML_INJECTION_MODE'] = 'True'
        self.env['PYTHONPATH'] = f"{self.dcgm_dir}/share/dcgm_tests:{self.env.get('PYTHONPATH', '')}"

    def is_port_open(self, port=5555, host='localhost', timeout=1):
        """Check if a port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def is_running(self):
        """Check if host engine is running."""
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)  # Check if process exists
                return True, pid
            except (OSError, ValueError):
                return False, None
        return False, None

    def stop(self):
        """Stop the DCGM host engine."""
        running, pid = self.is_running()

        if not running:
            log_warn("DCGM host engine is not running")
            return

        log(f"Stopping DCGM host engine (PID: {pid})...")

        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)

            # Check if still running
            try:
                os.kill(pid, 0)
                log_warn("Process still running, forcing kill...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
            except OSError:
                pass

            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)

            log("✓ DCGM host engine stopped")
        except Exception as e:
            log_error(f"Failed to stop host engine: {e}")

    def start_host_engine(self):
        """Start the DCGM host engine."""
        log("Starting nv-hostengine...")

        hostengine_path = os.path.join(self.dcgm_dir, 'bin/nv-hostengine')

        # Open log file
        log_f = open(self.log_file, 'w')

        # Start the process in foreground mode (-n flag) but as a background subprocess
        # This prevents nv-hostengine from daemonizing itself
        process = subprocess.Popen(
            [hostengine_path, '-n'],  # -n = no daemon mode
            stdout=log_f,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=self.env,
            cwd=self.dcgm_dir,
            start_new_session=True  # Detach from session so it survives script exit
        )

        self.hostengine_pid = process.pid

        # Save PID
        with open(self.pid_file, 'w') as f:
            f.write(str(self.hostengine_pid))

        log(f"Host engine started (PID: {self.hostengine_pid})")

        # Wait for it to be ready
        log("Waiting for host engine to initialize...")
        max_retries = 15
        for i in range(max_retries):
            time.sleep(2)

            # Check if process is still alive
            if process.poll() is not None:
                log_error("Host engine process died!")
                log_error(f"Exit code: {process.returncode}")
                log_error(f"Check log: {self.log_file}")
                log_f.close()
                with open(self.log_file, 'r') as f:
                    log_error(f.read())
                return False

            # Check if port is open
            if self.is_port_open(5555):
                log("✓ Host engine is ready and listening on port 5555")
                # Don't close log_f - keep it open for the process
                return True

            if i < max_retries - 1:
                log_info(f"Still waiting... ({i+1}/{max_retries})")

        log_warn("Timeout waiting for port 5555")

        # Show the log
        log_f.close()
        with open(self.log_file, 'r') as f:
            log_warn("Log contents:")
            print(f.read())

        return False

    def create_fake_gpus(self):
        """Create fake GPU entities."""
        log(f"Creating {self.num_gpus} fake GPUs...")

        # Add DCGM Python modules to path
        sys.path.insert(0, os.path.join(self.dcgm_dir, 'share/dcgm_tests'))

        try:
            import pydcgm
            import dcgm_structs
            import dcgm_structs_internal
            import dcgm_agent_internal
            import dcgm_fields

            # Connect to DCGM
            handle = pydcgm.DcgmHandle(None, "localhost", dcgm_structs.DCGM_OPERATION_MODE_AUTO)

            # Create fake GPUs
            cfe = dcgm_structs_internal.c_dcgmCreateFakeEntities_v2()
            cfe.numToCreate = 0
            fake_gpu_list = []

            for i in range(self.num_gpus):
                cfe.entityList[cfe.numToCreate].entity.entityGroupId = dcgm_fields.DCGM_FE_GPU
                cfe.numToCreate += 1

            updated = dcgm_agent_internal.dcgmCreateFakeEntities(handle.handle, cfe)
            for i in range(updated.numToCreate):
                if updated.entityList[i].entity.entityGroupId == dcgm_fields.DCGM_FE_GPU:
                    fake_gpu_list.append(updated.entityList[i].entity.entityId)

            log(f"✓ Created {len(fake_gpu_list)} fake GPUs: {fake_gpu_list}")

            # Inject GPU attributes using NVML injection
            self._inject_gpu_attributes_nvml(handle.handle, fake_gpu_list)

            return True

        except Exception as e:
            log_error(f"Failed to create fake GPUs: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _inject_gpu_attributes_nvml(self, handle, gpu_ids):
        """Inject GPU attributes using NVML injection."""
        log("Injecting GPU attributes (name, UUID, PCI)...")

        try:
            import dcgm_agent_internal
            import nvml_injection
            import nvml_injection_structs
            import dcgm_nvml
            from ctypes import c_char_p, create_string_buffer

            gpu_models = [
                "Tesla V100-SXM2-16GB",
                "Tesla V100-SXM2-32GB",
                "A100-SXM4-40GB",
                "A100-SXM4-80GB",
                "H100-SXM5-80GB",
                "A100-PCIE-40GB"
            ]

            for idx, gpu_id in enumerate(gpu_ids):
                gpu_name = gpu_models[idx % len(gpu_models)]
                pci_bus_id = f"00000000:{idx+1:02x}:00.0"
                uuid = f"GPU-{idx+1:08x}-fake-dcgm-{idx+1:04x}-{self.num_gpus:04x}{idx+1:08x}"

                # Inject GPU Name
                try:
                    injected_ret = nvml_injection.c_injectNvmlRet_t()
                    injected_ret.nvmlRet = dcgm_nvml.NVML_SUCCESS
                    injected_ret.values[0].type = nvml_injection_structs.c_injectionArgType_t.INJECTION_CHAR_PTR
                    injected_ret.values[0].value.CharPtr = c_char_p(gpu_name.encode('utf-8'))
                    injected_ret.valueCount = 1

                    dcgm_agent_internal.dcgmInjectNvmlDevice(
                        handle, gpu_id, "Name", None, 0, injected_ret)
                except Exception as e:
                    log_warn(f"Could not inject name for GPU {gpu_id}: {e}")

                # Inject UUID
                try:
                    injected_ret = nvml_injection.c_injectNvmlRet_t()
                    injected_ret.nvmlRet = dcgm_nvml.NVML_SUCCESS
                    injected_ret.values[0].type = nvml_injection_structs.c_injectionArgType_t.INJECTION_CHAR_PTR
                    injected_ret.values[0].value.CharPtr = c_char_p(uuid.encode('utf-8'))
                    injected_ret.valueCount = 1

                    dcgm_agent_internal.dcgmInjectNvmlDevice(
                        handle, gpu_id, "UUID", None, 0, injected_ret)
                except Exception as e:
                    log_warn(f"Could not inject UUID for GPU {gpu_id}: {e}")

                # Inject PCI Info (structure)
                try:
                    injected_ret = nvml_injection.c_injectNvmlRet_t()
                    injected_ret.nvmlRet = dcgm_nvml.NVML_SUCCESS
                    injected_ret.values[0].type = nvml_injection_structs.c_injectionArgType_t.INJECTION_PCIINFO
                    # Create PCI info structure
                    bus_id_buf = create_string_buffer(pci_bus_id.encode('utf-8'), 32)
                    injected_ret.values[0].value.PciInfo.busId = bus_id_buf.value
                    injected_ret.values[0].value.PciInfo.domain = 0
                    injected_ret.values[0].value.PciInfo.bus = idx + 1
                    injected_ret.values[0].value.PciInfo.device = 0
                    injected_ret.values[0].value.PciInfo.pciDeviceId = 0x1DB6  # V100/A100 device ID
                    injected_ret.values[0].value.PciInfo.pciSubSystemId = 0x12A2
                    injected_ret.valueCount = 1

                    dcgm_agent_internal.dcgmInjectNvmlDevice(
                        handle, gpu_id, "PciInfo", None, 0, injected_ret)
                except Exception as e:
                    log_warn(f"Could not inject PCI info for GPU {gpu_id}: {e}")

                log_info(f"  GPU {gpu_id}: {gpu_name}, {pci_bus_id}, {uuid[:40]}...")

            log("✓ GPU attributes injected")

        except Exception as e:
            log_warn(f"Failed to inject GPU attributes: {e}")
            import traceback
            traceback.print_exc()

    def inject_metrics(self):
        """Inject realistic metrics into fake GPUs."""
        log("Injecting realistic metrics...")

        # Add DCGM Python modules to path
        sys.path.insert(0, os.path.join(self.dcgm_dir, 'share/dcgm_tests'))

        try:
            import pydcgm
            import dcgm_structs
            import dcgm_fields
            import dcgm_field_injection_helpers
            import dcgm_agent
            import random

            # Connect to DCGM
            handle = pydcgm.DcgmHandle(None, "localhost", dcgm_structs.DCGM_OPERATION_MODE_AUTO)
            gpu_ids = dcgm_agent.dcgmGetAllDevices(handle.handle)

            # Skip GPU 0 (it's the injected V100 from nvml injection library)
            # Only inject into fake GPUs (1-N)
            fake_gpu_ids = [gid for gid in gpu_ids if gid > 0]

            for gpu_id in fake_gpu_ids:
                # Add some randomness to make it realistic
                temp = 50 + (gpu_id - 1) * 5 + random.randint(0, 5)
                power = 150 + (gpu_id - 1) * 20 + random.randint(-10, 10)
                gpu_util = 30 + (gpu_id - 1) * 10 + random.randint(-5, 5)
                mem_util = 40 + (gpu_id - 1) * 5 + random.randint(-5, 5)

                # Clamp values
                temp = max(45, min(85, temp))
                power = max(100, min(300, power))
                gpu_util = max(0, min(100, gpu_util))
                mem_util = max(0, min(100, mem_util))

                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_GPU_TEMP,
                    temp, 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_POWER_USAGE,
                    power, 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_GPU_UTIL,
                    gpu_util, 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_MEM_COPY_UTIL,
                    mem_util, 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_SM_CLOCK,
                    1400 + random.randint(-50, 100), 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_MEM_CLOCK,
                    877 + random.randint(-20, 0), 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_FB_TOTAL,
                    16384, 0, True)

                used_mem = 4096 + (gpu_id - 1) * 1024 + random.randint(-512, 512)
                used_mem = max(2048, min(14336, used_mem))

                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_FB_USED,
                    used_mem, 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_FB_FREE,
                    16384 - used_mem, 0, True)

                log_info(f"  GPU {gpu_id}: {temp}°C, {power}W, {gpu_util}% util")

            log("✓ Metrics injected")
            return True

        except Exception as e:
            log_error(f"Failed to inject metrics: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start_metric_updater(self, interval=30):
        """Start background thread to update metrics periodically."""
        import threading

        def update_loop():
            while True:
                try:
                    time.sleep(interval)
                    log_info("Updating metrics...")
                    self.inject_metrics()
                except Exception as e:
                    log_error(f"Metric updater error: {e}")

        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        log(f"✓ Started metric updater (updates every {interval}s)")

    def create_wrapper(self):
        """Create dcgm.sh wrapper script."""
        wrapper_path = os.path.join(self.dcgm_dir, 'dcgm.sh')

        wrapper_content = f"""#!/bin/bash
# DCGM wrapper with injection environment
DCGM_DIR="{self.dcgm_dir}"
export LD_LIBRARY_PATH=$DCGM_DIR/lib:$LD_LIBRARY_PATH
export LD_PRELOAD=$DCGM_DIR/lib/libnvml_injection.so.1.0.0
export NVML_INJECTION_MODE=True
exec $DCGM_DIR/bin/dcgmi "$@"
"""

        with open(wrapper_path, 'w') as f:
            f.write(wrapper_content)

        os.chmod(wrapper_path, 0o755)
        log(f"✓ Created wrapper: {wrapper_path}")

    def start(self):
        """Start DCGM with fake GPUs."""
        print("=" * 50)
        print("DCGM Fake GPU Manager - Start")
        print("=" * 50)
        print()

        # Check if already running
        running, pid = self.is_running()
        if running:
            log_warn(f"DCGM is already running (PID: {pid})")
            response = input("Stop and restart? (y/n): ").lower().strip()
            if response == 'y':
                self.stop()
                time.sleep(2)
            else:
                log("Exiting...")
                return False

        # Start host engine
        if not self.start_host_engine():
            log_error("Failed to start host engine")
            return False

        time.sleep(2)

        # Create fake GPUs
        if not self.create_fake_gpus():
            log_error("Failed to create fake GPUs")
            self.stop()
            return False

        time.sleep(1)

        # Inject metrics
        if not self.inject_metrics():
            log_warn("Failed to inject metrics (GPUs created but no metrics)")

        # Start metric updater for dynamic updates
        self.start_metric_updater(interval=30)

        # Create wrapper
        self.create_wrapper()

        print()
        print("=" * 50)
        print("✓ Setup Complete!")
        print("=" * 50)
        print()
        log_info(f"Host Engine PID: {self.hostengine_pid}")
        log_info(f"Fake GPUs: {self.num_gpus} (GPUs 1-{self.num_gpus})")
        log_info(f"Note: GPU 0 is from NVML injection (shows N/A)")
        log_info(f"Metrics: Auto-updating every 30 seconds")
        log_info(f"Log File: {self.log_file}")
        print()
        print("Usage:")
        print(f"  {self.dcgm_dir}/dcgm.sh discovery -l")
        print(f"  {self.dcgm_dir}/dcgm.sh dmon -e 150,155,203,204")
        print()
        print(f"To stop: python3 {sys.argv[0]} stop")
        print(f"Or: kill {self.hostengine_pid}")
        print()

        return True

    def status(self):
        """Show status of DCGM."""
        running, pid = self.is_running()

        print("=" * 50)
        print("DCGM Fake GPU Manager - Status")
        print("=" * 50)
        print()

        if running:
            log(f"DCGM is running (PID: {pid})")
            log_info(f"Log file: {self.log_file}")

            if self.is_port_open(5555):
                log("✓ Port 5555 is open and accepting connections")
            else:
                log_warn("Port 5555 is not accessible")

            # Try to get GPU count
            try:
                sys.path.insert(0, os.path.join(self.dcgm_dir, 'share/dcgm_tests'))
                import pydcgm
                import dcgm_agent

                handle = pydcgm.DcgmHandle(None, "localhost")
                gpu_ids = dcgm_agent.dcgmGetAllDevices(handle.handle)
                log_info(f"Number of GPUs: {len(gpu_ids)}")
            except:
                log_warn("Could not query GPU count")
        else:
            log_warn("DCGM is not running")

        print()


def main():
    parser = argparse.ArgumentParser(
        description='DCGM Fake GPU Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 dcgm_fake_manager.py start           # Start with 4 GPUs
  python3 dcgm_fake_manager.py start -n 8      # Start with 8 GPUs
  python3 dcgm_fake_manager.py status          # Check status
  python3 dcgm_fake_manager.py stop            # Stop service
        """
    )

    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'],
                       help='Action to perform')
    parser.add_argument('-n', '--num-gpus', type=int, default=4,
                       help='Number of fake GPUs to create (default: 4)')
    parser.add_argument('-d', '--dcgm-dir',
                       help='DCGM directory (default: ~/Workspace/DCGM/_out/Linux-amd64-debug)')

    args = parser.parse_args()

    try:
        manager = DCGMFakeManager(dcgm_dir=args.dcgm_dir, num_gpus=args.num_gpus)

        if args.action == 'start':
            manager.start()
        elif args.action == 'stop':
            manager.stop()
        elif args.action == 'restart':
            manager.stop()
            time.sleep(2)
            manager.start()
        elif args.action == 'status':
            manager.status()

    except Exception as e:
        log_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()