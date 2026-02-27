cmake_minimum_required(VERSION 3.16)
project(sanhum LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Common ROS2 packages
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

if(WIN32)
    # --- Windows GUI Build ---
    message(STATUS "Configuring for Windows GUI")

    find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network)
    set(CMAKE_AUTOMOC ON)
    set(CMAKE_AUTORCC ON)
    set(CMAKE_AUTOUIC ON)

    find_package(nav_msgs REQUIRED)
    find_package(vision_msgs REQUIRED)
    find_package(cv_bridge REQUIRED)
    find_package(OpenCV REQUIRED core imgproc)

    add_executable(sanhum_gui
        src/gui_main.cpp
        src/main_window.cpp
        src/joystick_widget.cpp
        src/robot_view_widget.cpp
        src/gamepad_control.cpp
        src/wifi_server.cpp
    )

    target_compile_definitions(sanhum_gui PRIVATE PLATFORM_WINDOWS)

    target_include_directories(sanhum_gui PRIVATE
        include
        ${OpenCV_INCLUDE_DIRS}
    )

    target_link_libraries(sanhum_gui PRIVATE
        Qt6::Core
        Qt6::Gui
        Qt6::Widgets
        Qt6::Network
        ${OpenCV_LIBS}
    )

    ament_target_dependencies(sanhum_gui
        rclcpp
        geometry_msgs
        nav_msgs
        sensor_msgs
        std_msgs
        vision_msgs
        cv_bridge
    )

    install(TARGETS sanhum_gui DESTINATION lib/${PROJECT_NAME})

else()
    # --- Linux/PI Robot Build ---
    message(STATUS "Configuring for Linux Robot")

    # In the future, you might need to find hardware-specific libraries here
    # find_package(pigpio REQUIRED)

    add_executable(sanhum_robot
        src/robot_main.cpp
        # src/motor_driver.cpp # To be added when implemented
        # src/arduino_sensors.cpp # To be added when implemented
        # src/esp32_driver.cpp # To be added when implemented
    )

    target_compile_definitions(sanhum_robot PRIVATE PLATFORM_LINUX PLATFORM_PI)

    target_include_directories(sanhum_robot PRIVATE include)

    ament_target_dependencies(sanhum_robot
        rclcpp
        geometry_msgs
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

ament_package()
