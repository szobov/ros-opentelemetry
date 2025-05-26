#include <string>
#include <utility>

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>

#include "ros_opentelemetry_cpp/ros_opentelemetry_cpp.hpp"
#include <moveit/move_group_interface/move_group_interface.hpp>
#include <moveit_core/moveit/utils/moveit_error_code.hpp>
#include <opentelemetry/context/runtime_context.h>
#include <opentelemetry/trace/provider.h>
#include <opentelemetry/trace/scope.h>
#include <opentelemetry/trace/span.h>
#include <opentelemetry/trace/tracer.h>

#include "robot_control/robot_control_node.hpp"

namespace robot_control {

RobotControlNode::RobotControlNode()
    : rclcpp::Node(
          "robot_control",
          rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(
              true)) {}

auto RobotControlNode::initialize() -> void {
  std::string planning_group_default = "kuka_robot";
  std::string target_frame_default = "base_link";
  std::string otlp_grpc_endpoint;

  std::string planning_group = planning_group_default;
  if (!this->has_parameter("planning_group")) {
    this->declare_parameter<std::string>("planning_group",
                                         planning_group_default);
  } else {
    this->get_parameter("planning_group", planning_group);
  }

  std::string target_frame = target_frame_default;
  if (!this->has_parameter("target_frame")) {
    this->declare_parameter<std::string>("target_frame", target_frame_default);
  } else {
    this->get_parameter("target_frame", target_frame);
  }

  this->get_parameter("otlp_grpc_endpoint", otlp_grpc_endpoint);
  if (!otlp_grpc_endpoint.empty()) {
    ros_opentelemetry_cpp::setup_tracer("robot_control", otlp_grpc_endpoint);
  } else {
    ros_opentelemetry_cpp::setup_tracer("robot_control", std::nullopt);
  }

  this->move_group_interface =
      std::make_shared<moveit::planning_interface::MoveGroupInterface>(
          this->shared_from_this(), planning_group);
  this->constrains_initialization(target_frame);

  this->action_server_callback_group =
      this->create_callback_group(rclcpp::CallbackGroupType::MutuallyExclusive);

  rcl_action_server_options_t action_options =
      rcl_action_server_get_default_options();

  this->action_server = rclcpp_action::create_server<
      robot_control_interface::action::SendRobotTargets>(
      this, "send_robot_targets",
      [this](auto &&PH1, auto &&PH2) {
        return handleSendRobotTargetsGoal(std::forward<decltype(PH1)>(PH1),
                                          std::forward<decltype(PH2)>(PH2));
      },
      [this](auto &&PH1) {
        return handleSendRobotTargetsCancel(std::forward<decltype(PH1)>(PH1));
      },
      [this](auto &&PH1) {
        return handleSendRobotTargetsAccepted(std::forward<decltype(PH1)>(PH1));
      },
      action_options, this->action_server_callback_group);
  RCLCPP_INFO(this->get_logger(), "Node has been started.");
}

void RobotControlNode::constrains_initialization(
    const std::string &target_frame) {
  this->move_group_interface->setPoseReferenceFrame(target_frame);
  this->move_group_interface->setNumPlanningAttempts(10);
  this->move_group_interface->setPlanningTime(5.0);
  this->move_group_interface->setGoalPositionTolerance(0.001);
  this->move_group_interface->setGoalOrientationTolerance(0.05);
  this->move_group_interface->setEndEffectorLink("tool0");
}

auto RobotControlNode::handleSendRobotTargetsGoal(
    const rclcpp_action::GoalUUID & /* uuid */,
    std::shared_ptr<
        const robot_control_interface::action::SendRobotTargets::Goal>
        goal) -> rclcpp_action::GoalResponse {

  if (!goal || goal->targets.empty()) {
    RCLCPP_WARN(this->get_logger(), "Goal is rejected: no targets");
    return rclcpp_action::GoalResponse::REJECT;
  }
  RCLCPP_INFO(this->get_logger(), "Goal is accepted");
  return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
}

auto RobotControlNode::handleSendRobotTargetsCancel(
    std::shared_ptr<SendRobotTargetsServerHandle> /*goal_handle*/)
    -> rclcpp_action::CancelResponse {
  RCLCPP_INFO(this->get_logger(), "Cancel requested.");
  return rclcpp_action::CancelResponse::ACCEPT;
}

void RobotControlNode::handleSendRobotTargetsAccepted(
    std::shared_ptr<SendRobotTargetsServerHandle> goal_handle) {

  const auto goal = goal_handle->get_goal();
  auto extracted_ctx =
      ros_opentelemetry_cpp::extract_trace_context(&goal->trace_metadata);
  [[maybe_unused]] auto ctx_token =
      opentelemetry::context::RuntimeContext::Attach(extracted_ctx);

  auto tracer = opentelemetry::trace::Provider::GetTracerProvider()->GetTracer(
      "robot_control");

  auto span = tracer->StartSpan("handleSendRobotTargetsAccepted");

  RCLCPP_INFO_TRACED(this->get_logger(), "Processing <%lu> targets",
                     goal->targets.size());

  auto result = std::make_shared<
      robot_control_interface::action::SendRobotTargets::Result>();
  auto feedback = std::make_shared<
      robot_control_interface::action::SendRobotTargets::Feedback>();

  const auto &targets = goal->targets;

  opentelemetry::trace::Scope scope(span);

  std::vector<bool> targets_status(targets.size(), false);

  std::size_t target_index = 0;
  for (const auto &target : targets) {
    const auto current_index = target_index;
    feedback->current_target_id = current_index;
    target_index++;

    if (goal_handle->is_canceling()) {
      result->success = false;
      result->targets_status = targets_status;
      goal_handle->canceled(result);
      return;
    }

    auto target_span = tracer->StartSpan("plan_and_execute");
    opentelemetry::trace::Scope target_scope(target_span);

    this->move_group_interface->setPoseTarget(target.target_pose);
    moveit::planning_interface::MoveGroupInterface::Plan plan;

    bool has_planned = false;
    {
      auto plan_span = tracer->StartSpan("plan");
      opentelemetry::trace::Scope plan_scope(plan_span);
      const auto planning_result = this->move_group_interface->plan(plan);
      has_planned = planning_result == moveit::core::MoveItErrorCode::SUCCESS;
      if (!has_planned) {
        RCLCPP_ERROR_TRACED(
            this->get_logger(),
            "Planning failed: %s, target_id: <%lu>, pose: %s",
            moveit::core::errorCodeToString(planning_result).c_str(),
            current_index, poseToString(target.target_pose).c_str());
        plan_span->SetStatus(opentelemetry::trace::StatusCode::kError,
                             "planning failed");
        targets_status[current_index] = has_planned;
        feedback->status = has_planned;
        goal_handle->publish_feedback(feedback);
      } else {
        plan_span->SetStatus(opentelemetry::trace::StatusCode::kOk);
      }
    }
    if (!has_planned) {
      continue;
    }

    bool has_executed = false;
    {
      auto exec_span = tracer->StartSpan("execute");
      opentelemetry::trace::Scope exec_scope(exec_span);
      const auto execution_result = this->move_group_interface->execute(plan);
      has_executed = execution_result == moveit::core::MoveItErrorCode::SUCCESS;
      if (!has_executed) {
        RCLCPP_ERROR_TRACED(
            this->get_logger(), "Execution failed: %s, target_id: %lu",
            moveit::core::errorCodeToString(execution_result).c_str(),
            current_index);
        exec_span->SetStatus(opentelemetry::trace::StatusCode::kError,
                             "execution failed");
      } else {
        exec_span->SetStatus(opentelemetry::trace::StatusCode::kOk);
      }
    }
    targets_status[current_index] = has_executed;

    feedback->status = has_executed;
    goal_handle->publish_feedback(feedback);
  }

  result->success = std::all_of(targets_status.begin(), targets_status.end(),
                                [](bool value) { return value; });
  result->targets_status = targets_status;

  if (goal_handle->is_canceling()) {
    goal_handle->canceled(result);
    return;
  }
  goal_handle->succeed(result);
  RCLCPP_INFO_TRACED(this->get_logger(), "Finished processing of <%lu> targets",
                     goal->targets.size());
}

auto poseToString(const geometry_msgs::msg::Pose &pose) -> std::string {
  std::stringstream sstream;
  sstream << "Position: (" << pose.position.x << ", " << pose.position.y << ", "
          << pose.position.z << "), "
          << "Orientation: (" << pose.orientation.x << ", "
          << pose.orientation.y << ", " << pose.orientation.z << ", "
          << pose.orientation.w << ")";
  return sstream.str();
}
} // namespace robot_control
