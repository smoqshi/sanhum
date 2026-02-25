#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>

class CamerasImpl;

class Cameras
{
public:
    explicit Cameras(std::shared_ptr<rclcpp::Node> node);
    ~Cameras();

private:
    void captureTimerCallback();

    std::shared_ptr<rclcpp::Node> node_;
    std::unique_ptr<CamerasImpl> impl_;

    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr left_pub_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr right_pub_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr mono_pub_;
    rclcpp::TimerBase::SharedPtr capture_timer_;
};
