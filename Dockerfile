FROM ubuntu:22.04

# Install system and Python dependencies
RUN apt-get update && \
	apt-get install -y python3 python3-pip git wget curl lsb-release && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for OpenTelemetry and others
RUN pip3 install --no-cache-dir \
	opentelemetry-sdk \
	opentelemetry-api \
	opentelemetry-exporter-otlp \
	opentelemetry-sdk-extension-aws \
	psutil

RUN mkdir -p /root/Workspace/DCGM/_out/Linux-amd64-debug/bin
RUN mkdir -p /root/Workspace/DCGM/_out/Linux-amd64-debug/lib
RUN mkdir -p /root/Workspace/DCGM/_out/Linux-amd64-debug/share/dcgm_tests
COPY bin/nv-hostengine /root/Workspace/DCGM/_out/Linux-amd64-debug/bin/nv-hostengine
COPY lib/ /root/Workspace/DCGM/_out/Linux-amd64-debug/lib/
COPY share/dcgm_tests/ /root/Workspace/DCGM/_out/Linux-amd64-debug/share/dcgm_tests/
COPY dcgm_exporter.py /root/Workspace/DCGM/_out/Linux-amd64-debug/dcgm_exporter.py
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY dcgm_fake_manager.py /usr/local/bin/dcgm_fake_manager.py

RUN chmod +x /root/Workspace/DCGM/_out/Linux-amd64-debug/dcgm_exporter.py /usr/local/bin/docker-entrypoint.sh /usr/local/bin/dcgm_fake_manager.py

ENV LD_LIBRARY_PATH=/root/Workspace/DCGM/_out/Linux-amd64-debug/lib
ENV LD_PRELOAD=/root/Workspace/DCGM/_out/Linux-amd64-debug/lib/libnvml_injection.so.1.0.0
ENV NVML_INJECTION_MODE=True
ENV PYTHONPATH=/root/Workspace/DCGM/_out/Linux-amd64-debug/share/dcgm_tests
ENV EXPORTER_PORT=9400
ENV NUM_FAKE_GPUS=4
ENV DCGM_DIR=/root/Workspace/DCGM/_out/Linux-amd64-debug
ENV PATH="$PATH:/root/Workspace/DCGM/_out/Linux-amd64-debug/bin"

# Optionally allow mounting external DCGM directory at /dcgm-host
VOLUME ["/dcgm-host"]

EXPOSE 5555 9400

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
