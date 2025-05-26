from __future__ import annotations

import math
import random
from collections.abc import Iterable

import rclpy
from geometry_msgs.msg import Pose
from opentelemetry import trace
from rclpy.action import ActionClient
from rclpy.node import Node
from robot_control_interface.action import SendRobotTargets
from robot_control_interface.msg import RobotTarget

from ros_opentelemetry_py import inject_trace_context, setup_tracer, wrap_logger

tracer: trace.Tracer = trace.get_tracer(__name__)


def make_pose(x: float, y: float, z: float, yaw: float = 0.0) -> Pose:
    pose = Pose()
    pose.position.x = float(x)
    pose.position.y = float(y)
    pose.position.z = float(z)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    pose.orientation.x = 0.0
    pose.orientation.y = 0.0
    pose.orientation.z = sy
    pose.orientation.w = cy
    return pose


class RobotTaskProducer(Node):
    def __init__(self) -> None:
        super().__init__("robot_task_producer")

        self._client: ActionClient = ActionClient(
            self, SendRobotTargets, "send_robot_targets"
        )
        self._traced_logger = wrap_logger(self.get_logger())

    def _wait_for_server(self) -> bool:
        while rclpy.ok():
            if self._client.wait_for_server(timeout_sec=1.0):
                return True
            self.get_logger().info("Waiting for action server send_robot_targets ...")
        return False

    @tracer.start_as_current_span("send_targets")
    def send_targets(self, targets: Iterable[RobotTarget]) -> None:
        if not self._wait_for_server():
            return

        goal_msg = SendRobotTargets.Goal()
        goal_msg.targets = list(targets)

        goal_msg.trace_metadata = inject_trace_context()

        self._traced_logger.info(
            f"Sending {len(goal_msg.targets)} targets to robot_control"
        )

        send_future = self._client.send_goal_async(
            goal_msg, feedback_callback=self._on_feedback
        )

        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        if not goal_handle.accepted:
            self._traced_logger.warn("Goal rejected")
            return

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result().result  # type: ignore[attr-defined]

        self._traced_logger.info(
            f"Completed: success={result.success}, statuses={list(result.targets_status)}"
        )

    def _on_feedback(self, feedback_msg: SendRobotTargets.FeedbackMessage) -> None:
        fb = feedback_msg.feedback
        self._traced_logger.info(
            f"Feedback: current_target_id={fb.current_target_id} status={fb.status}"
        )


def generate_tasks() -> list[RobotTarget]:
    base = (0.6, 1.0, 0.8, 0.0)
    bx, by, bz, byaw = base
    targets: list[RobotTarget] = []
    for idx in range(random.randint(1, 5)):
        dx = random.uniform(-0.25, 0.25)
        dy = random.uniform(-0.25, 0.25)
        dz = random.uniform(-0.25, 0.25)
        dyaw = random.uniform(-0.2, 0.2)
        pose = make_pose(bx + dx, by + dy, bz + dz, byaw + dyaw)
        targets.append(RobotTarget(target_id=idx, target_pose=pose))
    return targets


def main() -> None:
    setup_tracer("robot_task_producer")
    rclpy.init()

    node = RobotTaskProducer()

    try:
        while rclpy.ok():
            node.send_targets(generate_tasks())
    finally:
        node.destroy_node()
        rclpy.shutdown()
