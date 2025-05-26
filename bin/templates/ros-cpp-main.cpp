// __PROJECT_NAME__ executable example
#include <chrono>
#include <memory>
#include <rclcpp/rclcpp.hpp>

using namespace std::chrono_literals;

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("__PROJECT_NAME__");
  auto timer = node->create_wall_timer(1s, [node]() {
    RCLCPP_INFO(node->get_logger(), "Hello from __PROJECT_NAME__");
  });
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}

