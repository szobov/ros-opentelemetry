from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description() -> LaunchDescription:
    robot_control_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(
                Path(get_package_share_directory("robot_control"))
                / "launch"
                / "bringup.launch.py"
            )
        )
    )

    producer_node = Node(
        package="robot_task_producer",
        executable="robot_task_producer",
        output="screen",
    )

    return LaunchDescription(
        [
            robot_control_bringup,
            producer_node,
        ]
    )
