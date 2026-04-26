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
    message(STATUS "Configuring for Windows GUI - High Performance C++")

    find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network)
    set(CMAKE_AUTOMOC ON)
    set(CMAKE_AUTORCC ON)
    set(CMAKE_AUTOUIC ON)

    find_package(nav_msgs REQUIRED)
    find_package(vision_msgs REQUIRED)
    find_package(cv_bridge REQUIRED)
    find_package(OpenCV REQUIRED core imgproc)

    # High Performance C++ GUI Application
    add_executable(sanhum_robot_gui_cpp
        src/sanhum_robot_gui.cpp
        src/motor_driver.cpp
        src/esp32_driver.cpp
        src/arduino_sensors.cpp
        src/cameras.cpp
        src/gamepad_control.cpp
        src/wifi_server.cpp
        src/yolo_detector.cpp
    )

    target_compile_definitions(sanhum_robot_gui_cpp PRIVATE PLATFORM_WINDOWS HIGH_PERFORMANCE)

    target_include_directories(sanhum_robot_gui_cpp PRIVATE
        include
        ${OpenCV_INCLUDE_DIRS}
    )

    target_link_libraries(sanhum_robot_gui_cpp PRIVATE
        Qt6::Core
        Qt6::Gui
        Qt6::Widgets
        Qt6::Network
        ${OpenCV_LIBS}
    )

    ament_target_dependencies(sanhum_robot_gui_cpp
        rclcpp
        geometry_msgs
        nav_msgs
        sensor_msgs
        std_msgs
        vision_msgs
        cv_bridge
    )

    install(TARGETS sanhum_robot_gui_cpp DESTINATION lib/${PROJECT_NAME})

    # Legacy Python GUI (for comparison)
    add_executable(sanhum_gui
        src/gui_main.cpp
        src/main_window.cpp
        src/joystick_widget.cpp
        src/robot_view_widget.cpp
    )

    target_compile_definitions(sanhum_gui PRIVATE PLATFORM_WINDOWS LEGACY_GUI)

    ament_target_dependencies(sanhum_gui
        rclcpp
        geometry_msgs
        nav_msgs
        sensor_msgs
        std_msgs
    )

else()
    # --- Linux/PI Robot Build ---
    message(STATUS "Configuring for Linux Robot - High Performance C++")

    # Find Qt5
    find_package(Qt5 REQUIRED COMPONENTS Core Gui Widgets Network SerialPort)
    set(CMAKE_AUTOMOC ON)
    set(CMAKE_AUTORCC ON)
    set(CMAKE_AUTOUIC ON)

    # Find OpenCV
    find_package(OpenCV REQUIRED)

    # Find additional ROS2 packages
    find_package(nav_msgs REQUIRED)
    find_package(vision_msgs REQUIRED)
    find_package(cv_bridge REQUIRED)

    # High Performance C++ GUI Application (Linux - no gamepad_control)
    add_executable(sanhum_robot_gui_cpp
        src/sanhum_robot_gui.cpp
        src/motor_driver.cpp
        src/esp32_driver.cpp
        src/arduino_sensors.cpp
        src/cameras.cpp
        src/wifi_server.cpp
        src/yolo_detector.cpp
        include/esp32_driver.h
        include/arduino_sensors.h
        include/wifi_server.h
    )

    target_compile_definitions(sanhum_robot_gui_cpp PRIVATE PLATFORM_LINUX HIGH_PERFORMANCE)

    target_include_directories(sanhum_robot_gui_cpp PRIVATE
        include
        ${OpenCV_INCLUDE_DIRS}
    )

    target_link_libraries(sanhum_robot_gui_cpp
        Qt5::Core
        Qt5::Gui
        Qt5::Widgets
        Qt5::Network
        Qt5::SerialPort
        ${OpenCV_LIBS}
    )

    ament_target_dependencies(sanhum_robot_gui_cpp
        rclcpp
        geometry_msgs
        nav_msgs
        sensor_msgs
        std_msgs
        vision_msgs
        cv_bridge
    )

    install(TARGETS sanhum_robot_gui_cpp DESTINATION lib)

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

    install(TARGETS sanhum_robot DESTINATION lib)

endif()

# Install common launch and config files
install(
    DIRECTORY launch config
    DESTINATION share/${PROJECT_NAME}
)

ament_package()
