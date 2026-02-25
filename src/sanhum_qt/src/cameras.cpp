#include "cameras.h"
#include <opencv2/opencv.hpp>
#include <cv_bridge/cv_bridge.hpp>

using namespace std::chrono_literals;

class CamerasImpl
{
public:
    cv::VideoCapture cap_left;
    cv::VideoCapture cap_right;
    cv::VideoCapture cap_mono;
};

Cameras::Cameras(std::shared_ptr<rclcpp::Node> node)
    : node_(std::move(node)),
    impl_(std::make_unique<CamerasImpl>())
{
    // параметры можно сделать настраиваемыми
    impl_->cap_left.open(0);
    impl_->cap_right.open(1);
    impl_->cap_mono.open(2);

    impl_->cap_left.set(cv::CAP_PROP_FRAME_WIDTH, 640);
    impl_->cap_left.set(cv::CAP_PROP_FRAME_HEIGHT, 480);
    impl_->cap_right.set(cv::CAP_PROP_FRAME_WIDTH, 640);
    impl_->cap_right.set(cv::CAP_PROP_FRAME_HEIGHT, 480);
    impl_->cap_mono.set(cv::CAP_PROP_FRAME_WIDTH, 640);
    impl_->cap_mono.set(cv::CAP_PROP_FRAME_HEIGHT, 480);

    left_pub_ = node_->create_publisher<sensor_msgs::msg::Image>("/stereo/left/image_raw", 10);
    right_pub_ = node_->create_publisher<sensor_msgs::msg::Image>("/stereo/right/image_raw", 10);
    mono_pub_ = node_->create_publisher<sensor_msgs::msg::Image>("/mono/image_raw", 10);

    capture_timer_ = node_->create_wall_timer(
        33ms, std::bind(&Cameras::captureTimerCallback, this));
}

Cameras::~Cameras() = default;

void Cameras::captureTimerCallback()
{
    cv::Mat frame_left, frame_right, frame_mono;

    if (impl_->cap_left.isOpened())  impl_->cap_left.read(frame_left);
    if (impl_->cap_right.isOpened()) impl_->cap_right.read(frame_right);
    if (impl_->cap_mono.isOpened())  impl_->cap_mono.read(frame_mono);

    auto stamp = node_->now();

    if (!frame_left.empty()) {
        std_msgs::msg::Header header;
        header.stamp = stamp;
        header.frame_id = "stereo_left";
        sensor_msgs::msg::Image::SharedPtr msg =
            cv_bridge::CvImage(header, "bgr8", frame_left).toImageMsg();
        left_pub_->publish(*msg);
    }

    if (!frame_right.empty()) {
        std_msgs::msg::Header header;
        header.stamp = stamp;
        header.frame_id = "stereo_right";
        sensor_msgs::msg::Image::SharedPtr msg =
            cv_bridge::CvImage(header, "bgr8", frame_right).toImageMsg();
        right_pub_->publish(*msg);
    }

    if (!frame_mono.empty()) {
        std_msgs::msg::Header header;
        header.stamp = stamp;
        header.frame_id = "mono_camera";
        sensor_msgs::msg::Image::SharedPtr msg =
            cv_bridge::CvImage(header, "bgr8", frame_mono).toImageMsg();
        mono_pub_->publish(*msg);
    }
}

