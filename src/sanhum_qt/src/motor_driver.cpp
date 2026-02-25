#include "motor_driver.h"
#include <chrono>

using namespace std::chrono_literals;

MotorDriver::MotorDriver(std::shared_ptr<rclcpp::Node> node)
    : node_(std::move(node))
{
    // Подписка на /cmd_vel
    cmd_vel_sub_ = node_->create_subscription<geometry_msgs::msg::Twist>(
        "/cmd_vel", 10,
        std::bind(&MotorDriver::cmdVelCallback, this, std::placeholders::_1));

    // Публикация одометрии
    odom_pub_ = node_->create_publisher<nav_msgs::msg::Odometry>("/odom", 10);

    // Таймер одометрии (50 Гц)
    odom_timer_ = node_->create_wall_timer(
        20ms, std::bind(&MotorDriver::odomTimerCallback, this));

    // TODO: инициализация pigpio / GPIO драйвера
    // gpioInitialise();
}

MotorDriver::~MotorDriver()
{
    // gpioTerminate();
}

void MotorDriver::cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg)
{
    double v = msg->linear.x;
    double w = msg->angular.z;

    // Простейшая дифф.-кинематика
    double wheel_separation = 0.35; // м, подтянуть из параметров robоt_params.yaml
    left_speed_  = v - w * wheel_separation / 2.0;
    right_speed_ = v + w * wheel_separation / 2.0;

    // TODO: конвертировать в PWM/скорость моторов
    // setLeftMotor(left_speed_);
    // setRightMotor(right_speed_);
}

void MotorDriver::odomTimerCallback()
{
    // TODO: считать реальное смещение по энкодерам
    static double x = 0.0;
    static double y = 0.0;
    static double theta = 0.0;

    double dt = 0.02; // 20ms
    double v = (left_speed_ + right_speed_) / 2.0;
    double w = (right_speed_ - left_speed_) / 0.35;

    x     += v * dt * std::cos(theta);
    y     += v * dt * std::sin(theta);
    theta += w * dt;

    nav_msgs::msg::Odometry odom;
    odom.header.stamp = node_->now();
    odom.header.frame_id = "odom";
    odom.child_frame_id = "base_link";
    odom.pose.pose.position.x = x;
    odom.pose.pose.position.y = y;
    odom.pose.pose.orientation.z = std::sin(theta / 2.0);
    odom.pose.pose.orientation.w = std::cos(theta / 2.0);
    odom.twist.twist.linear.x = v;
    odom.twist.twist.angular.z = w;

    odom_pub_->publish(odom);
}
