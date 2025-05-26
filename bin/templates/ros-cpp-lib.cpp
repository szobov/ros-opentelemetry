#include "__PROJECT_NAME__/__PROJECT_NAME__.hpp"
#include <rclcpp/rclcpp.hpp>

namespace __PROJECT_NAME__ {

// Example usage point to keep the library linked with rclcpp
void example_log(rclcpp::Logger logger) {
  RCLCPP_INFO(logger, "%s", greet().c_str());
}

} // namespace __PROJECT_NAME__

