# ROS2 OpenTelemetry Integration Framework

A production-grade integration framework for instrumenting ROS2 (Robot Operating System 2) applications with OpenTelemetry distributed tracing and observability capabilities. This project provides a comprehensive toolchain for building, deploying, and monitoring ROS2 workspaces with native OpenTelemetry support for both C++ and Python nodes.

## Architecture Overview

This framework bridges the gap between ROS2's robotics-focused middleware and OpenTelemetry's observability ecosystem. It enables distributed tracing across heterogeneous ROS2 node graphs, supporting both ament_cmake (C++) and ament_python package types. The architecture leverages:

- **ROS2 Jazzy**: Latest ROS2 distribution with improved DDS middleware performance
- **OpenTelemetry SDK**: Industry-standard observability instrumentation for traces, metrics, and logs
- **Conan 2.x**: C++ dependency management with reproducible builds
- **Colcon**: ROS2-native meta-build system orchestrating multiple package types
- **SigNoz**: OpenTelemetry-native application performance monitoring backend
- **Docker Compose**: Containerized telemetry infrastructure and example deployments

The framework supports local development workflows with isolated workspaces, containerized deployments for reproducibility, and comprehensive linting/formatting pipelines for maintaining code quality across polyglot codebases.

## Just Command Runner

This project utilizes [Just](https://github.com/casey/just), a command runner that provides a unified interface for complex development workflows. Just recipes are defined in the `Justfile` and abstract multi-step operations involving shell scripts, Docker orchestration, and ROS2 toolchain invocations. Unlike traditional Makefiles, Just focuses on command execution rather than dependency-based builds, offering clearer syntax and better ergonomics for development automation.

### Available Commands

#### Build and Development

**`just build-locally`**  
Constructs the ROS2 workspace locally with the `local_` prefix. Invokes the complete build pipeline: Python dependency installation via UV, C++ dependency resolution through Conan, symlink creation for source packages, rosdep dependency installation, and colcon build with CMake export flags for IDE integration.

**`just build-docker`**  
Similar to `build-locally` but uses the `docker_` workspace prefix for containerized build artifacts. Useful for validating builds in controlled environments.

**`just setup-conan`**  
Initializes Conan package manager by detecting system profile and configuring the ConAn Center remote repository endpoint. Required before building C++ packages with external dependencies.

#### Code Quality

**`just check`**  
Executes the complete linting and formatting pipeline. Runs Ruff formatter in validation mode (exits on formatting violations), Ruff linter with auto-fix enabled, and invokes the C++ linting pipeline (clang-tidy, clang-format) via `bin/run-cpp-linters.bash`.

#### Dependency Management

**`just generate-ros-dep-txt`**  
Generates `rosdep-deps.txt` by resolving all ROS2 package dependencies through rosdep. Runs a disposable ROS2 container to query and resolve dependencies, updating the file only if changes are detected. This ensures reproducible builds by pinning system dependencies.

#### Docker and Telemetry

**`just docker-build-example`**  
Builds the example ROS2 application in a Docker container after generating rosdep dependencies. Orchestrates multi-stage Docker builds through docker-compose.

**`just docker-up-telemetry`**  
Deploys the SigNoz observability stack (OpenTelemetry collector, query service, and UI) using docker-compose. Exposes OTLP endpoints (4317 for gRPC, 4318 for HTTP) for receiving telemetry data.

**`just run-example-with-telemetry`**  
End-to-end workflow that starts the telemetry infrastructure, builds example containers, and launches two instrumented ROS2 node instances. Demonstrates distributed tracing across multiple nodes communicating through the same ROS2 graph. SigNoz UI becomes available at `http://localhost:8181`.

#### Package Scaffolding

**`just add-ros-python-package <package> [path="src"]`**  
Scaffolds a new ament_python ROS2 package with proper directory structure. Creates package using ros2 CLI tools, removes default boilerplate tests, and applies project-specific templates for `setup.py` and `pyproject.toml` with dependency management configured.

**`just add-ros-cpp-package <package> [type="exe"] [path="src"]`**  
Scaffolds a new ament_cmake ROS2 package with either executable (`type="exe"`) or library (`type="lib"`) configuration. Generates appropriate CMakeLists.txt, package.xml, and source file templates. Includes Conan configuration for C++ dependency management and proper header inclusion structure.

## Prerequisites

- **ROS2 Jazzy**: Install from [ros.org](https://docs.ros.org/en/jazzy/Installation.html)
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

The framework provides native ROS2 wrappers around OpenTelemetry SDKs, enabling automatic context propagation across topic publications and service calls. Instrumented nodes emit traces with semantic conventions aligned to robotics workflows, including topic names, message types, and node lifecycle events.

Traces are exported via OTLP to the collector, which batches and forwards them to SigNoz for storage and visualization. The architecture supports sampling strategies, custom trace attributes, and correlation with ROS2 logs through trace context injection.

## License

Apache-2.0

## Contributing

Contributions are welcome. Please ensure `just check` passes before submitting pull requests.
