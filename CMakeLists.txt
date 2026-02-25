cmake_minimum_required(VERSION 3.16)
project(sanhum LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Флаг платформы: Windows = GUI, остальное = робот
if(WIN32)
  set(PLATFORM_WINDOWS ON)
else()
  set(PLATFORM_PI ON)
endif()

# Qt и GUI нужны только на Windows
if(PLATFORM_WINDOWS)
  find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network SerialPort)

  set(CMAKE_AUTOMOC ON)
  set(CMAKE_AUTORCC ON)
  set(CMAKE_AUTOUIC ON)
endif()

# ROS2
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(vision_msgs REQUIRED)
find_package(cv_bridge REQUIRED)

# OpenCV
find_package(OpenCV REQUIRED core imgproc dnn highgui)

# Источники и заголовки
file(GLOB_RECURSE PROJECT_SOURCES
    src/*.cpp
)
file(GLOB_RECURSE PROJECT_HEADERS
    include/*.h
)

add_executable(${PROJECT_NAME}
    ${PROJECT_SOURCES}
    ${PROJECT_HEADERS}
)

target_include_directories(${PROJECT_NAME} PRIVATE
    include
    ${OpenCV_INCLUDE_DIRS}
)

if(PLATFORM_WINDOWS)
  target_compile_definitions(${PROJECT_NAME} PRIVATE PLATFORM_WINDOWS)
else()
  target_compile_definitions(${PROJECT_NAME} PRIVATE PLATFORM_PI PLATFORM_LINUX)
endif()

if(PLATFORM_WINDOWS)
  target_link_libraries(${PROJECT_NAME}
      Qt6::Core
      Qt6::Gui
      Qt6::Widgets
      Qt6::Network
      Qt6::SerialPort
      ${OpenCV_LIBS}
  )
else()
  target_link_libraries(${PROJECT_NAME}
      ${OpenCV_LIBS}
  )
endif()

ament_target_dependencies(${PROJECT_NAME}
    rclcpp
    geometry_msgs
    nav_msgs
    sensor_msgs
    std_msgs
    vision_msgs
    cv_bridge
)

install(TARGETS ${PROJECT_NAME}
    DESTINATION lib/${PROJECT_NAME}
)

ament_package()
