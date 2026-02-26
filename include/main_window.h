#ifndef MAIN_WINDOW_H
#define MAIN_WINDOW_H

#include <QMainWindow>
#include <QPushButton>
#include <QTimer>
#include <QTcpSocket>
#include <memory>
#include <array>

#include <rclcpp/rclcpp.hpp>

class RobotViewWidget;
class JoystickWidget;

// Абстрактное состояние управления от геймпада/клавиатуры
struct ControlState
{
    double drive_v;        // -1..1, движение вперёд/назад (левый стик Y / W,S)
    double drive_w;        // -1..1, поворот (правый стик X / A,D)
    double manip_extend;   // -1..1, удлинение манипулятора (правый стик Y / I,K)
    double manip_height;   // -1..1, высота манипулятора (LT / LT+LB / U,J)
    bool   grip_closed;    // захват закрыт (RT / O)
};

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(std::shared_ptr<rclcpp::Node> node,
                        QWidget *parent = nullptr);

    // Задать IP Raspberry Pi; пустая строка -> чистая симуляция
    void setRobotHost(const QString &ip);

protected:
    void keyPressEvent(QKeyEvent *event) override;
    void keyReleaseEvent(QKeyEvent *event) override;

private slots:
    void onSimUpdate();
    void onResetPose();
    void onRobotConnected();
    void onRobotDisconnected();

private:
    void sendDriveAndManipulatorCommand(double u_L, double u_R);
    void updateManipulatorModel(double dt);

private:
    // ROS2
    std::shared_ptr<rclcpp::Node> ros_node_;

    // Виджеты
    RobotViewWidget *robot_view_;
    JoystickWidget  *joystick_drive_;
    JoystickWidget  *joystick_manip_;
    QPushButton     *reset_button_;

    // Сетевое соединение с Raspberry Pi
    QTcpSocket *robot_socket_;
    bool        robot_connected_;
    QString     robot_host_;

    // Таймер симуляции
    QTimer *sim_timer_;
    int     sim_dt_ms_;

    // Состояние симуляции гусеничного шасси
    double sim_x_;      // м
    double sim_y_;      // м
    double sim_theta_;  // рад

    // Состояние манипулятора (4 звена)
    std::array<double, 4> joints_;

    // Абстрактное состояние управления (геймпад + клавиатура)
    ControlState control_;
};

#endif // MAIN_WINDOW_H
