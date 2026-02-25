#pragma once

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <nav_msgs/msg/odometry.hpp>

class MotorDriver
{
public:
    explicit MotorDriver(std::shared_ptr<rclcpp::Node> node);
    ~MotorDriver();

private:
    void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg);
    void odomTimerCallback();

    std::shared_ptr<rclcpp::Node> node_;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::TimerBase::SharedPtr odom_timer_;

    double left_speed_{0.0};
    double right_speed_{0.0};
};
