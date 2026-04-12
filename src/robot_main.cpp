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

    // Initialize hardware drivers
    auto motor_driver = std::make_shared<MotorDriver>(node);
    auto esp32_driver = std::make_shared<Esp32Driver>(node);
    auto arduino_sensors = std::make_shared<ArduinoSensors>(node);

    // Motor driver handles its own cmd_vel subscription internally

    // Hardware drivers handle their own publishers internally

    rclcpp::spin(node);
    rclcpp::shutdown();

    return 0;
}
