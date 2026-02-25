cmake_minimum_required(VERSION 3.8)
project(sanhum)

# ПЛАТФОРМА Pi = ТОЛЬКО main_pi.cpp
if(PLATFORM_PI OR UNIX)
  message(STATUS "=== RASPBERRY PI HEADLESS ===")
  add_compile_definitions(PLATFORM_PI)
  set(PROJECT_SOURCES src/main_pi.cpp)
else()
  message(STATUS "=== DESKTOP Qt GUI ===")
  find_package(Qt6 REQUIRED COMPONENTS Core Widgets SerialPort)
  add_compile_definitions(PLATFORM_WINDOWS)
  file(GLOB_RECURSE PROJECT_SOURCES src/*.cpp)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(sanhum ${PROJECT_SOURCES})
ament_target_dependencies(sanhum rclcpp sensor_msgs geometry_msgs std_msgs)

if(NOT (PLATFORM_PI OR UNIX))
  target_link_libraries(sanhum Qt6::Core Qt6::Widgets Qt6::SerialPort)
endif()

install(TARGETS sanhum DESTINATION lib/${PROJECT_NAME})
ament_package()
