#include "main_window.h"
#include "joystick_widget.h"
#include "robot_view_widget.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGroupBox>
#include <QApplication>

#include <cv_bridge/cv_bridge.h>
#include <opencv2/imgproc.hpp>

using namespace std::chrono_literals;

MainWindow::MainWindow(std::shared_ptr<rclcpp::Node> node, QWidget *parent)
    : QMainWindow(parent),
    node_(std::move(node))
{
    setupUi();
    setupRosInterfaces();
    setupTimers();
}

MainWindow::~MainWindow() = default;

void MainWindow::setupUi()
{
    tabs_ = new QTabWidget(this);

    QWidget *main_tab  = createMainTab();
    QWidget *diag_tab  = createDiagnosticsTab();
    QWidget *manip_tab = createManipulatorTab();

    tabs_->addTab(main_tab,  tr("Main"));
    tabs_->addTab(diag_tab,  tr("Diagnostics"));
    tabs_->addTab(manip_tab, tr("Manipulator"));

    setCentralWidget(tabs_);
    resize(1200, 750);
    setWindowTitle("Sanhum Robot Control");

    // Тёмная минималистичная тема
    QString style = R"(
        QMainWindow {
            background-color: #151515;
            color: #DDDDDD;
        }
        QWidget {
            background-color: #151515;
            color: #DDDDDD;
        }
        QTabWidget::pane {
            border-top: 1px solid #333333;
        }
        QTabBar::tab {
            background: #1d1d1d;
            color: #bbbbbb;
            padding: 4px 10px;
        }
        QTabBar::tab:selected {
            background: #242424;
            color: #ffffff;
        }
        QGroupBox {
            border: 1px solid #333333;
            margin-top: 6px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 2px 0 2px;
        }
        QLabel {
            color: #DDDDDD;
        }
        QSlider::groove:horizontal {
            height: 4px;
            background: #333333;
        }
        QSlider::handle:horizontal {
            width: 12px;
            background: #00A0FF;
            margin: -6px 0;
            border-radius: 6px;
        }
        QPushButton {
            background-color: #222222;
            border: 1px solid #444444;
            padding: 4px 8px;
        }
        QPushButton:hover {
            background-color: #2b2b2b;
        }
        QPushButton:checked {
            background-color: #005f99;
            border-color: #00A0FF;
        }
        QPlainTextEdit {
            background-color: #131313;
            border: 1px solid #333333;
            color: #DDDDDD;
        }
    )";
    qApp->setStyleSheet(style);
}

