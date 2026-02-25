cmake_minimum_required(VERSION 3.8)
cmake_minimum_required(VERSION 3.8)
project(sanhum)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# Pi/Linux = ТОЛЬКО main_pi.cpp
if(UNIX)
  add_executable(sanhum src/main_pi.cpp)
  message(STATUS "Pi: main_pi.cpp only")
else()
  # Windows = все Qt файлы
  find_package(Qt6 REQUIRED COMPONENTS Core Widgets SerialPort)
  file(GLOB_RECURSE SOURCES "src/*.cpp")
  add_executable(sanhum ${SOURCES})
  target_link_libraries(sanhum Qt6::Core Qt6::Widgets Qt6::SerialPort)
endif()

ament_target_dependencies(sanhum rclcpp sensor_msgs geometry_msgs std_msgs)
install(TARGETS sanhum DESTINATION lib/${PROJECT_NAME})
ament_package()
