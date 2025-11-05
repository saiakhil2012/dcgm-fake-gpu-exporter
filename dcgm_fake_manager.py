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
import math
import random
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


# ============================================================================
# Metric Profile Classes
# ============================================================================

class MetricProfile:
    """Base class for metric behavior profiles."""
    
    def __init__(self, name):
        self.name = name
        self.iteration = 0
    
    def apply(self, gpu_id, base_values):
        """
        Apply profile transformation to base metric values.
        
        Args:
            gpu_id: GPU identifier (1-N)
            base_values: dict with keys: temp, power, gpu_util, mem_util, sm_clock, mem_clock, fb_used
        
        Returns:
            dict with transformed values
        """
        raise NotImplementedError
    
    def _clamp(self, value, min_val, max_val):
        """Clamp value between min and max."""
        return max(min_val, min(max_val, value))


class StaticProfile(MetricProfile):
    """Static profile - fixed random values per GPU (original v1.x behavior)."""
    
    def __init__(self):
        super().__init__("static")
    
    def apply(self, gpu_id, base_values):
        # Original logic from the codebase
        temp = 50 + (gpu_id - 1) * 5 + random.randint(0, 5)
        power = 150 + (gpu_id - 1) * 20 + random.randint(-10, 10)
        gpu_util = 30 + (gpu_id - 1) * 10 + random.randint(-5, 5)
        mem_util = 40 + (gpu_id - 1) * 5 + random.randint(-5, 5)
        
        # Clamp values
        temp = self._clamp(temp, 45, 85)
        power = self._clamp(power, 100, 300)
        gpu_util = self._clamp(gpu_util, 0, 100)
        mem_util = self._clamp(mem_util, 0, 100)
        
        sm_clock = 1400 + random.randint(-50, 100)
        mem_clock = 877 + random.randint(-20, 0)
        
        used_mem = 4096 + (gpu_id - 1) * 1024 + random.randint(-512, 512)
        used_mem = self._clamp(used_mem, 2048, 14336)
        
        return {
            'temp': temp,
            'power': power,
            'gpu_util': gpu_util,
            'mem_util': mem_util,
            'sm_clock': sm_clock,
            'mem_clock': mem_clock,
            'fb_used': used_mem
        }


class StableProfile(MetricProfile):
    """Stable profile - constant values with minimal variation."""
    
    def __init__(self):
        super().__init__("stable")
    
    def apply(self, gpu_id, base_values):
        # Very small random variations
        temp = 55 + (gpu_id - 1) * 3 + random.randint(-1, 1)
        power = 180 + (gpu_id - 1) * 15 + random.randint(-3, 3)
        gpu_util = 50 + (gpu_id - 1) * 5 + random.randint(-2, 2)
        mem_util = 45 + (gpu_id - 1) * 3 + random.randint(-2, 2)
        
        temp = self._clamp(temp, 45, 90)
        power = self._clamp(power, 100, 350)
        gpu_util = self._clamp(gpu_util, 0, 100)
        mem_util = self._clamp(mem_util, 0, 100)
        
        sm_clock = 1400 + random.randint(-10, 10)
        mem_clock = 877 + random.randint(-5, 5)
        used_mem = 6144 + (gpu_id - 1) * 512 + random.randint(-100, 100)
        used_mem = self._clamp(used_mem, 2048, 14336)
        
        return {
            'temp': temp,
            'power': power,
            'gpu_util': gpu_util,
            'mem_util': mem_util,
            'sm_clock': sm_clock,
            'mem_clock': mem_clock,
            'fb_used': used_mem
        }


