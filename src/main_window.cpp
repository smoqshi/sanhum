#include "main_window.h"

#include "robot_view_widget.h"
#include "joystick_widget.h"
#include "gamepad_control.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QTimer>
#include <QKeyEvent>
#include <QTcpSocket>
#include <QDebug>
#include <QtMath>

// Конструктор
MainWindow::MainWindow(std::shared_ptr<rclcpp::Node> node, QWidget *parent)
    : QMainWindow(parent)
    , ros_node_(std::move(node))
    , robot_view_(nullptr)
    , joystick_drive_(nullptr)
    , joystick_manip_(nullptr)
    , reset_button_(nullptr)
    , robot_socket_(new QTcpSocket(this))
    , robot_connected_(false)
    , sim_x_(0.0)
    , sim_y_(0.0)
    , sim_theta_(0.0)
    , sim_dt_ms_(20)
    , sim_timer_(new QTimer(this))
    , gamepad_(nullptr)
{
    // Центральный виджет и лэйаут
    QWidget *central = new QWidget(this);
    setCentralWidget(central);

    QHBoxLayout *mainLayout = new QHBoxLayout(central);

    // Слева: круглая арена с роботом и манипулятором
    robot_view_ = new RobotViewWidget(this);
    mainLayout->addWidget(robot_view_, /*stretch*/ 2);

    // Справа: два виджета джойстиков + кнопка сброса
    QVBoxLayout *sideLayout = new QVBoxLayout();

    joystick_drive_ = new JoystickWidget(this);   // левый стик: движение
    joystick_drive_->setLabel(tr("Ходовая (левый стик / WASD)"));
    sideLayout->addWidget(joystick_drive_);

    joystick_manip_ = new JoystickWidget(this);   // правый стик: манипулятор
    joystick_manip_->setLabel(tr("Манипулятор (правый стик / IJKUO)"));
    sideLayout->addWidget(joystick_manip_);

    reset_button_ = new QPushButton(tr("Сброс положения"), this);
    sideLayout->addWidget(reset_button_);

    sideLayout->addStretch();
    mainLayout->addLayout(sideLayout, /*stretch*/ 1);

    // Таймер симуляции
    sim_timer_->setInterval(sim_dt_ms_);
    connect(sim_timer_, &QTimer::timeout, this, &MainWindow::onSimUpdate);
    sim_timer_->start();

    // Сигналы/слоты для TCP‑подключения к роботу
    connect(robot_socket_, &QTcpSocket::connected,
            this, &MainWindow::onRobotConnected);
    connect(robot_socket_, &QTcpSocket::disconnected,
            this, &MainWindow::onRobotDisconnected);

    // Кнопка сброса положения
    connect(reset_button_, &QPushButton::clicked,
            this, &MainWindow::onResetPose);

    // Инициализируем виртуальное состояние управления
    control_.drive_v = 0.0;
    control_.drive_w = 0.0;
    control_.manip_extend = 0.0;
    control_.manip_height = 0.0;
    control_.grip_closed = false;

    joints_.fill(0.0);

    // Инициализация геймпада
    gamepad_ = new GamepadControl(this);
    connect(gamepad_, &GamepadControl::stateChanged,
            this, [this](const GamepadControl::State &st) {
                control_.drive_v      = st.drive_v;
                control_.drive_w      = st.drive_w;
                control_.manip_extend = st.manip_extend;
                control_.manip_height = st.manip_height;
                control_.grip_closed  = st.grip_closed;

                // Обновляем визуализацию джойстиков
                joystick_drive_->setAxes(control_.drive_w, control_.drive_v);
                joystick_manip_->setAxes(control_.drive_w, control_.manip_extend);
            });

    setFocusPolicy(Qt::StrongFocus);
}

// Установка адреса робота и попытка подключения
void MainWindow::setRobotHost(const QString &ip)
{
    robot_host_ = ip;
    if (!robot_host_.isEmpty()) {
        robot_socket_->abort();
        // Простой локальный TCP‑протокол, порт 5555
        robot_socket_->connectToHost(robot_host_, 5555);
    } else {
        robot_socket_->abort();
        robot_connected_ = false;
    }
}

void MainWindow::onRobotConnected()
{
    robot_connected_ = true;
    qDebug() << "Connected to robot at" << robot_host_;
}

void MainWindow::onRobotDisconnected()
{
    robot_connected_ = false;
    qDebug() << "Disconnected from robot";
}

// Сброс позы робота в симуляции
void MainWindow::onResetPose()
{
    sim_x_ = 0.0;
    sim_y_ = 0.0;
    sim_theta_ = 0.0;
    robot_view_->setPose(sim_x_, sim_y_, sim_theta_);
}

