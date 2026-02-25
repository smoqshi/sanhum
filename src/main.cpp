#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>

using std::placeholders::_1;

class SanhumRobot : public rclcpp::Node 
{
public:
  SanhumRobot()
  : Node("sanhum_robot")
  {
    // Publisher для моторов
    motor_publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);
    
    // Subscriber для лазера
    laser_subscriber_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
      "/scan", 10, std::bind(&SanhumRobot::laser_callback, this, _1));
    
    // Таймер управления 50Гц
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(20),
      std::bind(&SanhumRobot::control_loop, this));

    RCLCPP_INFO(this->get_logger(), "Sanhum Robot Node Started");
  }

private:
  void laser_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg) 
  {
    // Берем центральный луч
    front_distance_ = msg->ranges[0];
  }

  void control_loop()
  {
    auto cmd = geometry_msgs::msg::Twist();
    
    if (front_distance_ > 0.5 || front_distance_ == 0.0) {
      // Дорога свободна
      cmd.linear.x = 0.2;
    } else {
      // Препятствие - поворот
      cmd.angular.z = 1.0;
    }
    
    motor_publisher_->publish(cmd);
  }

  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr motor_publisher_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr laser_subscriber_;
  rclcpp::TimerBase::SharedPtr timer_;
  float front_distance_ = 10.0;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<SanhumRobot>());
  rclcpp::shutdown();
  return 0;
}
