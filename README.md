# ROS2 OpenTelemetry Integration Library

A production-grade integration library for instrumenting ROS2 (Robot Operating System 2) applications with [OpenTelemetry](https://opentelemetry.io/) distributed tracing and observability capabilities. This project provides a comprehensive toolchain for building, deploying, and monitoring ROS2 workspaces with native OpenTelemetry support for both C++ and Python nodes.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [ROS2 OpenTelemetry Integration Library](#ros2-opentelemetry-integration-library)
  - [How to use this Library](#how-to-use-this-library)
    - [Installation](#installation)
      - [Streamlined](#streamlined)
      - [Classical](#classical)
    - [Instrumenting Code](#instrumenting-code)
      - [Traces](#traces)
      - [Logs](#logs)
  - [Architecture Overview](#architecture-overview)
  - [Example](#example)
    - [Just Command Runner](#just-command-runner)
    - [Prerequisites to build locally](#prerequisites-to-build-locally)
    - [Quick Start](#quick-start)
  - [License](#license)
  - [Contributing](#contributing)

<!-- markdown-toc end -->

## How to use this Library

### Installation

There are two ways how you can use this library.

#### Streamlined

You utilize streamlined approach provided by this library:

You have to use `bin/build-locally.bash` to build your project together with this library. `build-locally.bash` install dependencies using `conan` and `uv` and then runs `colcon` in the `virtualenv` made by `uv`, so your python nodes have access to PyPI packages.
If you switches to this method you'll be able using `conanfile.txt` and `pyproject.toml` files to manage your dependencies.

#### Classical

You install [opentelemetry-sdk](https://opentelemetry.io/docs/languages/) yourself and build it together with the library.

The tricky part is, there is no obvious ways to install PyPI packages so they're available in your ROS2 environment. Plus, for [opentelemetry-cpp](https://github.com/open-telemetry/opentelemetry-cpp/blob/main/INSTALL.md), you would need to follow the installation guide and build it yourself. If you choose this way you would need to add `ros_opentelemetry_py` or `ros_opentelemety_cpp` and `ros_opentelemety_interfaces` from `src/` to your ROS-workspace.

### Instrumenting Code

After you installation you need to instrument your code.

OpenTelemetry provides an extensive [guidance](https://opentelemetry.io/docs/concepts/instrumentation/) on code instrumentation for both [C++](https://opentelemetry.io/docs/languages/cpp/instrumentation/) and [Python](https://opentelemetry.io/docs/languages/python/instrumentation/).

#### Traces

To make integrate it in your node you'd need to the following in C++:

``` c++
#include "ros_opentelemetry_cpp/ros_opentelemetry_cpp.hpp"

std::string otlp_grpc_endpoint = "hostname-of-your-otel-collector:4317";
ros_opentelemetry_cpp::setup_tracer("robot_control", otlp_grpc_endpoint);
```

In Python:

``` python

from ros_opentelemetry_py import setup_tracer

# somewhere on the start of your node
if __name__ == "__main__":
    # Expects environment variable OTLP_ENDPOINT set
    setup_tracer("robot_task_producer")
```

That's the way you connect your [tracers](https://opentelemetry.io/docs/concepts/signals/traces/#tracer) to the [trace collector](https://opentelemetry.io/docs/collector/).

After you can use standard opentelemetry tracers to trace your code.
In C++:

``` c++
#include <opentelemetry/trace/span.h>
#include <opentelemetry/trace/tracer.h>
#include <opentelemetry/trace/provider.h>
#include <opentelemetry/trace/scope.h>


auto tracer = opentelemetry::trace::Provider::GetTracerProvider()->GetTracer(
      "name_of_your_component");
auto span = tracer->StartSpan("handleActionOrServiceOrOtherCallback");
{

    auto target_span = tracer->StartSpan("nested_span");
    opentelemetry::trace::Scope scope(span);
    // your code
}
```

In Python:

``` python
from opentelemetry import trace

tracer: trace.Tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("method_of_your_node")
def method_of_your_node(self, params):
    ...
```

If you want to connect your nodes you'd need to propagate [Trace Context](https://opentelemetry.io/docs/concepts/signals/traces/#context-propagation).

For this you'd need to add `ros_opentelemetry_interfaces` to your `package.xml` for your message package.

``` xml

  <depend>ros_opentelemetry_interfaces</depend>
```

Update your `CMakeLists.txt` to link it and add `TraceMetadata` field to your messages:

``` text
ros_opentelemetry_interfaces/TraceMetadata trace_metadata
```
Then you have to inject trace context into your messages (Action/Service/Topics):

``` python
from ros_opentelemetry_py import inject_trace_context

example_msg = ExampleActionMessage.Goal()
example_msg.trace_metadata = inject_trace_context()
```
and add it extract it in the other node:

``` c++
#include <opentelemetry/context/runtime_context.h>

const auto goal = goal_handle->get_goal();
auto extracted_ctx =
ros_opentelemetry_cpp::extract_trace_context(&goal->trace_metadata);
[[maybe_unused]] auto ctx_token =
      opentelemetry::context::RuntimeContext::Attach(extracted_ctx);

```

After this instrumentation the traces will be connected between two nodes.

#### Logs

To connect traces to the logs, you can use traced loggers:

``` c++
RCLCPP_ERROR_TRACED(this->get_logger(), "logger")
```

``` python
from ros_opentelemetry_py import wrap_logger


self._traced_logger = wrap_logger(self.get_logger())
```

and update the way you collect the logs in your otel-collector:
For example:
``` yaml
receivers:
  filelog:
    include: ["/opt/logs/**/*.log"]
    start_at: end
    multiline:
      line_start_pattern: '^\[\w+\] \[\d+\.\d+\] \[.*\]:'  # To support cases when we output multiline json
    operators:
      - type: regex_parser
        regex: '^\[(?P<level>\w+)\] \[(?P<timestamp>\d+\.\d+)\] \[(?P<source>[^\]]+)\]: (?P<message>.*)$'
        timestamp:
          parse_from: attributes.timestamp
          layout_type: epoch
          layout: "s.ns"
        severity:
          parse_from: attributes.level
      - type: regex_parser
        parse_from: attributes.message
        regex: '^(?:\[trace_id=(?P<trace_id>[0-9a-f]{32})\s+span_id=(?P<span_id>[0-9a-f]{16})\]\s*)?(?P<body>.*)$'

      - type: trace_parser
        trace_id:
          parse_from: attributes.trace_id     # 32-char lowercase hex
        span_id:
          parse_from: attributes.span_id      # 16-char lowercase hex

      - type: move
        from: attributes.body
        to: body

      - type: remove
        field: attributes.message
      - type: remove
        field: attributes.trace_id
      - type: remove
        field: attributes.span_id
```

This way collected logs will be connected to the traces.

## Architecture Overview

This library bridges the gap between ROS2's robotics-focused middleware and OpenTelemetry's observability ecosystem. It enables distributed tracing across heterogeneous ROS2 node graphs, supporting both ament_cmake (C++) and ament_python package types. The architecture leverages:

- **ROS2**: Compatible with multiple ROS2 distributions with improved DDS middleware performance
- **OpenTelemetry SDK**: Industry-standard observability instrumentation for traces, metrics, and logs
- **Conan 2.x**: C++ dependency management with reproducible builds

The library is backend-agnostic and can integrate with any OpenTelemetry-compatible observability platform. Example configurations are provided for [SigNoz](https://github.com/SigNoz/signoz), with [Grafana](https://github.com/grafana/grafana) support planned for future releases.

This project consist of three main packages:

- [ros_opentelemetry_cpp](https://github.com/szobov/ros-opentelemetry/tree/main/src/ros_opentelemetry_cpp) -- C++ package providing a bridge between ROS2 and OpenTelemetry.
- [ros_opentelemetry_py](https://github.com/szobov/ros-opentelemetry/tree/main/src/ros_opentelemetry_py/ros_opentelemetry_py) -- same, but for Python
- [ros_opentelemetry_interfaces](https://github.com/szobov/ros-opentelemetry/tree/main/src/ros_opentelemetry_interfaces) -- ROS2 messages to propagate trace context.

## Example

The library also provides a real world [example](https://github.com/szobov/ros-opentelemetry/tree/main/src/example), utilizing MoveIt2-based C++ RobotControl node and Python's TaskProducer.

### Just Command Runner

This project utilizes [Just](https://github.com/casey/just), a command runner that provides a unified interface for complex development workflows.

Run `just --list` to see all available commands with descriptions.

### Prerequisites to build locally

- [ROS2](https://docs.ros.org/en/rolling/Installation.html)
- [Just](https://just.systems/man/en/packages.html)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [direnv](https://direnv.net/docs/installation.html)

### Quick Start

```bash
# Clone repository
git clone https://github.com/szobov/ros-opentelemetry.git
cd ros-opentelemetry

# Allow direnv to operate environment variable
direnv allow .

just setup-conan

just build-locally

# Update env variables with ROS2' required ones
direnv reload

# To run example telemetry setup
just docker-up-telemetry

# Run example
just docker-up-example
```

## License

Apache-2.0

## Contributing

Contributions are welcome, but keep it mind that this is the open-source project -- maintainer can accept or reject your changes. Please ensure `just check` passes before submitting pull requests.
