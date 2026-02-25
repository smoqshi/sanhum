cmake_minimum_required(VERSION 3.8)
project(sanhum)

# Pi определяем автоматически
if(UNIX AND NOT APPLE)
  add_compile_definitions(PLATFORM_PI)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

file(GLOB_RECURSE SOURCES src/*.cpp)
add_executable(sanhum ${SOURCES})

ament_target_dependencies(sanhum 
  rclcpp 
  sensor_msgs 
  geometry_msgs 
  std_msgs
)

if(NOT (UNIX AND NOT APPLE))
  find_package(Qt6 REQUIRED COMPONENTS Core Widgets SerialPort)
  target_link_libraries(sanhum Qt6::Core Qt6::Widgets Qt6::SerialPort)
endif()

install(TARGETS
  sanhum
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
