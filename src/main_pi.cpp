#include <rclcpp/rclcpp.hpp>

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("sanhum_pi");
    RCLCPP_INFO(node->get_logger(), "🦾 Sanhum Pi started (headless)");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
