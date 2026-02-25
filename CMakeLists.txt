cmake_minimum_required(VERSION 3.8)
project(sanhum)

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ИСПРАВЛЕНО: ВСЕ find_package()
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

# ИСПРАВЛЕНО: ТВОЙ main.cpp + зависимости линковки
add_executable(sanhum_node src/main.cpp)
ament_target_dependencies(sanhum_node 
  rclcpp 
  std_msgs 
  sensor_msgs 
  geometry_msgs
)

# ИСПРАВЛЕНО: install (отсутствовал)
install(TARGETS
  sanhum_node
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_lint_auto_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
