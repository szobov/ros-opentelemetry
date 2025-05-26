#include "robot_control/robot_control_node.hpp"

auto main(int argc, char **argv) -> int {

  rclcpp::init(argc, argv);

  auto node = std::make_shared<robot_control::RobotControlNode>();
  node->initialize();

  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();
  return 0;
}
