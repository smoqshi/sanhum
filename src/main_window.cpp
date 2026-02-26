#include "main_window.h"
#include "robot_view_widget.h"
#include "joystick_widget.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QKeyEvent>
#include <QtMath>
#include <QDebug>

MainWindow::MainWindow(std::shared_ptr<rclcpp::Node> node, QWidget *parent)
    : QMainWindow(parent)
    , ros_node_(std::move(node))
    , robot_namespace_("")
    , robot_connected_(false)
    , robot_view_(nullptr)
    , joystick_drive_(nullptr)
    , joystick_manip_(nullptr)
    , reset_button_(nullptr)
    , sim_timer_(nullptr)
    , gamepad_(nullptr)
    , sim_x_(0.0)
    , sim_y_(0.0)
    , sim_theta_(0.0)
    , sim_dt_ms_(20)
{
    QWidget *central = new QWidget(this);
    setCentralWidget(central);

    QHBoxLayout *mainLayout = new QHBoxLayout(central);

    robot_view_ = new RobotViewWidget(this);
    mainLayout->addWidget(robot_view_, 2);

    QVBoxLayout *sideLayout = new QVBoxLayout();

    joystick_drive_ = new JoystickWidget(this);
    joystick_drive_->setLabel(tr("Ходовая (левый стик)"));
    sideLayout->addWidget(joystick_drive_);

    joystick_manip_ = new JoystickWidget(this);
    joystick_manip_->setLabel(tr("Манипулятор (правый стик)"));
    sideLayout->addWidget(joystick_manip_);

    reset_button_ = new QPushButton(tr("Сброс положения"), this);
    sideLayout->addWidget(reset_button_);

    sideLayout->addStretch();
    mainLayout->addLayout(sideLayout, 1);

    sim_timer_ = new QTimer(this);
    sim_timer_->setInterval(sim_dt_ms_);
    connect(sim_timer_, &QTimer::timeout, this, &MainWindow::onSimUpdate);
    sim_timer_->start();

    connect(reset_button_, &QPushButton::clicked,
            this, &MainWindow::onResetPose);

    // Инициализация управления
    control_.drive_v = 0.0;
    control_.drive_w = 0.0;
    control_.manip_extend = 0.0;
    control_.manip_height = 0.0;
    control_.grip_closed = false;
    joints_.fill(0.0);

    // Подключаем геймпад
    gamepad_ = new GamepadControl(this);
    connect(gamepad_, &GamepadControl::stateChanged,
            this, [this](const GamepadControl::State &st) {
                control_.drive_v      = st.drive_v;
                control_.drive_w      = st.drive_w;
                control_.manip_extend = st.manip_extend;
                control_.manip_height = st.manip_height;
                control_.grip_closed  = st.grip_closed;

                joystick_drive_->setAxes(control_.drive_w, control_.drive_v);
                joystick_manip_->setAxes(control_.drive_w, control_.manip_extend);
            });

    setFocusPolicy(Qt::StrongFocus);
}

void MainWindow::setRobotNamespace(const QString &ns)
{
    robot_namespace_ = ns;
    if (!robot_namespace_.isEmpty()) {
        // Создаём publisher на /<ns>/cmd_vel
        std::string topic = robot_namespace_.toStdString() + "/cmd_vel";
        cmd_vel_pub_ = ros_node_->create_publisher<geometry_msgs::msg::Twist>(topic, 10);
        robot_connected_ = true;
        qDebug() << "ROS2 cmd_vel publisher created for namespace" << robot_namespace_;
    } else {
        cmd_vel_pub_.reset();
        robot_connected_ = false;
    }
}

void MainWindow::onResetPose()
{
    sim_x_ = 0.0;
    sim_y_ = 0.0;
    sim_theta_ = 0.0;
    robot_view_->setPose(sim_x_, sim_y_, sim_theta_);
}

