#pragma once

#include <QMainWindow>
#include <QPushButton>
#include <QTcpSocket>
#include <QTimer>
#include <array>
#include <memory>

#include <rclcpp/rclcpp.hpp>

class RobotViewWidget;
class JoystickWidget;
class GamepadControl;

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    explicit MainWindow(std::shared_ptr<rclcpp::Node> node,
                        QWidget *parent = nullptr);

    void setRobotHost(const QString &ip);

protected:
    void keyPressEvent(QKeyEvent *event) override;
    void keyReleaseEvent(QKeyEvent *event) override;

private slots:
    void onRobotConnected();
    void onRobotDisconnected();
    void onResetPose();
    void onSimUpdate();

private:
    void updateManipulatorModel(double dt);
    void sendDriveAndManipulatorCommand(double u_L, double u_R);

    struct ControlState {
        double drive_v;        // -1..1, линейная скорость шасси
        double drive_w;        // -1..1, поворот
        double manip_extend;   // -1..1, удлинение манипулятора
        double manip_height;   // -1..1, высота манипулятора
        bool   grip_closed;    // состояние захвата
    };

    std::shared_ptr<rclcpp::Node> ros_node_;

    RobotViewWidget *robot_view_;
    JoystickWidget *joystick_drive_;
    JoystickWidget *joystick_manip_;
    QPushButton *reset_button_;

    QTcpSocket *robot_socket_;
    bool robot_connected_;
    QString robot_host_;

    double sim_x_;
    double sim_y_;
    double sim_theta_;
    int    sim_dt_ms_;
    QTimer *sim_timer_;

    GamepadControl *gamepad_;

    ControlState control_;
    std::array<double, 4> joints_;
};