class SpikeProfile(MetricProfile):
    """Spike profile - random sudden spikes in usage."""
    
    def __init__(self):
        super().__init__("spike")
    
    def apply(self, gpu_id, base_values):
        self.iteration += 1
        
        # 20% chance of spike
        is_spiking = random.random() < 0.20
        
        if is_spiking:
            # Spike conditions
            temp = 75 + random.randint(0, 15)
            power = 280 + random.randint(0, 50)
            gpu_util = 90 + random.randint(0, 10)
            mem_util = 85 + random.randint(0, 15)
            used_mem = 12288 + random.randint(0, 2048)
        else:
            # Normal conditions
            temp = 50 + (gpu_id - 1) * 4 + random.randint(-5, 5)
            power = 150 + (gpu_id - 1) * 15 + random.randint(-10, 10)
            gpu_util = 25 + (gpu_id - 1) * 8 + random.randint(-10, 10)
            mem_util = 30 + (gpu_id - 1) * 5 + random.randint(-10, 10)
            used_mem = 4096 + (gpu_id - 1) * 1024 + random.randint(-1024, 1024)
        
        temp = self._clamp(temp, 45, 95)
        power = self._clamp(power, 100, 350)
        gpu_util = self._clamp(gpu_util, 0, 100)
        mem_util = self._clamp(mem_util, 0, 100)
        used_mem = self._clamp(used_mem, 2048, 14336)
        
        sm_clock = 1400 + random.randint(-100, 200) if is_spiking else 1400 + random.randint(-50, 50)
        mem_clock = 877 + random.randint(-20, 20)
        
        return {
            'temp': temp,
            'power': power,
            'gpu_util': gpu_util,
            'mem_util': mem_util,
            'sm_clock': sm_clock,
            'mem_clock': mem_clock,
            'fb_used': used_mem
        }


class WaveProfile(MetricProfile):
    """Wave profile - sine wave patterns for realistic workload simulation."""
    
    def __init__(self):
        super().__init__("wave")
        self.time_offset = random.uniform(0, 2 * math.pi)
    
    def apply(self, gpu_id, base_values):
        self.iteration += 1
        
        # Create sine wave with period of ~60 iterations (30 minutes at 30s intervals)
        phase = (self.iteration / 60.0) * 2 * math.pi + self.time_offset + (gpu_id * 0.5)
        wave = math.sin(phase)
        
        # Map wave to metrics (wave ranges from -1 to 1)
        temp_base = 60
        temp_amplitude = 20
        temp = temp_base + (wave * temp_amplitude)
        
        power_base = 200
        power_amplitude = 80
        power = power_base + (wave * power_amplitude)
        
        util_base = 50
        util_amplitude = 40
        gpu_util = util_base + (wave * util_amplitude)
        mem_util = util_base + (wave * util_amplitude * 0.8)
        
        mem_base = 8192
        mem_amplitude = 4096
        used_mem = mem_base + (wave * mem_amplitude)
        
        # Convert all float values to integers
        temp = int(self._clamp(temp, 45, 90))
        power = int(self._clamp(power, 100, 350))
        gpu_util = int(self._clamp(gpu_util, 0, 100))
        mem_util = int(self._clamp(mem_util, 0, 100))
        used_mem = int(self._clamp(used_mem, 2048, 14336))
        
        sm_clock = 1400 + int(wave * 200)
        mem_clock = 877 + int(wave * 100)
        
        return {
            'temp': temp,
            'power': power,
            'gpu_util': gpu_util,
            'mem_util': mem_util,
            'sm_clock': sm_clock,
            'mem_clock': mem_clock,
            'fb_used': used_mem
        }


class DegradingProfile(MetricProfile):
    """Degrading profile - simulates gradual performance decline."""
    
    def __init__(self):
        super().__init__("degrading")
    
    def apply(self, gpu_id, base_values):
        self.iteration += 1
        
        # Gradual increase in temperature and power over time
        # Gradual decrease in performance
        degradation_factor = min(self.iteration / 200.0, 0.5)  # Up to 50% degradation
        
        temp = 50 + (degradation_factor * 30) + random.randint(-3, 3)
        power = 150 + (degradation_factor * 100) + random.randint(-10, 10)
        gpu_util = 70 - (degradation_factor * 30) + random.randint(-5, 5)
        mem_util = 60 - (degradation_factor * 20) + random.randint(-5, 5)
        
        # Convert all float values to integers
        temp = int(self._clamp(temp, 45, 95))
        power = int(self._clamp(power, 100, 350))
        gpu_util = int(self._clamp(gpu_util, 0, 100))
        mem_util = int(self._clamp(mem_util, 0, 100))
        
        sm_clock = int(1400 - (degradation_factor * 300)) + random.randint(-50, 50)
        mem_clock = int(877 - (degradation_factor * 100)) + random.randint(-20, 20)
        used_mem = 6144 + random.randint(-1024, 1024)
        used_mem = int(self._clamp(used_mem, 2048, 14336))
        
        return {
            'temp': temp,
            'power': power,
            'gpu_util': gpu_util,
            'mem_util': mem_util,
            'sm_clock': sm_clock,
            'mem_clock': mem_clock,
            'fb_used': used_mem
        }


