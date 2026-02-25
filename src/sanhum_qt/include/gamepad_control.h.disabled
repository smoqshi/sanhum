#pragma once

#include <QObject>
#include <QGamepad>
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>

class GamepadControl : public QObject
{
    Q_OBJECT
public:
    explicit GamepadControl(std::shared_ptr<rclcpp::Node> node,
                            QObject *parent = nullptr);

private slots:
    void onAxisLeftXChanged(double value);
    void onAxisLeftYChanged(double value);

private:
    void publishCmdVel();

    std::shared_ptr<rclcpp::Node> node_;
    QGamepad gamepad_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;

    double axis_x_{0.0};
    double axis_y_{0.0};
};
