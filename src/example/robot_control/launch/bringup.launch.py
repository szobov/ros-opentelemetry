import os
from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    pkg_share = Path(get_package_share_directory("robot_control"))
    config_dir = pkg_share / "config"

    moveit_config = (
        MoveItConfigsBuilder("kuka_kr210", package_name="robot_control")
        .robot_description(
            file_path=str(config_dir / "kuka_kr210.urdf.xacro"),
            mappings={
                "initial_positions_file": str(config_dir / "initial_positions.yaml"),
            },
        )
        .robot_description_semantic(file_path=str(config_dir / "kuka_kr210.srdf"))
        .robot_description_kinematics(file_path=str(config_dir / "kinematics.yaml"))
        .trajectory_execution(file_path=str(config_dir / "moveit_controllers.yaml"))
        .to_moveit_configs()
    )

    with open(config_dir / "joint_limits.yaml", encoding="utf-8") as f:
        robot_description_planning = yaml.safe_load(f)

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[moveit_config.robot_description],
        output="screen",
    )

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"robot_description_planning": robot_description_planning},
        ],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", str(config_dir / "moveit.rviz")],
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
            {"robot_description_planning": robot_description_planning},
        ],
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            moveit_config.robot_description,
            str(config_dir / "ros2_controllers.yaml"),
        ],
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )
    kuka_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["kuka_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    robot_control_node = Node(
        package="robot_control",
        executable="robot_control",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            {"robot_description_planning": robot_description_planning},
            {"planning_group": "kuka_robot"},
            {"target_frame": "base_link"},
            {"otlp_grpc_endpoint": os.getenv("OTLP_ENDPOINT")},
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            robot_state_publisher,
            move_group,
            rviz,
            ros2_control_node,
            joint_state_broadcaster_spawner,
            kuka_controller_spawner,
            robot_control_node,
        ]
    )
