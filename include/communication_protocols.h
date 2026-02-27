
#ifndef COMMUNICATION_PROTOCOLS_H
#define COMMUNICATION_PROTOCOLS_H

#include "geometry_msgs/msg/twist.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"

namespace sanhum {

// Topics for robot control and feedback
constexpr char kCmdVelTopic[] = "/cmd_vel";
constexpr char kOdometryTopic[] = "/odom";

// Topics for sensor data
constexpr char kImuTopic[] = "/imu/data";
constexpr char kArduinoSensorsTopic[] = "/arduino/sensors";

// Topics for manipulator control
constexpr char kManipulatorControlTopic[] = "/manipulator/control";

// Message types
using TwistMsg = geometry_msgs::msg::Twist;
using OdometryMsg = nav_msgs::msg::Odometry;
using ImuMsg = sensor_msgs::msg::Imu;
using Float32MultiArrayMsg = std_msgs::msg::Float32MultiArray;

} // namespace sanhum

#endif // COMMUNICATION_PROTOCOLS_H