// Обновление симуляции и отправка команд роботу
void MainWindow::onSimUpdate()
{
    const double dt = sim_dt_ms_ / 1000.0;

    // Преобразуем абстрактные команды в нормализованные PWM гусениц
    double u_v = control_.drive_v;   // -1..1, вперёд/назад
    double u_w = control_.drive_w;   // -1..1, поворот

    double u_L = qBound(-1.0, u_v - u_w, 1.0);
    double u_R = qBound(-1.0, u_v + u_w, 1.0);

    // Обновляем виджет джойстика для ходовой
    joystick_drive_->setAxes(u_w, u_v); // X=turn, Y=forward

    // Параметры шасси (гусеничный, как дифф‑робот)
    const double b = 0.235;      // расстояние между центрами гусениц, м
    const double v_max = 0.5;    // м/с (пример, подстрой по факту)

    double v_L = u_L * v_max;
    double v_R = u_R * v_max;

    double v = 0.5 * (v_L + v_R);
    double w = (v_R - v_L) / b;

    // Одометрия
    sim_x_ += v * std::cos(sim_theta_) * dt;
    sim_y_ += v * std::sin(sim_theta_) * dt;
    sim_theta_ += w * dt;

    // Обновляем визуализацию корпуса и гусениц
    robot_view_->setPose(sim_x_, sim_y_, sim_theta_);
    robot_view_->setTrackSpeeds(v_L, v_R);

    // Обновление модели манипулятора
    updateManipulatorModel(dt);

    // Если робот подключен — отправляем команды по TCP
    if (robot_connected_) {
        sendDriveAndManipulatorCommand(u_L, u_R);
    }
}

// Простая «динамика» манипулятора по осям управления
void MainWindow::updateManipulatorModel(double dt)
{
    const double speed_extend = 0.5; // рад/с эквивалент
    const double speed_height = 0.5; // рад/с

    // Условное распределение влияния управляющих сигналов
    joints_[0] += control_.manip_extend * speed_extend * dt;
    joints_[1] += control_.manip_height * speed_height * dt;
    joints_[2] += control_.manip_extend * speed_extend * dt * 0.5;
    joints_[3] += control_.manip_height * speed_height * dt * 0.5;

    // Ограничения диапазонов
    for (double &j : joints_) {
        j = qBound(-M_PI, j, M_PI);
    }

    robot_view_->setJointPositions(joints_);
    robot_view_->setGripperClosed(control_.grip_closed);
}

// Простейший текстовый протокол для Raspberry Pi
void MainWindow::sendDriveAndManipulatorCommand(double u_L, double u_R)
{
    if (!robot_connected_) return;
    if (robot_socket_->state() != QAbstractSocket::ConnectedState) return;

    // DRIVE L=<float> R=<float> J1=<float> J2=<float> J3=<float> J4=<float> GRIP=<0|1>\n
    QString cmd = QString("DRIVE L=%1 R=%2 J1=%3 J2=%4 J3=%5 J4=%6 GRIP=%7\n")
                      .arg(u_L, 0, 'f', 3)
                      .arg(u_R, 0, 'f', 3)
                      .arg(joints_[0], 0, 'f', 3)
                      .arg(joints_[1], 0, 'f', 3)
                      .arg(joints_[2], 0, 'f', 3)
                      .arg(joints_[3], 0, 'f', 3)
                      .arg(control_.grip_closed ? 1 : 0);

    robot_socket_->write(cmd.toUtf8());
    robot_socket_->flush();
}

// Обработка нажатий клавиш — дублируют управление геймпада
void MainWindow::keyPressEvent(QKeyEvent *event)
{
    if (event->isAutoRepeat()) {
        QMainWindow::keyPressEvent(event);
        return;
    }

    switch (event->key()) {
    // Ходовая (аналог левого стика)
    case Qt::Key_W: control_.drive_v = 1.0; break;
    case Qt::Key_S: control_.drive_v = -1.0; break;
    case Qt::Key_A: control_.drive_w = -1.0; break;
    case Qt::Key_D: control_.drive_w = 1.0; break;

    // Манипулятор: удлинение (аналог правый стик Y)
    case Qt::Key_I: control_.manip_extend = 1.0; break;
    case Qt::Key_K: control_.manip_extend = -1.0; break;

    // Манипулятор: высота (аналог LT / LT+LB)
    case Qt::Key_U: control_.manip_height = 1.0; break;
    case Qt::Key_J: control_.manip_height = -1.0; break;

    // Захват (аналог RT / RT+RB)
    case Qt::Key_O: control_.grip_closed = true; break;
    case Qt::Key_L: control_.grip_closed = false; break;

    default:
        break;
    }

    QMainWindow::keyPressEvent(event);
}

// Сброс значений при отпускании клавиш
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
