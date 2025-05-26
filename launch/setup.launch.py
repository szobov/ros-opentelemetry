import sys
from typing import Any

from launch_ros.actions import Node

from launch import LaunchDescription
from launch.actions import (
    LogInfo,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit

restart_attempts: dict[str, int] = {}
MAX_RESTARTS: int = 5


def create_node_with_restarts(
    package: str, executable: str, parameters: list[dict[str, Any]]
) -> list[Any]:
    node = Node(package=package, executable=executable, parameters=parameters)
    event_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=node,
            on_exit=attempt_restart(node, package, executable, parameters),
        )
    )
    return [node, event_handler]


def attempt_restart(
    node: Node, package: str, executable: str, parameters: list[dict[str, Any]]
) -> Any:
    del node

    def handler(event: Any, context: Any) -> list[Any]:
        del event, context
        restart_attempts[executable] = restart_attempts.get(executable, 0) + 1
        if restart_attempts[executable] > MAX_RESTARTS:
            sys.exit(1)
        return [
            LogInfo(
                msg=f"Restarting node {executable} (attempt {restart_attempts[executable]}/{MAX_RESTARTS})"
            ),
            *create_node_with_restarts(package, executable, parameters),
        ]

    return handler


def generate_launch_description() -> LaunchDescription:
    nodes = []
    for package, executable, parameters in [
        ("planner", "sample_application", [{"test": True}]),
    ]:
        nodes.extend(create_node_with_restarts(package, executable, parameters))

    env_variables = []

    return LaunchDescription(nodes + env_variables)
