FROM ghcr.io/astral-sh/uv:0.8.22 AS uv

FROM ros:jazzy-ros-base

ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    WORKSPACE_PREFIX=docker_ \
    PATH="/usr/local/bin:/workspace/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git \
    build-essential clang cmake pkg-config \
    just \
  && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /usr/local/bin/uv

COPY ./rosdep-deps.txt ./rosdep-deps.txt

RUN apt-get update && \
    xargs apt-get install -y < ./rosdep-deps.txt && \
    rm -rf /var/lib/apt/lists/*

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON=python3.12

WORKDIR /workspace

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --inexact

COPY . /workspace

SHELL ["/bin/bash","-lc"]

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.conan2 \
    source /opt/ros/jazzy/setup.bash && \
    source /workspace/.venv/bin/activate && \
    just setup-conan build-docker

RUN chown -R ${USER_UID}:${USER_GID} /workspace

USER ${USER_UID}

ENV OTLP_ENDPOINT=host.docker.internal:4317

# Entrypoint: run the project using ros2 launch
CMD source /opt/ros/jazzy/setup.bash && \
    source /workspace/.venv/bin/activate && \
    source /workspace/docker_workspace/install/setup.bash && \
    source /workspace/docker_workspace/install/local_setup.bash &&\
    source /workspace/docker_workspace/install/conanrosenv.sh && \
    ros2 launch launch/bringup_with_producer.launch.py otlp_grpc_endpoint:=${OTLP_ENDPOINT}
