cmake_minimum_required(VERSION 3.8)
project(sanhum)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

if(UNIX)
  # Pi: ТОЛЬКО main_pi.cpp (без motor_driver.h)
  add_executable(sanhum src/main_pi.cpp)
  message(STATUS "Pi: main_pi.cpp only")
else()
  # Windows: все файлы с Qt
  find_package(Qt6 REQUIRED COMPONENTS Core Widgets SerialPort)
  file(GLOB_RECURSE SOURCES src/*.cpp)
  add_executable(sanhum ${SOURCES})
  target_link_libraries(sanhum Qt6::Core Qt6::Widgets Qt6::SerialPort)
endif()

ament_target_dependencies(sanhum rclcpp)
install(TARGETS sanhum DESTINATION lib/${PROJECT_NAME})
ament_package()
