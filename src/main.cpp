#include <QApplication>
#include <rclcpp/rclcpp.hpp>
#include "main_window.h"

int main(int argc, char *argv[])
{
    // Инициализация ROS2
    rclcpp::init(argc, argv);

    // Инициализация Qt
    QApplication app(argc, argv);

    auto ros_node = std::make_shared<rclcpp::Node>("sanhum_qt_node");
    MainWindow w(ros_node);
    w.show();

    int ret = app.exec();

    rclcpp::shutdown();
    return ret;
}