class FaultyProfile(MetricProfile):
    """Faulty profile - simulates intermittent GPU failures."""
    
    def __init__(self):
        super().__init__("faulty")
        self.is_faulting = False
        self.fault_countdown = 0
    
    def apply(self, gpu_id, base_values):
        self.iteration += 1
        
        # Randomly enter fault state (10% chance)
        if not self.is_faulting and random.random() < 0.10:
            self.is_faulting = True
            self.fault_countdown = random.randint(3, 10)  # Fault for 3-10 iterations
        
        # Exit fault state
        if self.is_faulting:
            self.fault_countdown -= 1
            if self.fault_countdown <= 0:
                self.is_faulting = False
        
        if self.is_faulting:
            # Faulty conditions - high temp, erratic power, low performance
            temp = 85 + random.randint(0, 10)
            power = random.choice([50, 100, 300, 350])  # Erratic
            gpu_util = random.randint(0, 20)  # Very low
            mem_util = random.randint(0, 25)
            sm_clock = 800 + random.randint(-200, 200)  # Throttled
            mem_clock = 500 + random.randint(-100, 100)
            used_mem = 2048 + random.randint(0, 1024)
        else:
            # Normal operation
            temp = 55 + (gpu_id - 1) * 4 + random.randint(-5, 5)
            power = 170 + (gpu_id - 1) * 15 + random.randint(-10, 10)
            gpu_util = 60 + (gpu_id - 1) * 5 + random.randint(-10, 10)
            mem_util = 55 + (gpu_id - 1) * 3 + random.randint(-10, 10)
            sm_clock = 1400 + random.randint(-50, 50)
            mem_clock = 877 + random.randint(-20, 20)
            used_mem = 7168 + (gpu_id - 1) * 512 + random.randint(-512, 512)
        
        temp = self._clamp(temp, 45, 100)
        power = self._clamp(power, 50, 350)
        gpu_util = self._clamp(gpu_util, 0, 100)
        mem_util = self._clamp(mem_util, 0, 100)
        used_mem = self._clamp(used_mem, 2048, 14336)
        
        return {
            'temp': temp,
            'power': power,
            'gpu_util': gpu_util,
            'mem_util': mem_util,
            'sm_clock': sm_clock,
            'mem_clock': mem_clock,
            'fb_used': used_mem
        }


class ChaosProfile(MetricProfile):
    """Chaos profile - completely random, unpredictable behavior."""
    
    def __init__(self):
        super().__init__("chaos")
    
    def apply(self, gpu_id, base_values):
        temp = random.randint(45, 95)
        power = random.randint(100, 350)
        gpu_util = random.randint(0, 100)
        mem_util = random.randint(0, 100)
        sm_clock = random.randint(800, 1800)
        mem_clock = random.randint(600, 1000)
        used_mem = random.randint(2048, 14336)
        
        return {
            'temp': temp,
            'power': power,
            'gpu_util': gpu_util,
            'mem_util': mem_util,
            'sm_clock': sm_clock,
            'mem_clock': mem_clock,
            'fb_used': used_mem
        }


class ProfileFactory:
    """Factory for creating metric profiles."""
    
    PROFILES = {
        'static': StaticProfile,
        'stable': StableProfile,
        'spike': SpikeProfile,
        'wave': WaveProfile,
        'degrading': DegradingProfile,
        'faulty': FaultyProfile,
        'chaos': ChaosProfile,
    }
    
    @classmethod
    def create(cls, profile_name):
        """Create a profile instance by name."""
        profile_class = cls.PROFILES.get(profile_name.lower())
        if profile_class is None:
            log_warn(f"Unknown profile '{profile_name}', using 'static' profile")
            return StaticProfile()
        return profile_class()
    
    @classmethod
    def list_profiles(cls):
        """List all available profiles."""
        return list(cls.PROFILES.keys())


# ============================================================================
# DCGM Manager Class
# ============================================================================

