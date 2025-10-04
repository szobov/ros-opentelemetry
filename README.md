# ROS2 OpenTelemetry Integration Library

A production-grade integration library for instrumenting ROS2 (Robot Operating System 2) applications with OpenTelemetry distributed tracing and observability capabilities. This project provides a comprehensive toolchain for building, deploying, and monitoring ROS2 workspaces with native OpenTelemetry support for both C++ and Python nodes.

## Architecture Overview

This library bridges the gap between ROS2's robotics-focused middleware and OpenTelemetry's observability ecosystem. It enables distributed tracing across heterogeneous ROS2 node graphs, supporting both ament_cmake (C++) and ament_python package types. The architecture leverages:

- **ROS2**: Compatible with multiple ROS2 distributions with improved DDS middleware performance
- **OpenTelemetry SDK**: Industry-standard observability instrumentation for traces, metrics, and logs
- **Conan 2.x**: C++ dependency management with reproducible builds
- **Colcon**: ROS2-native meta-build system orchestrating multiple package types
- **Backend-agnostic**: Works with any OpenTelemetry-compatible backend (SigNoz, Grafana, Jaeger, etc.)
- **Docker Compose**: Containerized telemetry infrastructure and example deployments

The library is backend-agnostic and can integrate with any OpenTelemetry-compatible observability platform. Example configurations are provided for SigNoz, with Grafana support planned for future releases.

The library supports local development workflows with isolated workspaces, containerized deployments for reproducibility, and comprehensive linting/formatting pipelines for maintaining code quality across polyglot codebases.

## Just Command Runner

This project utilizes [Just](https://github.com/casey/just), a command runner that provides a unified interface for complex development workflows.

### Key Commands

- **`just build-locally`** - Build the ROS2 workspace locally
- **`just check`** - Run linters and formatters
- **`just run-example-with-telemetry`** - Run example with full telemetry stack

Run `just --list` to see all available commands with descriptions.

## Prerequisites

- **ROS2**: Install from [ros.org](https://docs.ros.org/en/rolling/Installation.html)
- **Just**: Install via `cargo install just` or package manager
- **Docker & Docker Compose**: For containerized workflows
- **UV**: Python package installer (`pip install uv`)
- **Conan**: C++ package manager (`pip install conan`)
- **direnv** (optional): Automatic environment activation

## Quick Start

```bash
# Clone repository
git clone https://github.com/szobov/ros-opentelemetry.git
cd ros-opentelemetry

# Setup C++ dependencies
just setup-conan

# Build ROS2 workspace
just build-locally

# Source environment (or use direnv)
source local_workspace/install/setup.bash

# Run with telemetry
just run-example-with-telemetry
```

Access SigNoz UI at `http://localhost:8181` to observe distributed traces across ROS2 nodes.

## Development Workflow

1. **Create new package**: Use `just add-ros-python-package` or `just add-ros-cpp-package`
2. **Implement node logic**: Add OpenTelemetry instrumentation using provided libraries
3. **Build iteratively**: Run `just build-locally` after changes
4. **Validate code quality**: Execute `just check` before committing
5. **Test with telemetry**: Launch with `just run-example-with-telemetry` to verify traces

## Project Structure

```
.
├── Justfile                    # Command runner recipes
├── bin/                        # Build scripts and templates
├── src/                        # ROS2 packages
│   ├── ros_opentelemetry_cpp/  # C++ telemetry library
│   ├── ros_opentelemetry_py/   # Python telemetry library
│   ├── ros_opentelemetry_interfaces/ # ROS2 message definitions
│   └── example/                # Instrumented example nodes
├── telemetry_services/         # SigNoz deployment configs
├── docker/                     # Containerization configs
└── launch/                     # ROS2 launch files

```

## Telemetry Integration

The library provides native ROS2 wrappers around OpenTelemetry SDKs, enabling automatic context propagation across topic publications and service calls. Instrumented nodes emit traces with semantic conventions aligned to robotics workflows, including topic names, message types, and node lifecycle events.

Traces are exported via OTLP to the collector, which batches and forwards them to your chosen backend for storage and visualization. The architecture supports sampling strategies, custom trace attributes, and correlation with ROS2 logs through trace context injection.

## License

Apache-2.0

## Contributing

Contributions are welcome. Please ensure `just check` passes before submitting pull requests.
