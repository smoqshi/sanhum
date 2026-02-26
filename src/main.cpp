#include <QApplication>
#include <QInputDialog>
#include <QLineEdit>
#include <rclcpp/rclcpp.hpp>

#include "main_window.h"

int main(int argc, char *argv[])
{
    // Инициализация ROS2
    rclcpp::init(argc, argv);

    // Инициализация Qt
    QApplication app(argc, argv);

    // Диалог выбора: работаем ли с реальным роботом по ROS2
    bool ok = false;
    QString ns = QInputDialog::getText(
        nullptr,
        QObject::tr("Подключение к роботу"),
        QObject::tr("ROS2 namespace робота (оставь пустым для чистой симуляции):"),
        QLineEdit::Normal,
        QString(),
        &ok
    );

    auto ros_node = std::make_shared<rclcpp::Node>("sanhum_qt_node");

    MainWindow w(ros_node);
    if (ok && !ns.trimmed().isEmpty()) {
        w.setRobotNamespace(ns.trimmed());
    } else {
        w.setRobotNamespace(QString());
    }

    w.show();

    int ret = app.exec();
    rclcpp::shutdown();
    return ret;
}
