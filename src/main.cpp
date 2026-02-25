#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>

using std::placeholders::_1;

class SanhumRobot : public rclcpp::Node 
{
public:
  SanhumRobot()
  : Node("sanhum_robot_node"), front_distance_(10.0)
  {
    // ИСПРАВЛЕНО: Publisher моторов
    motor_publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);
    
    // ИСПРАВЛЕНО: Subscriber лазера
    laser_subscriber_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
      "/scan", 10, std::bind(&SanhumRobot::laser_callback, this, _1));
    
    // ИСПРАВЛЕНО: Таймер 50Гц
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(20),
      std::bind(&SanhumRobot::control_loop, this));

    RCLCPP_INFO(this->get_logger(), "Sanhum Robot запущен");
  }

private:
  void laser_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg) 
  {
    if (!msg->ranges.empty()) {
      front_distance_ = msg->ranges[0];  // Центральный луч
    }
  }

  void control_loop()
  {
    auto cmd = geometry_msgs::msg::Twist();
    
    // ИСПРАВЛЕНО: Логика автономии
    if (front_distance_ > 0.5 || front_distance_ == 0.0) {
      cmd.linear.x = 0.2;  // Вперед
    } else {
      cmd.angular.z = 1.0; // Поворот направо
    }
    
    motor_publisher_->publish(cmd);
    
    // Отладка
    RCLCPP_INFO_ONCE(this->get_logger(), "Дистанция: %.2f м", front_distance_);
  }

  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr motor_publisher_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr laser_subscriber_;
  rclcpp::TimerBase::SharedPtr timer_;
  float front_distance_;
};

int main(int argc, char * argv[])
{
  // ИСПРАВЛЕНО: rclcpp::init()
  rclcpp::init(argc, argv);
  
  auto node = std::make_shared<SanhumRobot>();
  
  // ИСПРАВЛЕНО: rclcpp::spin()
  rclcpp::spin(node);
  
  // ИСПРАВЛЕНО: rclcpp::shutdown()
  rclcpp::shutdown();
  return 0;
}
