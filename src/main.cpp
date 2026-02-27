#if defined(PLATFORM_WINDOWS)
#include <QApplication>
#include <QInputDialog>
#include <QLineEdit>
#include <rclcpp/rclcpp.hpp>

#include "main_window.h"
#include "communication_protocols.h"

int main(int argc, char *argv[])
{
    // Инициализация ROS2
    rclcpp::init(argc, argv);

    // Инициализация Qt
    QApplication app(argc, argv);

    // Диалог выбора: работаем ли с реальным роботом по ROS2
    bool ok = false;
    QString ns = QInputDialog::getText(
        nullptr,
        QObject::tr("Подключение к роботу"),
        QObject::tr("ROS2 namespace робота (оставь пустым для чистой симуляции):"),
        QLineEdit::Normal,
        QString(),
        &ok
    );

    auto ros_node = std::make_shared<rclcpp::Node>("sanhum_qt_node");

    MainWindow w(ros_node);
    if (ok && !ns.trimmed().isEmpty()) {
        w.setRobotNamespace(ns.trimmed());
    } else {
        w.setRobotNamespace(QString());
    }

    w.show();

    int ret = app.exec();
    rclcpp::shutdown();
    return ret;
}

#elif defined(PLATFORM_PI)

#include <rclcpp/rclcpp.hpp>
#include <iostream>

#include "communication_protocols.h"
#include "motor_driver.h"
#include "arduino_sensors.h"
#include "esp32_driver.h"

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);

    auto node = std::make_shared<rclcpp::Node>("sanhum_robot_node");

    // Declare parameters to be loaded from a YAML file
    node->declare_parameter<int>("raspberry_pi.motor_pins.left_motor_1");
    node->declare_parameter<int>("raspberry_pi.motor_pins.left_motor_2");
    node->declare_parameter<int>("raspberry_pi.motor_pins.right_motor_1");
    node->declare_parameter<int>("raspberry_pi.motor_pins.right_motor_2");
    node->declare_parameter<std::string>("raspberry_pi.serial_ports.esp32.port");
    node->declare_parameter<int>("raspberry_pi.serial_ports.esp32.baud_rate");
    node->declare_parameter<std::string>("raspberry_pi.serial_ports.arduino_nano.port");
    node->declare_parameter<int>("raspberry_pi.serial_ports.arduino_nano.baud_rate");

    // Get parameters
    int left_motor_1 = node->get_parameter("raspberry_pi.motor_pins.left_motor_1").as_int();
    int left_motor_2 = node->get_parameter("raspberry_pi.motor_pins.left_motor_2").as_int();
    int right_motor_1 = node->get_parameter("raspberry_pi.motor_pins.right_motor_1").as_int();
    int right_motor_2 = node->get_parameter("raspberry_pi.motor_pins.right_motor_2").as_int();
    std::string esp32_port = node->get_parameter("raspberry_pi.serial_ports.esp32.port").as_string();
    int esp32_baud_rate = node->get_parameter("raspberry_pi.serial_ports.esp32.baud_rate").as_int();
    std::string arduino_port = node->get_parameter("raspberry_pi.serial_ports.arduino_nano.port").as_string();
    int arduino_baud_rate = node->get_parameter("raspberry_pi.serial_ports.arduino_nano.baud_rate").as_int();

    RCLCPP_INFO(node->get_logger(), "Starting Sanhum Robot Node on Raspberry Pi");
    RCLCPP_INFO(node->get_logger(), "Motor Pins: L1=%d, L2=%d, R1=%d, R2=%d", left_motor_1, left_motor_2, right_motor_1, right_motor_2);
    RCLCPP_INFO(node->get_logger(), "ESP32: port=%s, baud=%d", esp32_port.c_str(), esp32_baud_rate);
    RCLCPP_INFO(node->get_logger(), "Arduino Nano: port=%s, baud=%d", arduino_port.c_str(), arduino_baud_rate);

    // Initialize hardware drivers (placeholders for now)
    // sanhum::MotorDriver motor_driver(left_motor_1, left_motor_2, right_motor_1, right_motor_2);
    // sanhum::ESP32Driver esp32_driver(esp32_port, esp32_baud_rate);
    // sanhum::ArduinoSensors arduino_sensors(arduino_port, arduino_baud_rate);

    // Create a subscriber for command velocity
    auto cmd_vel_sub = node->create_subscription<sanhum::TwistMsg>(
        sanhum::kCmdVelTopic,
        10,
        [/*&motor_driver*/](const sanhum::TwistMsg::SharedPtr msg) {
            RCLCPP_INFO(rclcpp::get_logger("sanhum_robot_node"), "Received cmd_vel: linear.x=%.2f, angular.z=%.2f", msg->linear.x, msg->angular.z);
            // motor_driver.set_speeds(msg->linear.x, msg->angular.z);
        }
    );

    // Create publishers for sensor data
    auto odom_pub = node->create_publisher<sanhum::OdometryMsg>(sanhum::kOdometryTopic, 10);
    auto imu_pub = node->create_publisher<sanhum::ImuMsg>(sanhum::kImuTopic, 10);
    auto arduino_sensors_pub = node->create_publisher<sanhum::Float32MultiArrayMsg>(sanhum::kArduinoSensorsTopic, 10);

    // Example of publishing sensor data (in a real scenario, this would come from the sensors)
    auto timer = node->create_wall_timer(std::chrono::seconds(1), [&]() {
        // Here, you would get data from arduino_sensors, esp32_driver etc. and publish it.
    });

    rclcpp::spin(node);
    rclcpp::shutdown();

    return 0;
}

#endif
