cmake_minimum_required(VERSION 3.8)
project(sanhum)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

if(UNIX)
  # Pi использует СУЩЕСТВУЮЩИЙ main.cpp
  add_executable(sanhum src/main.cpp)
else()
  find_package(Qt6 REQUIRED COMPONENTS Core Widgets SerialPort)
  file(GLOB_RECURSE SOURCES src/*.cpp)
  add_executable(sanhum ${SOURCES})
  target_link_libraries(sanhum Qt6::Core Qt6::Widgets Qt6::SerialPort)
endif()

ament_target_dependencies(sanhum rclcpp)
install(TARGETS sanhum DESTINATION lib/${PROJECT_NAME})
ament_package()