QWidget* MainWindow::createMainTab()
{
    auto *root = new QWidget(this);
    auto *main_layout = new QVBoxLayout(root);

    // Верх: чувствительность
    auto *sens_layout = new QHBoxLayout();
    trans_sens_slider_ = new QSlider(Qt::Horizontal, root);
    trans_sens_slider_->setRange(1, 300);
    trans_sens_slider_->setValue(100);
    trans_sens_label_ = new QLabel("Trans sens: 1.00", root);

    rot_sens_slider_ = new QSlider(Qt::Horizontal, root);
    rot_sens_slider_->setRange(1, 300);
    rot_sens_slider_->setValue(100);
    rot_sens_label_ = new QLabel("Rot sens: 1.00", root);

    sens_layout->addWidget(new QLabel("Trans:", root));
    sens_layout->addWidget(trans_sens_slider_);
    sens_layout->addWidget(trans_sens_label_);
    sens_layout->addSpacing(20);
    sens_layout->addWidget(new QLabel("Rot:", root));
    sens_layout->addWidget(rot_sens_slider_);
    sens_layout->addWidget(rot_sens_label_);

    main_layout->addLayout(sens_layout);

    // Средний блок: левый джойстик, камеры+робот, правый джойстик
    auto *middle_layout = new QHBoxLayout();

    left_joy_ = new JoystickWidget(root);
    right_joy_ = new JoystickWidget(root);

    auto *center_frame = new QFrame(root);
    auto *center_layout = new QVBoxLayout(center_frame);

    auto *cams_row = new QHBoxLayout();
    cam_left_view_  = new QLabel(center_frame);
    cam_mono_view_  = new QLabel(center_frame);
    cam_right_view_ = new QLabel(center_frame);

    for (QLabel *lab : {cam_left_view_, cam_mono_view_, cam_right_view_}) {
        lab->setMinimumSize(320, 240);
        lab->setStyleSheet("background-color: black;");
        lab->setAlignment(Qt::AlignCenter);
    }

    cams_row->addWidget(cam_left_view_);
    cams_row->addWidget(cam_mono_view_);
    cams_row->addWidget(cam_right_view_);

    robot_view_ = new RobotViewWidget(center_frame);

    center_layout->addLayout(cams_row);
    center_layout->addWidget(robot_view_);

    middle_layout->addWidget(left_joy_);
    middle_layout->addWidget(center_frame, 1);
    middle_layout->addWidget(right_joy_);

    main_layout->addLayout(middle_layout);

    // Нижний блок: авто-режим, телеметрия, подсказки
    auto *bottom_layout = new QHBoxLayout();

    auto *auto_layout = new QVBoxLayout();
    auto_mode_button_ = new QPushButton("AUTO MODE", root);
    auto_mode_button_->setCheckable(true);
    auto_mode_status_ = new QLabel("Auto: OFF", root);
    auto_layout->addWidget(auto_mode_button_);
    auto_layout->addWidget(auto_mode_status_);
    auto_layout->addStretch(1);

    pi_stats_text_ = new QPlainTextEdit(root);
    pi_stats_text_->setReadOnly(true);
    pi_stats_text_->setMinimumWidth(250);

    auto *hints_layout = new QVBoxLayout();
    auto *row1 = new QHBoxLayout();
    auto *row2 = new QHBoxLayout();

    hint_forward_       = new QPushButton("W / ↑", root);
    hint_back_          = new QPushButton("S / ↓", root);
    hint_left_          = new QPushButton("A / ←", root);
    hint_right_         = new QPushButton("D / →", root);
    hint_rotate_left_   = new QPushButton("Q", root);
    hint_rotate_right_  = new QPushButton("E", root);

    row1->addWidget(hint_rotate_left_);
    row1->addWidget(hint_forward_);
    row1->addWidget(hint_rotate_right_);
    row2->addWidget(hint_left_);
    row2->addWidget(hint_back_);
    row2->addWidget(hint_right_);

    hints_layout->addLayout(row1);
    hints_layout->addLayout(row2);
    hints_layout->addStretch(1);

    bottom_layout->addLayout(auto_layout);
    bottom_layout->addWidget(pi_stats_text_);
    bottom_layout->addLayout(hints_layout);

    main_layout->addLayout(bottom_layout);

    // связи
    connect(trans_sens_slider_, &QSlider::valueChanged,
            this, &MainWindow::onTransSensitivityChanged);
    connect(rot_sens_slider_, &QSlider::valueChanged,
            this, &MainWindow::onRotSensitivityChanged);
    connect(auto_mode_button_, &QPushButton::toggled,
            this, &MainWindow::onAutoModeToggled);

    connect(hint_forward_, &QPushButton::clicked, [this]() { left_joy_->setFocus(); });
    connect(hint_back_,    &QPushButton::clicked, [this]() { left_joy_->setFocus(); });
    connect(hint_left_,    &QPushButton::clicked, [this]() { right_joy_->setFocus(); });
    connect(hint_right_,   &QPushButton::clicked, [this]() { right_joy_->setFocus(); });

    connect(left_joy_, &JoystickWidget::positionChanged,
            this, [this](double x, double y) {
                Q_UNUSED(x);
                double v = y * trans_sensitivity_;
                geometry_msgs::msg::Twist msg;
                msg.linear.x = v;
                msg.angular.z = 0.0;
                cmd_vel_pub_->publish(msg);
            });

    connect(right_joy_, &JoystickWidget::positionChanged,
            this, [this](double x, double y) {
                Q_UNUSED(y);
                double w = x * rot_sensitivity_;
                geometry_msgs::msg::Twist msg;
                msg.linear.x = 0.0;
                msg.angular.z = w;
                cmd_vel_pub_->publish(msg);
            });

    return root;
}

QWidget* MainWindow::createDiagnosticsTab()
{
    auto *root = new QWidget(this);
    auto *layout = new QVBoxLayout(root);

    odom_label_ = new QLabel("Odom: x=0.0 y=0.0 theta=0.0", root);
    diag_text_ = new QPlainTextEdit(root);
    diag_text_->setReadOnly(true);

    layout->addWidget(odom_label_);
    layout->addWidget(diag_text_);

    return root;
}

QWidget* MainWindow::createManipulatorTab()
{
    auto *root = new QWidget(this);
    auto *layout = new QVBoxLayout(root);

    joint_state_label_ = new QLabel("Joint states: -", root);
    layout->addWidget(joint_state_label_);
    layout->addStretch(1);

    return root;
}

