# ROS2 OpenTelemetry Integration Library

A production-grade integration library for instrumenting ROS2 (Robot Operating System 2) applications with [OpenTelemetry](https://opentelemetry.io/) distributed tracing and observability capabilities. This project provides a comprehensive toolchain for building, deploying, and monitoring ROS2 workspaces with native OpenTelemetry support for both C++ and Python nodes.

## Architecture Overview

This library bridges the gap between ROS2's robotics-focused middleware and OpenTelemetry's observability ecosystem. It enables distributed tracing across heterogeneous ROS2 node graphs, supporting both ament_cmake (C++) and ament_python package types. The architecture leverages:

- **ROS2**: Compatible with multiple ROS2 distributions with improved DDS middleware performance
- **OpenTelemetry SDK**: Industry-standard observability instrumentation for traces, metrics, and logs
- **Conan 2.x**: C++ dependency management with reproducible builds

The library is backend-agnostic and can integrate with any OpenTelemetry-compatible observability platform. Example configurations are provided for SigNoz, with Grafana support planned for future releases.

## Example

The library also provides a real world example, utilizing MoveIt2-based C++ RobotControl node and Python's TaskProducer.

## Just Command Runner

This project utilizes [Just](https://github.com/casey/just), a command runner that provides a unified interface for complex development workflows.

Run `just --list` to see all available commands with descriptions.

## Prerequisites to build locally

- [ROS2](https://docs.ros.org/en/rolling/Installation.html)
- [Just](https://just.systems/man/en/packages.html)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [direnv](https://direnv.net/docs/installation.html)

## Quick Start

```bash
# Clone repository
git clone https://github.com/szobov/ros-opentelemetry.git
cd ros-opentelemetry

# Allow direnv to operate environment variable
direnv allow .

just setup-conan

just build-locally

# To run example telemetry setup
just docker-up-telemetry

# Run exampe
just docker-up-example
```

Access SigNoz UI at `http://localhost:8181` to observe distributed traces across ROS2 nodes.

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
