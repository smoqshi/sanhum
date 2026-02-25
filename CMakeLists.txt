cmake_minimum_required(VERSION 3.8)
project(sanhum)

# Автоопределение платформы
if(UNIX AND NOT APPLE)
  set(PLATFORM_PI ON)
  message(STATUS "=== RASPBERRY PI HEADLESS ===")
  add_compile_definitions(PLATFORM_PI)
else()
  set(PLATFORM_PI OFF)
  message(STATUS "=== DESKTOP Qt GUI ===")
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

if(PLATFORM_PI)
  # Pi: ТОЛЬКО main_pi.cpp
  add_executable(sanhum src/main_pi.cpp)
else()
  # Desktop: все Qt файлы
  find_package(Qt6 REQUIRED COMPONENTS Core Widgets SerialPort)
  file(GLOB_RECURSE SOURCES src/*.cpp)
  add_executable(sanhum ${SOURCES})
  target_link_libraries(sanhum Qt6::Core Qt6::Widgets Qt6::SerialPort)
  add_compile_definitions(PLATFORM_WINDOWS)
endif()

ament_target_dependencies(sanhum rclcpp sensor_msgs geometry_msgs std_msgs)
install(TARGETS sanhum DESTINATION lib/${PROJECT_NAME})
ament_package()
