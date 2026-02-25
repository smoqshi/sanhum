#pragma once

#include <QMainWindow>
#include <QTimer>
#include <QLabel>
#include <QSlider>
#include <QPushButton>
#include <QTabWidget>
#include <QPlainTextEdit>
#include <QComboBox>
#include <array>
#include <memory>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <std_msgs/msg/string.hpp>

#ifdef PLATFORM_WINDOWS
#include "wifi_server.h"
//#include "gamepad_control.h"
#else
#include "robot_client.h"
#include "motor_driver.h"
#include "esp32_driver.h"
#include "arduino_sensors.h"
#include "cameras.h"
#include "yolo_detector.h"
#endif

class JoystickWidget;
class RobotViewWidget;

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    explicit MainWindow(std::shared_ptr<rclcpp::Node> node, QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void updateDiagnostics();
    void updateVideoFrames();

    void onTransSensitivityChanged(int value);
    void onRotSensitivityChanged(int value);
    void onAutoModeToggled(bool checked);

private:
    void setupUi();
    QWidget* createMainTab();
    QWidget* createDiagnosticsTab();
    QWidget* createManipulatorTab();

    void setupRosInterfaces();
    void setupTimers();

    std::shared_ptr<rclcpp::Node> node_;

    // ROS2
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr diag_sub_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr cam_left_sub_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr cam_right_sub_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr cam_mono_sub_;
    rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr pi_stats_sub_;

#ifdef PLATFORM_WINDOWS
    WifiServer *wifi_server_{nullptr};
    //GamepadControl *gamepad_{nullptr};
#else
    RobotClient *robot_client_{nullptr};
    MotorDriver *motor_driver_{nullptr};
    Esp32Driver *esp32_driver_{nullptr};
    ArduinoSensors *arduino_sensors_{nullptr};
    Cameras *cameras_{nullptr};
    YoloDetector *yolo_{nullptr};
#endif

    QTabWidget *tabs_{nullptr};

    // Главная вкладка
    JoystickWidget *left_joy_{nullptr};
    JoystickWidget *right_joy_{nullptr};

    QSlider *trans_sens_slider_{nullptr};
    QSlider *rot_sens_slider_{nullptr};
    QLabel  *trans_sens_label_{nullptr};
    QLabel  *rot_sens_label_{nullptr};

    QLabel *cam_left_view_{nullptr};
    QLabel *cam_right_view_{nullptr};
    QLabel *cam_mono_view_{nullptr};

    RobotViewWidget *robot_view_{nullptr};

    QPushButton *auto_mode_button_{nullptr};
    QLabel *auto_mode_status_{nullptr};

    QPushButton *hint_forward_{nullptr};
    QPushButton *hint_back_{nullptr};
    QPushButton *hint_left_{nullptr};
    QPushButton *hint_right_{nullptr};
    QPushButton *hint_rotate_left_{nullptr};
    QPushButton *hint_rotate_right_{nullptr};

    QPlainTextEdit *pi_stats_text_{nullptr};

    // Диагностика/манипулятор (простые элементы)
    QLabel *odom_label_{nullptr};
    QPlainTextEdit *diag_text_{nullptr};
    QLabel *joint_state_label_{nullptr};

    QTimer diagnostics_timer_;
    QTimer video_timer_;

    QImage last_left_frame_;
    QImage last_right_frame_;
    QImage last_mono_frame_;

    double trans_sensitivity_{1.0};
    double rot_sensitivity_{1.0};

    double pose_x_{0.0};
    double pose_y_{0.0};
    double pose_theta_{0.0};
    std::array<double,4> joint_positions_{{0,0,0,0}};
};


