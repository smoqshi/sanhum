#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <vision_msgs/msg/detection2_d_array.hpp>
#include <opencv2/dnn.hpp>

class YoloDetector
{
public:
    explicit YoloDetector(std::shared_ptr<rclcpp::Node> node);

private:
    void imageCallback(const sensor_msgs::msg::Image::SharedPtr msg);

    std::shared_ptr<rclcpp::Node> node_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
    rclcpp::Publisher<vision_msgs::msg::Detection2DArray>::SharedPtr det_pub_;
    cv::dnn::Net net_;
};
