#include "esp32_driver.h"

#include <sensor_msgs/msg/joint_state.hpp>
#include <QSerialPort>
#include <QSerialPortInfo>
#include <QByteArray>

Esp32Driver::Esp32Driver(std::shared_ptr<rclcpp::Node> node, QObject *parent)
    : QObject(parent),
      node_(std::move(node))
{
    // Настройка порта (можно поменять имя устройства под свою плату)
    serial_.setPortName("/dev/ttyACM0");
    serial_.setBaudRate(QSerialPort::Baud115200);
    serial_.setDataBits(QSerialPort::Data8);
    serial_.setParity(QSerialPort::NoParity);
    serial_.setStopBits(QSerialPort::OneStop);
    serial_.setFlowControl(QSerialPort::NoFlowControl);

    serial_.open(QIODevice::ReadWrite);

    QObject::connect(&serial_, &QSerialPort::readyRead,
                     this, &Esp32Driver::onSerialReadyRead);

    // Подписка на команды манипулятора
    joint_cmd_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
        "/manipulator/joint_commands", 10,
        [this](sensor_msgs::msg::JointState::SharedPtr msg) {
            sendJointCommand(*msg);
        });

    // Паблишер состояний манипулятора (пока заглушка)
    joint_state_pub_ = node_->create_publisher<sensor_msgs::msg::JointState>(
        "/manipulator/joint_states", 10);
}

void Esp32Driver::onSerialReadyRead()
{
    QByteArray data = serial_.readAll();
    if (data.isEmpty())
        return;

    // Dummy ESP32 protocol parsing - simulate joint states
    // TODO: Replace with actual protocol parsing from ESP32
    // Expected format: "S:p1,p2,p3,p4,p5\n" where p1-p5 are joint positions
    QString str = QString::fromUtf8(data);
    QStringList lines = str.split('\n', Qt::SkipEmptyParts);

    for (const QString &line : lines) {
        if (line.startsWith("S:")) {
            QStringList parts = line.mid(2).split(',');
            if (parts.size() >= 5) {
                sensor_msgs::msg::JointState state;
                state.header.stamp = node_->get_clock()->now();
                state.name = {"joint1", "joint2", "joint3", "joint4", "joint5"};
                state.position = {
                    parts[0].toDouble(),
                    parts[1].toDouble(),
                    parts[2].toDouble(),
                    parts[3].toDouble(),
                    parts[4].toDouble()
                };
                joint_state_pub_->publish(state);
            }
        }
    }

    // If no valid data received, publish dummy state
    sensor_msgs::msg::JointState state;
    state.header.stamp = node_->get_clock()->now();
    state.name = {"joint1", "joint2", "joint3", "joint4", "joint5"};
    state.position = {0.0, 0.0, 0.0, 0.0, 0.0};
    joint_state_pub_->publish(state);
}

void Esp32Driver::sendJointCommand(const sensor_msgs::msg::JointState &cmd)
{
    if (!serial_.isOpen())
        return;

    if (cmd.position.size() < 5)
        return;

    // Простейший текстовый протокол: C:p1,p2,p3,p4,p5\n
    QString out = QString("C:%1,%2,%3,%4,%5\n")
                      .arg(cmd.position[0], 0, 'f', 3)
                      .arg(cmd.position[1], 0, 'f', 3)
                      .arg(cmd.position[2], 0, 'f', 3)
                      .arg(cmd.position[3], 0, 'f', 3)
                      .arg(cmd.position[4], 0, 'f', 3);

    serial_.write(out.toUtf8());
}


