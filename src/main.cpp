#include <QApplication>
#include <QInputDialog>
#include <QHostAddress>
#include <rclcpp/rclcpp.hpp>
#include "main_window.h"

int main(int argc, char *argv[])
{
    // Инициализация ROS2
    rclcpp::init(argc, argv);

    // Инициализация Qt
    QApplication app(argc, argv);

    // Простое окно выбора режима подключения:
    // 1) Ввести IP Raspberry Pi (TCP к роботу)
    // 2) Пустая строка -> чистая симуляция
    bool ok = false;
    QString ip = QInputDialog::getText(
        nullptr,
        QObject::tr("Подключение к роботу"),
        QObject::tr("IP адрес Raspberry Pi (оставь пустым для симуляции):"),
        QLineEdit::Normal,
        QString(),
        &ok
    );

    // Инициализация ROS-узла
    auto ros_node = std::make_shared<rclcpp::Node>("sanhum_qt_node");

    MainWindow w(ros_node);
    if (ok) {
        if (!ip.trimmed().isEmpty()) {
            // Передаём IP в главное окно; оно само попробует установить TCP
            w.setRobotHost(ip.trimmed());
        } else {
            // Пустой IP -> только симуляция, robotHost оставляем пустым
            w.setRobotHost(QString());
        }
    } else {
        // Пользователь закрыл диалог — работаем в симуляции
        w.setRobotHost(QString());
    }

    w.show();

    int ret = app.exec();
    rclcpp::shutdown();
    return ret;
}