class DCGMFakeManager:
    def __init__(self, dcgm_dir=None, num_gpus=4, metric_profile='static', 
                 gpu_profiles=None, update_interval=30, gpu_start_index=1):
        self.dcgm_dir = dcgm_dir or os.path.expanduser('~/Workspace/DCGM/_out/Linux-amd64-debug')
        self.num_gpus = num_gpus
        self.metric_profile = metric_profile
        self.gpu_profiles = gpu_profiles  # List of profiles per GPU
        self.update_interval = update_interval
        self.gpu_start_index = gpu_start_index
        self.pid_file = '/tmp/dcgm-fake-gpu.pid'
        self.log_file = '/tmp/dcgm-fake.log'
        self.hostengine_pid = None
        
        # Create profile instances for each GPU
        self.profiles = {}
        if self.gpu_profiles and len(self.gpu_profiles) > 0:
            # Per-GPU profiles specified
            for i in range(1, self.num_gpus + 1):
                profile_idx = (i - 1) % len(self.gpu_profiles)
                profile_name = self.gpu_profiles[profile_idx]
                self.profiles[i] = ProfileFactory.create(profile_name)
            log_info(f"Using per-GPU profiles: {self.gpu_profiles}")
        else:
            # Use same profile for all GPUs
            for i in range(1, self.num_gpus + 1):
                self.profiles[i] = ProfileFactory.create(self.metric_profile)
            log_info(f"Using profile '{self.metric_profile}' for all GPUs")

        # Validate DCGM directory
        if not os.path.isdir(self.dcgm_dir):
            raise FileNotFoundError(f"DCGM directory not found: {self.dcgm_dir}")

        # Setup environment
        self.env = os.environ.copy()
        self.env['LD_LIBRARY_PATH'] = f"{self.dcgm_dir}/lib:{self.env.get('LD_LIBRARY_PATH', '')}"
        self.env['LD_PRELOAD'] = f"{self.dcgm_dir}/lib/libnvml_injection.so.1.0.0"
        self.env['NVML_INJECTION_MODE'] = 'True'
        self.env['PYTHONPATH'] = f"{self.dcgm_dir}/share/dcgm_tests:{self.env.get('PYTHONPATH', '')}"
        
        # Warnings for large GPU counts
        if self.num_gpus > 100:
            log_warn(f"Creating {self.num_gpus} GPUs may impact performance and memory usage")
        if self.num_gpus > 500:
            log_warn(f"Large GPU count (>{self.num_gpus}) may cause significant resource usage")

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
        """Inject realistic metrics into fake GPUs using configured profiles."""
        log("Injecting metrics using profiles...")

        # Add DCGM Python modules to path
        sys.path.insert(0, os.path.join(self.dcgm_dir, 'share/dcgm_tests'))

        try:
            import pydcgm
            import dcgm_structs
            import dcgm_fields
            import dcgm_field_injection_helpers
            import dcgm_agent

            # Connect to DCGM
            handle = pydcgm.DcgmHandle(None, "localhost", dcgm_structs.DCGM_OPERATION_MODE_AUTO)
            gpu_ids = dcgm_agent.dcgmGetAllDevices(handle.handle)

            # Skip GPU 0 (it's the injected V100 from nvml injection library)
            # Only inject into fake GPUs (1-N)
            fake_gpu_ids = [gid for gid in gpu_ids if gid > 0]

            for gpu_id in fake_gpu_ids:
                # Get the profile for this GPU
                profile = self.profiles.get(gpu_id, self.profiles[1])
                
                # Apply profile transformation
                base_values = {}  # Profiles generate their own values
                metrics = profile.apply(gpu_id, base_values)
                
                # Convert all metrics to integers (DCGM expects i64, not floats)
                metrics = {k: int(v) for k, v in metrics.items()}
                
                # Inject the metrics
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_GPU_TEMP,
                    metrics['temp'], 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_POWER_USAGE,
                    metrics['power'], 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_GPU_UTIL,
                    metrics['gpu_util'], 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_MEM_COPY_UTIL,
                    metrics['mem_util'], 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_SM_CLOCK,
                    metrics['sm_clock'], 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_MEM_CLOCK,
                    metrics['mem_clock'], 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_FB_TOTAL,
                    16384, 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_FB_USED,
                    metrics['fb_used'], 0, True)
                dcgm_field_injection_helpers.inject_value(
                    handle.handle, gpu_id, dcgm_fields.DCGM_FI_DEV_FB_FREE,
                    16384 - metrics['fb_used'], 0, True)

                profile_name = profile.name
                log_info(f"  GPU {gpu_id} [{profile_name}]: {metrics['temp']:.0f}°C, "
                        f"{metrics['power']:.0f}W, {metrics['gpu_util']:.0f}% util")

            log("✓ Metrics injected")
            return True

        except Exception as e:
            log_error(f"Failed to inject metrics: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start_metric_updater(self, interval=None):
        """Start background thread to update metrics periodically."""
        import threading
        
        if interval is None:
            interval = self.update_interval

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
        self.start_metric_updater()

        # Create wrapper
        self.create_wrapper()

        print()
        print("=" * 50)
        print("✓ Setup Complete!")
        print("=" * 50)
        print()
        log_info(f"Host Engine PID: {self.hostengine_pid}")
        log_info(f"Fake GPUs: {self.num_gpus} (GPUs 1-{self.num_gpus})")
        log_info(f"Metric Profile: {self.metric_profile}")
        if self.gpu_profiles:
            log_info(f"Per-GPU Profiles: {', '.join(self.gpu_profiles)}")
        log_info(f"Update Interval: {self.update_interval}s")
        log_info(f"Note: GPU 0 is from NVML injection (shows N/A)")
        log_info(f"Metrics: Auto-updating every {self.update_interval} seconds")
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
        epilog=f"""
Examples:
  python3 dcgm_fake_manager.py start                    # Start with defaults (4 GPUs, static profile)
  python3 dcgm_fake_manager.py start -n 8               # Start with 8 GPUs
  python3 dcgm_fake_manager.py start -p spike           # Use spike profile
  python3 dcgm_fake_manager.py start --gpu-profiles stable,spike,faulty  # Per-GPU profiles
  python3 dcgm_fake_manager.py status                   # Check status
  python3 dcgm_fake_manager.py stop                     # Stop service

Available Profiles:
  {', '.join(ProfileFactory.list_profiles())}

Environment Variables:
  NUM_FAKE_GPUS            Number of GPUs (default: 4)
  METRIC_PROFILE           Profile name (default: static)
  GPU_PROFILES             Comma-separated per-GPU profiles (overrides METRIC_PROFILE)
  METRIC_UPDATE_INTERVAL   Update interval in seconds (default: 30)
  GPU_START_INDEX          Starting GPU index (default: 1)
        """
    )

    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'],
                       help='Action to perform')
    parser.add_argument('-n', '--num-gpus', type=int,
                       help='Number of fake GPUs to create (default: from NUM_FAKE_GPUS env or 4)')
    parser.add_argument('-p', '--profile',
                       help=f'Metric profile to use (default: from METRIC_PROFILE env or static). Available: {", ".join(ProfileFactory.list_profiles())}')
    parser.add_argument('--gpu-profiles',
                       help='Comma-separated list of profiles per GPU (e.g., "stable,spike,faulty")')
    parser.add_argument('-i', '--interval', type=int,
                       help='Metric update interval in seconds (default: from METRIC_UPDATE_INTERVAL env or 30)')
    parser.add_argument('--gpu-start-index', type=int,
                       help='Starting GPU index (default: from GPU_START_INDEX env or 1)')
    parser.add_argument('-d', '--dcgm-dir',
                       help='DCGM directory (default: ~/Workspace/DCGM/_out/Linux-amd64-debug)')

    args = parser.parse_args()

    # Read from environment variables with fallbacks
    try:
        num_gpus = args.num_gpus if args.num_gpus is not None else int(os.environ.get('NUM_FAKE_GPUS', '4'))
    except ValueError:
        log_warn("Invalid NUM_FAKE_GPUS value, using default: 4")
        num_gpus = 4

    metric_profile = args.profile if args.profile else os.environ.get('METRIC_PROFILE', 'static')
    
    # Parse GPU profiles (per-GPU)
    gpu_profiles = None
    if args.gpu_profiles:
        gpu_profiles = [p.strip() for p in args.gpu_profiles.split(',')]
    elif os.environ.get('GPU_PROFILES'):
        gpu_profiles = [p.strip() for p in os.environ.get('GPU_PROFILES', '').split(',')]
    
    try:
        update_interval = args.interval if args.interval is not None else int(os.environ.get('METRIC_UPDATE_INTERVAL', '30'))
    except ValueError:
        log_warn("Invalid METRIC_UPDATE_INTERVAL value, using default: 30")
        update_interval = 30
    
    try:
        gpu_start_index = args.gpu_start_index if args.gpu_start_index is not None else int(os.environ.get('GPU_START_INDEX', '1'))
    except ValueError:
        log_warn("Invalid GPU_START_INDEX value, using default: 1")
        gpu_start_index = 1

    try:
        manager = DCGMFakeManager(
            dcgm_dir=args.dcgm_dir,
            num_gpus=num_gpus,
            metric_profile=metric_profile,
            gpu_profiles=gpu_profiles,
            update_interval=update_interval,
            gpu_start_index=gpu_start_index
        )

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