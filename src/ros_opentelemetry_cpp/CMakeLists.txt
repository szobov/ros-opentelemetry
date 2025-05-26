cmake_minimum_required(VERSION 3.22)
project(ros_opentelemetry_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ros_opentelemetry_interfaces)

include(${CMAKE_BINARY_DIR}/conan_toolchain.cmake OPTIONAL)

find_package(opentelemetry-cpp CONFIG REQUIRED COMPONENTS exporters_otlp_grpc)

add_library(${PROJECT_NAME} src/ros_opentelemetry_cpp.cpp)

target_include_directories(${PROJECT_NAME}
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>)

if(DEFINED OPENTELEMETRY_CPP_INCLUDE_DIRS)
  target_include_directories(${PROJECT_NAME} PUBLIC ${OPENTELEMETRY_CPP_INCLUDE_DIRS})
endif()
if(DEFINED OPENTELEMETRY_CPP_DEFINITIONS)
  target_compile_definitions(${PROJECT_NAME} PRIVATE ${OPENTELEMETRY_CPP_DEFINITIONS})
endif()

target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -Wpedantic)

ament_target_dependencies(
  ${PROJECT_NAME}
  ros_opentelemetry_interfaces
  rclcpp
)

target_link_libraries(${CMAKE_PROJECT_NAME}
   ${OPENTELEMETRY_CPP_LIBRARIES}
)

install(TARGETS ${PROJECT_NAME}
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

install(DIRECTORY include/
  DESTINATION include)

ament_export_include_directories(include)
ament_export_dependencies(rclcpp ros_opentelemetry_interfaces opentelemetry-cpp)
ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)

ament_package()
