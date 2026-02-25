cmake_minimum_required(VERSION 3.8)
project(sanhum)

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Найти все зависимости ROS2
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)

# Основной исполняемый файл
add_executable(sanhum_robot 
  src/main.cpp
  src/robot_controller.cpp
  src/sensor_manager.cpp
)

# Зависимости для линковки (ИСПРАВЛЕНИЕ №1)
ament_target_dependencies(sanhum_robot
  rclcpp
  std_msgs
  sensor_msgs
  geometry_msgs
  nav_msgs
)

# Установка исполняемого файла (ИСПРАВЛЕНИЕ №2)
install(TARGETS
  sanhum_robot
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
