# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please send an email to the maintainer or create a private security advisory on GitHub.

**Please do not disclose security vulnerabilities publicly until they have been addressed.**

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

## Security Considerations

### Container Security

This project creates Docker containers with simulated GPU metrics. Consider:

1. **Network Exposure**: Only expose ports 9400 and 5555 if needed
   ```bash
   # Bind to localhost only
   docker run -p 127.0.0.1:9400:9400 dcgm-fake-gpu-exporter
   ```

2. **Resource Limits**: Set container resource limits
   ```yaml
   services:
     dcgm-exporter:
       deploy:
         resources:
           limits:
             cpus: '1'
             memory: 1G
   ```

3. **Read-only Filesystem**: Run with read-only root filesystem when possible
   ```bash
   docker run --read-only -p 9400:9400 dcgm-fake-gpu-exporter
   ```

### GitHub Container Registry

When pulling images:

1. Verify image signatures
2. Use specific tags instead of `latest` in production
3. Scan images for vulnerabilities

```bash
# Pull specific version
docker pull ghcr.io/saiakhil2012/dcgm-fake-gpu-exporter:v1.0.0

# Scan for vulnerabilities
docker scan ghcr.io/saiakhil2012/dcgm-fake-gpu-exporter:latest
```

### Environment Variables

Be cautious with environment variables:

- Don't store secrets in `docker-compose.yml`
- Use `.env` files (added to `.gitignore`)
- Never commit tokens or credentials

### DCGM Binaries

The DCGM binaries are:
- Licensed under Apache 2.0
- Provided by NVIDIA Corporation
- Not modified by this project
- Used according to their license terms

## Best Practices

1. **Development/Testing Only**: This tool is for development and testing, not production GPU monitoring
2. **Network Isolation**: Use Docker networks to isolate containers
3. **Regular Updates**: Keep Docker and dependencies updated
4. **Least Privilege**: Run containers with minimal required permissions

## Known Limitations

- Simulated metrics only (not real GPU data)
- Platform-specific (Linux x86-64)
- Requires Docker for containerization

---

For questions about security, please open a [GitHub Discussion](https://github.com/saiakhil2012/dcgm-fake-gpu-exporter/discussions).
