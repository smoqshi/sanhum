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
int sim_dt_ms_;
QTimer *sim_timer_;

GamepadControl *gamepad_;

struct ControlState {
    double drive_v;
    double drive_w;
    double manip_extend;
    double manip_height;
    bool   grip_closed;
} control_;

std::array<double, 4> joints_;
