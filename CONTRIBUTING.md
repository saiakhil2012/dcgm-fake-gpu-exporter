# Contributing to DCGM Fake GPU Exporter

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Getting Started

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   git clone https://github.com/YOUR_USERNAME/dcgm-fake-gpu-exporter.git
   cd dcgm-fake-gpu-exporter
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

## Development Workflow

### Building and Testing

```bash
# Build the Docker image
./build-smart.sh

# Test your changes
docker-compose up -d
curl http://localhost:9400/metrics

# Test specific profiles
docker run -d -p 9400:9400 -e METRIC_PROFILE=wave dcgm-fake-gpu-exporter:latest

# Check logs
docker logs dcgm-exporter
```

### Code Style

- **Python**: Follow PEP 8 guidelines
- **Shell scripts**: Use shellcheck for validation
- **Docker**: Follow Docker best practices (multi-stage builds, minimal layers)
- **Documentation**: Keep README.md and inline comments up to date

### Testing Your Changes

Before submitting a PR, ensure:

1. **Docker image builds successfully**
   ```bash
   ./build-smart.sh
   ```

2. **Container starts and runs**
   ```bash
   docker-compose up -d
   sleep 15
   docker ps | grep dcgm-exporter
   ```

3. **Metrics are exposed**
   ```bash
   curl -s http://localhost:9400/metrics | grep dcgm_gpu_temp
   ```

4. **No errors in logs**
   ```bash
   docker logs dcgm-exporter
   ```

5. **Test all metric profiles** (if changing metric logic)
   ```bash
   for profile in static stable spike wave degrading faulty chaos; do
     echo "Testing profile: $profile"
     docker run -d -p 9400:9400 -e METRIC_PROFILE=$profile dcgm-fake-gpu-exporter:latest
     sleep 10
     curl -s http://localhost:9400/metrics | head -20
     docker stop $(docker ps -q --filter ancestor=dcgm-fake-gpu-exporter:latest)
   done
   ```

## Types of Contributions

### Bug Fixes
- Check existing issues first
- Include reproduction steps
- Add tests if possible

### New Features
- Open an issue first to discuss
- Update documentation
- Add examples if applicable

### Documentation
- Fix typos and improve clarity
- Add examples and use cases
- Update diagrams and screenshots

### Performance Improvements
- Benchmark before and after
- Document the improvement
- Consider backward compatibility

## Submitting Changes

1. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new metric profile for X"
   # or
   git commit -m "fix: resolve issue with GPU creation"
   ```

   Use conventional commit messages:
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `docs:` - Documentation changes
   - `perf:` - Performance improvements
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

2. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template
   - Link any related issues

## Pull Request Guidelines

- **One feature per PR**: Keep PRs focused on a single change
- **Update documentation**: Include relevant README updates
- **Test thoroughly**: Ensure all tests pass
- **Clean commit history**: Squash commits if needed
- **Respond to feedback**: Address review comments promptly

## Development Tips

### Working with DCGM Binaries

If you don't have DCGM binaries:
```bash
# Use the from-image build method
./build-smart.sh --from-image
```

### Testing on ARM Macs (M1/M2/M3)

```bash
# Build for AMD64 explicitly
docker build --platform linux/amd64 -t dcgm-fake-gpu-exporter .

# Run with platform specified
docker run --platform linux/amd64 -p 9400:9400 dcgm-fake-gpu-exporter:latest
```

### Debugging Container Issues

```bash
# Get a shell in the container
docker run -it --entrypoint /bin/bash dcgm-fake-gpu-exporter:latest

# Check DCGM binaries
ls -la /root/Workspace/DCGM/_out/Linux-amd64-debug/bin/

# Test nv-hostengine manually
/root/Workspace/DCGM/_out/Linux-amd64-debug/bin/nv-hostengine -f /tmp/nv-hostengine.log
```

### Adding New Metric Profiles

1. Edit `dcgm_fake_manager.py`
2. Add profile to `METRIC_PROFILES` dict
3. Update `README.md` with profile documentation
4. Test with various GPU counts
5. Add example to `examples/`

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Questions?

- Open a [GitHub Discussion](https://github.com/saiakhil2012/dcgm-fake-gpu-exporter/discussions)
- Create an [issue](https://github.com/saiakhil2012/dcgm-fake-gpu-exporter/issues) for bugs or features

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
