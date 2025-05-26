cmake_minimum_required(VERSION 3.22)
project(robot_control)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(${CMAKE_PROJECT_NAME}_interface REQUIRED)
find_package(rclcpp REQUIRED)

find_package(ros_opentelemetry_cpp REQUIRED)
find_package(opentelemetry-cpp CONFIG REQUIRED)
find_package(ros_opentelemetry_interfaces REQUIRED)


include_directories(
  include
  ${rclcpp_INCLUDE_DIRS}
)

add_library(${CMAKE_PROJECT_NAME}_lib SHARED src/robot_control_node.cpp)

add_executable(${CMAKE_PROJECT_NAME} src/robot_control.cpp)


target_include_directories(${CMAKE_PROJECT_NAME}_lib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/${CMAKE_PROJECT_NAME}>
  
  ${OPENTELEMETRY_CPP_INCLUDE_DIRS}
)

target_link_libraries(${CMAKE_PROJECT_NAME}
  PRIVATE
  ${CMAKE_PROJECT_NAME}_lib
  opentelemetry-cpp::opentelemetry-cpp
)

target_compile_features(${CMAKE_PROJECT_NAME} PUBLIC c_std_99 cxx_std_17)

ament_target_dependencies(
  ${CMAKE_PROJECT_NAME}_lib
  ${CMAKE_PROJECT_NAME}_interface
  ros_opentelemetry_cpp

  moveit_ros_planning_interface
  rclcpp
)



install(TARGETS ${CMAKE_PROJECT_NAME}
  DESTINATION lib/${CMAKE_PROJECT_NAME})

if(BUILD_TESTING)
endif()

ament_package()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch")
  install(
    DIRECTORY launch
    DESTINATION share/${CMAKE_PROJECT_NAME}
    PATTERN "setup_assistant.launch" EXCLUDE)
endif()

install(DIRECTORY config DESTINATION share/${CMAKE_PROJECT_NAME})
install(FILES .setup_assistant DESTINATION share/${CMAKE_PROJECT_NAME})
