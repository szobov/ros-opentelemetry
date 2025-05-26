cmake_minimum_required(VERSION 3.8)
project(robot_control_interface)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(action_msgs REQUIRED)
find_package(ros_opentelemetry_interfaces REQUIRED)

rosidl_generate_interfaces(${CMAKE_PROJECT_NAME}
  "msg/RobotTarget.msg"
  "action/SendRobotTargets.action"
  DEPENDENCIES
  geometry_msgs

  ros_opentelemetry_interfaces
)

ament_package()
