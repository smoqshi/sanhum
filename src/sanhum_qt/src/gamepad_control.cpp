#include "gamepad_control.h"

GamepadControl::GamepadControl(std::shared_ptr<rclcpp::Node> node, QObject *parent)
    : QObject(parent),
    node_(std::move(node)),
    gamepad_(0) // ID геймпада
{
    cmd_vel_pub_ = node_->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);

    connect(&gamepad_, &QGamepad::axisLeftXChanged,
            this, &GamepadControl::onAxisLeftXChanged);
    connect(&gamepad_, &QGamepad::axisLeftYChanged,
            this, &GamepadControl::onAxisLeftYChanged);
}

void GamepadControl::onAxisLeftXChanged(double value)
{
    axis_x_ = value;
    publishCmdVel();
}

void GamepadControl::onAxisLeftYChanged(double value)
{
    axis_y_ = value;
    publishCmdVel();
}

void GamepadControl::publishCmdVel()
{
    geometry_msgs::msg::Twist msg;
    msg.linear.x  = -axis_y_;
    msg.angular.z = axis_x_;
    cmd_vel_pub_->publish(msg);
}