// Обновление симуляции и публикация команд в ROS2
void MainWindow::onSimUpdate()
{
    const double dt = sim_dt_ms_ / 1000.0;

    // Управление гусеничной базой
    double u_v = control_.drive_v;
    double u_w = control_.drive_w;

    double u_L = qBound(-1.0, u_v - u_w, 1.0);
    double u_R = qBound(-1.0, u_v + u_w, 1.0);

    joystick_drive_->setAxes(u_w, u_v);

    const double b = 0.235;   // база, м
    const double v_max = 0.5; // м/с
    double v_L = u_L * v_max;
    double v_R = u_R * v_max;

    double v = 0.5 * (v_L + v_R);
    double w = (v_R - v_L) / b;

    sim_x_ += v * std::cos(sim_theta_) * dt;
    sim_y_ += v * std::sin(sim_theta_) * dt;
    sim_theta_ += w * dt;

    robot_view_->setPose(sim_x_, sim_y_, sim_theta_);
    robot_view_->setTrackSpeeds(v_L, v_R);

    // Манипулятор
    updateManipulatorModel(dt);

    // Публикация в ROS2, если есть реальный робот
    publishRosCommands(u_L, u_R);
}

// Простейшая кинематика манипулятора (для визуализации)
void MainWindow::updateManipulatorModel(double dt)
{
    const double speed_extend = 0.5;
    const double speed_height = 0.5;

    joints_[0] += control_.manip_extend * speed_extend * dt;
    joints_[1] += control_.manip_height * speed_height * dt;
    joints_[2] += control_.manip_extend * speed_extend * dt * 0.5;
    joints_[3] += control_.manip_height * speed_height * dt * 0.5;

    for (double &j : joints_) {
        j = qBound(-M_PI, j, M_PI);
    }

    robot_view_->setJointPositions(joints_);
    robot_view_->setGripperClosed(control_.grip_closed);
}

// Публикация команд в ROS2 (ходовая)
void MainWindow::publishRosCommands(double u_L, double u_R)
{
    if (!robot_connected_) return;
    if (!cmd_vel_pub_) return;

    const double b = 0.235;
    const double v_max = 0.5;

    double v_L = u_L * v_max;
    double v_R = u_R * v_max;

    double v = 0.5 * (v_L + v_R);
    double w = (v_R - v_L) / b;

    geometry_msgs::msg::Twist cmd;
    cmd.linear.x  = v;
    cmd.linear.y  = 0.0;
    cmd.linear.z  = 0.0;
    cmd.angular.x = 0.0;
    cmd.angular.y = 0.0;
    cmd.angular.z = w;

    cmd_vel_pub_->publish(cmd);
}

void MainWindow::keyPressEvent(QKeyEvent *event)
{
    if (event->isAutoRepeat()) {
        QMainWindow::keyPressEvent(event);
        return;
    }

    switch (event->key()) {
    // Ходовая
    case Qt::Key_W: control_.drive_v = 1.0; break;
    case Qt::Key_S: control_.drive_v = -1.0; break;
    case Qt::Key_A: control_.drive_w = -1.0; break;
    case Qt::Key_D: control_.drive_w = 1.0; break;

    // Манипулятор: удлинение
    case Qt::Key_I: control_.manip_extend = 1.0; break;
    case Qt::Key_K: control_.manip_extend = -1.0; break;

    // Манипулятор: высота
    case Qt::Key_U: control_.manip_height = 1.0; break;
    case Qt::Key_J: control_.manip_height = -1.0; break;

    // Захват
    case Qt::Key_O: control_.grip_closed = true; break;
    case Qt::Key_L: control_.grip_closed = false; break;

    default:
        break;
    }

    QMainWindow::keyPressEvent(event);
}

void MainWindow::keyReleaseEvent(QKeyEvent *event)
{
    if (event->isAutoRepeat()) {
        QMainWindow::keyReleaseEvent(event);
        return;
    }

    switch (event->key()) {
    case Qt::Key_W:
    case Qt::Key_S:
        control_.drive_v = 0.0;
        break;
    case Qt::Key_A:
    case Qt::Key_D:
        control_.drive_w = 0.0;
        break;
    case Qt::Key_I:
    case Qt::Key_K:
        control_.manip_extend = 0.0;
        break;
    case Qt::Key_U:
    case Qt::Key_J:
        control_.manip_height = 0.0;
        break;
    default:
        break;
    }

    QMainWindow::keyReleaseEvent(event);
}
