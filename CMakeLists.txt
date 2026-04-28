cmake_minimum_required(VERSION 3.16)
project(sanhum
    VERSION 1.0.0
    DESCRIPTION "Sanhum Robot System - ROS2 robot control with Python GUI"
    LANGUAGES CXX
)

# C++ Standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler warnings
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Common ROS2 packages
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

if(WIN32)
    # Windows: Skip C++ build, use Python GUI only
    message(STATUS "Windows detected - Using Python GUI, skipping C++ build")

else()
    # --- Linux/PI Robot Build ---
    message(STATUS "Configuring for Linux Robot - Robot Node Only")

    # Find Qt5 for serial port (robot node only)
    find_package(Qt5 REQUIRED COMPONENTS Core SerialPort)
    set(CMAKE_AUTOMOC ON)

    # Robot node
    add_executable(sanhum_robot
        src/robot_main.cpp
        src/motor_driver.cpp
        src/esp32_driver.cpp
        src/arduino_sensors.cpp
        include/esp32_driver.h
        include/arduino_sensors.h
    )

    set_target_properties(sanhum_robot PROPERTIES AUTOMOC ON)

    target_compile_definitions(sanhum_robot PRIVATE PLATFORM_LINUX PLATFORM_PI)

    target_include_directories(sanhum_robot PRIVATE include)

    target_link_libraries(sanhum_robot Qt5::SerialPort Qt5::Core)

    ament_target_dependencies(sanhum_robot
        rclcpp
        geometry_msgs
        nav_msgs
        std_msgs
        sensor_msgs
    )

    install(TARGETS sanhum_robot DESTINATION lib/${PROJECT_NAME})

endif()

# Install common launch and config files
install(
    DIRECTORY launch config
    DESTINATION share/${PROJECT_NAME}
)

# Install headers
install(
    DIRECTORY include/
    DESTINATION include/${PROJECT_NAME}
)

ament_package()
