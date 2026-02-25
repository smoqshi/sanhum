#include <rclcpp/rclcpp.hpp>
#include "robot_controller.hpp"

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);  // ИСПРАВЛЕНИЕ №4 - обязательная инициализация
  
  auto node = std::make_shared<RobotController>("sanhum_robot");
  
  rclcpp::spin(node);  // ИСПРАВЛЕНИЕ №5 - основной цикл ROS2
  
  rclcpp::shutdown();
  return 0;
}
