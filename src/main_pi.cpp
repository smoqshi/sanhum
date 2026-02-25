#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>

class SanhumRobot : public rclcpp::Node {
public:
    SanhumRobot() : Node("sanhum_robot") {
        publisher_ = create_publisher<sensor_msgs::msg::Image>("camera/image_raw", 10);
        subscription_cmd_ = create_subscription<geometry_msgs::msg::Twist>(
            "cmd_vel", 10, std::bind(&SanhumRobot::cmdVelCallback, this, _1));
        subscription_joints_ = create_subscription<std_msgs::msg::Float32MultiArray>(
            "manipulator/joint_commands", 10, std::bind(&SanhumRobot::jointsCallback, this, _1));
        
        timer_ = create_wall_timer(
            std::chrono::milliseconds(100), std::bind(&SanhumRobot::timerCallback, this));
        
        RCLCPP_INFO(get_logger(), "Sanhum Robot started (headless Pi mode)");
    }

private:
    void timerCallback() {
        // Симуляция камеры
        auto msg = sensor_msgs::msg::Image();
        msg.header.stamp = now();
        msg.height = 480;
        msg.width = 640;
        msg.encoding = "bgr8";
        msg.is_bigendian = 0;
        msg.step = 1920;
        msg.data.resize(480 * 1920, 128); // серый кадр
        publisher_->publish(msg);
    }
    
    void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg) {
        RCLCPP_INFO(get_logger(), "CmdVel: linear.x=%.2f angular.z=%.2f", 
                   msg->linear.x, msg->angular.z);
    }
    
    void jointsCallback(const std_msgs::msg::Float32MultiArray::SharedPtr msg) {
        RCLCPP_INFO(get_logger(), "Joints: size=%zu", msg->data.size());
    }

    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr subscription_cmd_;
    rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_joints_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SanhumRobot>());
    rclcpp::shutdown();
    return 0;
}
