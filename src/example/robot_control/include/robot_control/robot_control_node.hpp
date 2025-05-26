#ifndef ROBOT_CONTROL_NODE_H_
#define ROBOT_CONTROL_NODE_H_

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>

#include <robot_control_interface/action/send_robot_targets.hpp>

#include <moveit/move_group_interface/move_group_interface.hpp>

namespace robot_control {

auto poseToString(const geometry_msgs::msg::Pose &pose) -> std::string;

class RobotControlNode : public rclcpp::Node {

public:
  RobotControlNode();

  auto initialize() -> void;

  using SendRobotTargetsServerHandle = rclcpp_action::ServerGoalHandle<
      robot_control_interface::action::SendRobotTargets>;

private:
  auto handleSendRobotTargetsGoal(
      const rclcpp_action::GoalUUID &uuid,
      std::shared_ptr<
          const robot_control_interface::action::SendRobotTargets::Goal>
          goal) -> rclcpp_action::GoalResponse;

  auto handleSendRobotTargetsCancel(
      std::shared_ptr<SendRobotTargetsServerHandle> goal_handle)
      -> rclcpp_action::CancelResponse;

  void handleSendRobotTargetsAccepted(
      std::shared_ptr<SendRobotTargetsServerHandle> goal_handle);

  void constrains_initialization(const std::string &target_frame);

  std::shared_ptr<moveit::planning_interface::MoveGroupInterface>
      move_group_interface;

  rclcpp_action::Server<robot_control_interface::action::SendRobotTargets>::
      SharedPtr action_server;
  rclcpp::CallbackGroup::SharedPtr action_server_callback_group;
};
} // namespace robot_control

#endif // ROBOT_CONTROL_NODE_H_
