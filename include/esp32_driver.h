#pragma once

#include <QObject>
#include <QSerialPort>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>

class Esp32Driver : public QObject
{
    Q_OBJECT
public:
    explicit Esp32Driver(std::shared_ptr<rclcpp::Node> node,
                         QObject *parent = nullptr);

private slots:
    void onSerialReadyRead();

private:
    void sendJointCommand(const sensor_msgs::msg::JointState &cmd);

    std::shared_ptr<rclcpp::Node> node_;
    QSerialPort serial_;
    rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_cmd_sub_;
    rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_state_pub_;
};
