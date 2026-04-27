#include "motor_driver.h"
#include <chrono>
#include <cmath>

using namespace std::chrono_literals;

// Dummy GPIO implementation for testing without hardware
// TODO: Replace with actual pigpio library calls for real hardware
namespace {
    // Simulated GPIO pin states
    int gpio_left_motor_1 = 0;
    int gpio_left_motor_2 = 0;
    int gpio_right_motor_1 = 0;
    int gpio_right_motor_2 = 0;

    // Dummy GPIO functions
    void gpioSetMode(int pin, int mode) {
        // TODO: Replace with gpioSetMode(pin, mode) from pigpio
    }

    void gpioWrite(int pin, int level) {
        // TODO: Replace with gpioWrite(pin, level) from pigpio
        // For now, just track the state
        if (pin == 17) gpio_left_motor_1 = level;
        if (pin == 27) gpio_left_motor_2 = level;
        if (pin == 22) gpio_right_motor_1 = level;
        if (pin == 23) gpio_right_motor_2 = level;
    }

    int gpioInitialise() {
        // TODO: Replace with gpioInitialise() from pigpio
        return 0; // Return 0 on success
    }

    void gpioTerminate() {
        // TODO: Replace with gpioTerminate() from pigpio
    }
}

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

    // Initialize dummy GPIO
    gpioInitialise();

    // Set GPIO pins to output mode
    gpioSetMode(17, 1); // left_motor_1
    gpioSetMode(27, 1); // left_motor_2
    gpioSetMode(22, 1); // right_motor_1
    gpioSetMode(23, 1); // right_motor_2
}

MotorDriver::~MotorDriver()
{
    // Stop motors and cleanup
    gpioWrite(17, 0);
    gpioWrite(27, 0);
    gpioWrite(22, 0);
    gpioWrite(23, 0);
    gpioTerminate();
}

void MotorDriver::cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg)
{
    double v = msg->linear.x;
    double w = msg->angular.z;

    // Простейшая дифф.-кинематика
    double wheel_separation = 0.35; // м, подтянуть из параметров robоt_params.yaml
    left_speed_  = v - w * wheel_separation / 2.0;
    right_speed_ = v + w * wheel_separation / 2.0;

    // Dummy motor control - set GPIO pins based on speed
    // TODO: Replace with actual PWM control using pigpio
    if (left_speed_ > 0.1) {
        gpioWrite(17, 1); // Forward
        gpioWrite(27, 0);
    } else if (left_speed_ < -0.1) {
        gpioWrite(17, 0); // Reverse
        gpioWrite(27, 1);
    } else {
        gpioWrite(17, 0); // Stop
        gpioWrite(27, 0);
    }

    if (right_speed_ > 0.1) {
        gpioWrite(22, 1); // Forward
        gpioWrite(23, 0);
    } else if (right_speed_ < -0.1) {
        gpioWrite(22, 0); // Reverse
        gpioWrite(23, 1);
    } else {
        gpioWrite(22, 0); // Stop
        gpioWrite(23, 0);
    }
}

void MotorDriver::odomTimerCallback()
{
    // Dummy encoder reading - simulate odometry from commanded speeds
    // TODO: Replace with actual encoder reading using pigpio
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
