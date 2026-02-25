#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>

class SanhumRobot : public rclcpp::Node {
public:
    SanhumRobot() : Node("sanhum_robot") {
        publisher_ = this->create_publisher<sensor_msgs::msg::Image>("camera/image_raw", 10);
        cmd_sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
            "cmd_vel", 10, std::bind(&SanhumRobot::cmdVelCallback, this, _1));
        joints_sub_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
            "manipulator/joint_commands", 10, std::bind(&SanhumRobot::jointsCallback, this, _1));
        
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100), std::bind(&SanhumRobot::timerCallback, this));
        
        RCLCPP_INFO(this->get_logger(), "🦾 Sanhum Robot Pi started");
    }

private:
    void timerCallback() {
        auto msg = sensor_msgs::msg::Image();
        msg.header.stamp = this->now();
        msg.height = 480; msg.width = 640; msg.encoding = "bgr8";
        msg.is_bigendian = 0; msg.step = 1920;
        msg.data.resize(480 * 1920, 128);
        publisher_->publish(msg);
    }
    
    void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg) {
        RCLCPP_INFO(this->get_logger(), "CmdVel: X=%.2f Z=%.2f", msg->linear.x, msg->angular.z);
    }
    
    void jointsCallback(const std_msgs::msg::Float32MultiArray::SharedPtr msg) {
        RCLCPP_INFO(this->get_logger(), "Joints: %zu", msg->data.size());
    }

    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_sub_;
    rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr joints_sub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SanhumRobot>());
    rclcpp::shutdown();
    return 0;
}
