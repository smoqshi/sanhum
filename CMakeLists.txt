cmake_minimum_required(VERSION 3.8)
project(sanhum)

# Определяем платформу
if(NOT DEFINED PLATFORM_PI)
  if(UNIX AND NOT APPLE)
    set(PLATFORM_PI ON)
  else()
    set(PLATFORM_PI OFF)
  endif()
endif()

if(PLATFORM_PI)
  message(STATUS "Building for Raspberry Pi (headless)")
  add_compile_definitions(PLATFORM_PI)
else()
  message(STATUS "Building for Desktop (Qt GUI)")
  find_package(Qt6 REQUIRED COMPONENTS Core Widgets SerialPort)
  add_compile_definitions(PLATFORM_WINDOWS)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# Источники для Pi (headless)
set(PI_SOURCES
  src/main_pi.cpp
)

# Источники для Desktop (GUI)  
set(DESKTOP_SOURCES
  src/main.cpp
  src/main_window.cpp
  src/joystick_widget.cpp
)

# Общие заголовки
set(COMMON_HEADERS
  include/motor_driver.h
  include/esp32_driver.h
  include/arduino_sensors.h
)

if(PLATFORM_PI)
  # Только Pi версии файлов (без Qt)
  set(PROJECT_SOURCES ${PI_SOURCES})
else()
  set(PROJECT_SOURCES ${DESKTOP_SOURCES})
endif()

add_executable(sanhum ${PROJECT_SOURCES} ${COMMON_HEADERS})
ament_target_dependencies(sanhum rclcpp sensor_msgs geometry_msgs std_msgs)

if(NOT PLATFORM_PI)
  target_link_libraries(sanhum Qt6::Core Qt6::Widgets Qt6::SerialPort)
endif()

install(TARGETS
  sanhum
  DESTINATION lib/${PROJECT_NAME})

ament_package()
