#include "robot_controller.hpp"
#include <memory>

RobotController::RobotController(const std::string & node_name)
  : Node(node_name)
{
  // Publisher для команд моторов (ИСПРАВЛЕНИЕ №6)
  motor_pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);
  
  // Subscriber для датчиков
  sensor_sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
    "/scan", 10, std::bind(&RobotController::sensorCallback, this, _1));
    
  timer_ = this->create_wall_timer(
    std::chrono::milliseconds(100),
    std::bind(&RobotController::controlLoop, this));
    
  RCLCPP_INFO(this->get_logger(), "Sanhum Robot запущен");
}

void RobotController::sensorCallback(const sensor_msgs::msg::LaserScan::SharedPtr msg) {
  distance_front_ = msg->ranges[0];  // Центральный луч
}

void RobotController::controlLoop() {
  geometry_msgs::msg::Twist cmd;
  
  if (distance_front_ > 0.5 || distance_front_ == 0.0) {
    // Свободный путь - вперед
    cmd.linear.x = 0.3;
  } else {
    // Препятствие - поворот
    cmd.angular.z = 1.0;
  }
  
  motor_pub_->publish(cmd);
}
