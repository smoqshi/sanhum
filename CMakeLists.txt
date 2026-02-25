cmake_minimum_required(VERSION 3.8)
project(sanhum)

# Pi = UNIX = ТОЛЬКО main_pi.cpp, НИКЧЕМ НЕ КОМПИЛИРУЕТСЯ GUI
if(UNIX AND NOT APPLE)
  set(IS_PI TRUE)
else()
  set(IS_PI FALSE)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# Pi: ЖЕСТКО ТОЛЬКО main_pi.cpp
if(IS_PI)
  message(STATUS "Pi: compiling ONLY main_pi.cpp")
  add_executable(sanhum src/main_pi.cpp)
else()
  # Desktop: ВСЕ файлы
  message(STATUS "Desktop: compiling ALL files")
  find_package(Qt6 REQUIRED COMPONENTS Core Widgets SerialPort)
  file(GLOB_RECURSE SOURCES src/*.cpp)
  add_executable(sanhum ${SOURCES})
  target_link_libraries(sanhum Qt6::Core Qt6::Widgets Qt6::SerialPort)
endif()

ament_target_dependencies(sanhum rclcpp sensor_msgs geometry_msgs std_msgs)
install(TARGETS sanhum DESTINATION lib/${PROJECT_NAME})
ament_package()
