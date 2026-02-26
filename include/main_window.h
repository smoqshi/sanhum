#pragma once

#include <QMainWindow>
#include <QPushButton>
#include <QTimer>
#include <memory>
#include <array>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>

#include "gamepad_control.h"

class RobotViewWidget;
class JoystickWidget;

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    explicit MainWindow(std::shared_ptr<rclcpp::Node> node, QWidget *parent = nullptr);
    ~MainWindow() override = default;

    void setRobotNamespace(const QString &ns);

protected:
    void keyPressEvent(QKeyEvent *event) override;
    void keyReleaseEvent(QKeyEvent *event) override;

private slots:
    void onSimUpdate();
    void onResetPose();

private:
    struct ControlState {
        double drive_v;        // -1..1 линейная скорость
        double drive_w;        // -1..1 поворот
        double manip_extend;   // -1..1 удлинение
        double manip_height;   // -1..1 высота
        bool   grip_closed;    // захват
    };

    void updateManipulatorModel(double dt);
    void publishRosCommands(double u_L, double u_R);

    // ROS2
    std::shared_ptr<rclcpp::Node> ros_node_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
    // Для манипулятора и захвата предполагается собственный msg, но пока сделаем TODO.

    QString robot_namespace_;
    bool robot_connected_;

    // GUI
    RobotViewWidget *robot_view_;
    JoystickWidget  *joystick_drive_;
    JoystickWidget  *joystick_manip_;
    QPushButton     *reset_button_;
    QTimer          *sim_timer_;

    // Управление
    GamepadControl *gamepad_;
    ControlState    control_;
    std::array<double, 4> joints_;

    // Симуляция гусеничного робота
    double sim_x_;
    double sim_y_;
    double sim_theta_;
    int    sim_dt_ms_;
};
