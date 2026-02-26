#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>

struct ControlState {
    double drive_v;
    double drive_w;
    double manip_extend;
    double manip_height;
    bool   grip_closed;
};

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    explicit MainWindow(std::shared_ptr<rclcpp::Node> node, QWidget *parent = nullptr);
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

    std::shared_ptr<rclcpp::Node> ros_node_;

    // ROS2 publishers
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
    rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr manip_cmd_pub_;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr grip_pub_;

    QTcpSocket *robot_socket_;
    bool robot_connected_;
    QString robot_host_;
    QTimer *sim_timer_;

    RobotViewWidget *robot_view_;
    JoystickWidget *joystick_drive_;
    JoystickWidget *joystick_manip_;
    QPushButton *reset_button_;
    GamepadControl *gamepad_;

    ControlState control_;
    std::array<double,4> joints_;

    double sim_x_;
    double sim_y_;
    double sim_theta_;
    int sim_dt_ms_;
};