void MainWindow::setupRosInterfaces()
{
    cmd_vel_pub_ = node_->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);

    odom_sub_ = node_->create_subscription<nav_msgs::msg::Odometry>(
        "/odom", 10,
        [this](nav_msgs::msg::Odometry::SharedPtr msg) {
            pose_x_ = msg->pose.pose.position.x;
            pose_y_ = msg->pose.pose.position.y;
            double z = msg->pose.pose.orientation.z;
            double w = msg->pose.pose.orientation.w;
            pose_theta_ = 2.0 * std::atan2(z, w);
            odom_label_->setText(
                QString("Odom: x=%1 y=%2 theta=%3")
                    .arg(pose_x_, 0, 'f', 2)
                    .arg(pose_y_, 0, 'f', 2)
                    .arg(pose_theta_, 0, 'f', 2));
            robot_view_->setPose(pose_x_, pose_y_, pose_theta_);
        });

    diag_sub_ = node_->create_subscription<std_msgs::msg::String>(
        "/diagnostics", 10,
        [this](std_msgs::msg::String::SharedPtr msg) {
            diag_text_->appendPlainText(QString::fromStdString(msg->data));
        });

    cam_left_sub_ = node_->create_subscription<sensor_msgs::msg::Image>(
        "/stereo/left/image_raw", 5,
        [this](sensor_msgs::msg::Image::SharedPtr msg) {
            try {
                cv::Mat img = cv_bridge::toCvCopy(msg, "bgr8")->image;
                cv::cvtColor(img, img, cv::COLOR_BGR2RGB);
                QImage qimg(img.data, img.cols, img.rows, img.step, QImage::Format_RGB888);
                last_left_frame_ = qimg.copy();
            } catch (...) {}
        });

    cam_right_sub_ = node_->create_subscription<sensor_msgs::msg::Image>(
        "/stereo/right/image_raw", 5,
        [this](sensor_msgs::msg::Image::SharedPtr msg) {
            try {
                cv::Mat img = cv_bridge::toCvCopy(msg, "bgr8")->image;
                cv::cvtColor(img, img, cv::COLOR_BGR2RGB);
                QImage qimg(img.data, img.cols, img.rows, img.step, QImage::Format_RGB888);
                last_right_frame_ = qimg.copy();
            } catch (...) {}
        });

    cam_mono_sub_ = node_->create_subscription<sensor_msgs::msg::Image>(
        "/mono/image_raw", 5,
        [this](sensor_msgs::msg::Image::SharedPtr msg) {
            try {
                cv::Mat img = cv_bridge::toCvCopy(msg, "bgr8")->image;
                cv::cvtColor(img, img, cv::COLOR_BGR2RGB);
                QImage qimg(img.data, img.cols, img.rows, img.step, QImage::Format_RGB888);
                last_mono_frame_ = qimg.copy();
            } catch (...) {}
        });

    pi_stats_sub_ = node_->create_subscription<std_msgs::msg::String>(
        "/pi_stats", 10,
        [this](std_msgs::msg::String::SharedPtr msg) {
            pi_stats_text_->setPlainText(QString::fromStdString(msg->data));
        });

    joint_state_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
        "/manipulator/joint_states", 10,
        [this](sensor_msgs::msg::JointState::SharedPtr msg) {
            QString text("Joint states: ");
            for (size_t i = 0; i < msg->name.size(); ++i) {
                double pos = (i < msg->position.size()) ? msg->position[i] : 0.0;
                text += QString("%1=%2 ")
                            .arg(QString::fromStdString(msg->name[i]))
                            .arg(pos, 0, 'f', 2);
            }
            joint_state_label_->setText(text);
            for (int i = 0; i < 4 && i < static_cast<int>(msg->position.size()); ++i)
                joint_positions_[i] = msg->position[i];
            robot_view_->setJointPositions(joint_positions_);
        });

#ifdef PLATFORM_WINDOWS
    wifi_server_ = new WifiServer(node_, this);
    gamepad_ = new GamepadControl(node_, this);
#else
    robot_client_ = new RobotClient(node_, this);
    motor_driver_ = new MotorDriver(node_);
    esp32_driver_ = new Esp32Driver(node_, this);
    arduino_sensors_ = new ArduinoSensors(node_, this);
    cameras_ = new Cameras(node_);
    yolo_ = new YoloDetector(node_);
#endif
}

void MainWindow::setupTimers()
{
    connect(&diagnostics_timer_, &QTimer::timeout,
            this, &MainWindow::updateDiagnostics);
    diagnostics_timer_.start(100);

    connect(&video_timer_, &QTimer::timeout,
            this, &MainWindow::updateVideoFrames);
    video_timer_.start(50);
}

void MainWindow::updateDiagnostics()
{
    // здесь можно добавить дополнительные обновления, если нужно
}

void MainWindow::updateVideoFrames()
{
    auto updateView = [](QLabel *label, const QImage &img) {
        if (!label || img.isNull()) return;
        QPixmap pix = QPixmap::fromImage(img).scaled(
            label->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation);
        label->setPixmap(pix);
    };

    updateView(cam_left_view_,  last_left_frame_);
    updateView(cam_right_view_, last_right_frame_);
    updateView(cam_mono_view_,  last_mono_frame_);
}

void MainWindow::onTransSensitivityChanged(int value)
{
    trans_sensitivity_ = value / 100.0;
    trans_sens_label_->setText(
        QString("Trans sens: %1").arg(trans_sensitivity_, 0, 'f', 2));
}

void MainWindow::onRotSensitivityChanged(int value)
{
    rot_sensitivity_ = value / 100.0;
    rot_sens_label_->setText(
        QString("Rot sens: %1").arg(rot_sensitivity_, 0, 'f', 2));
}

void MainWindow::onAutoModeToggled(bool checked)
{
    auto_mode_status_->setText(checked ? "Auto: ON" : "Auto: OFF");

    auto pub = node_->create_publisher<std_msgs::msg::String>("/behavior_mode", 10);
    std_msgs::msg::String msg;
    msg.data = checked ? "Auto" : "Manual";
    pub->publish(msg);
}
