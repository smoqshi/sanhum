#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <geometry_msgs/msg/twist.hpp>

class SanhumRobot : public rclcpp::Node {
public:
    SanhumRobot() : Node("sanhum_robot") {
        pub_ = this->create_publisher<sensor_msgs::msg::Image>("camera/image_raw", 10);
        sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
            "cmd_vel", 10, [this](const geometry_msgs::msg::Twist::SharedPtr msg) {
                RCLCPP_INFO(this->get_logger(), "Cmd: %.2f", msg->linear.x);
            });
        timer_ = this->create_wall_timer(
            std::chrono::seconds(1), [this]() {
                RCLCPP_INFO(this->get_logger(), "🦾 Sanhum Pi OK");
            });
    }

private:
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub_;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr sub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SanhumRobot>());
    rclcpp::shutdown();
    return 0;
}
