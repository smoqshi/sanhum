#include <rclcpp/rclcpp.hpp>

#ifdef PLATFORM_WINDOWS
#include <QApplication>
#include "main_window.h"
#endif

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);

#ifdef PLATFORM_WINDOWS
    QApplication app(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("sanhum_gui");
    MainWindow w(node);
    w.show();
    auto spin_thread = std::thread([node]() { rclcpp::spin(node); });
    int ret = app.exec();
    rclcpp::shutdown();
    spin_thread.join();
    return ret;
#else
    auto node = std::make_shared<rclcpp::Node>("sanhum_robot");

    // здесь запускаешь headless‑логику:
    // MotorDriver, Esp32Driver, Cameras, YoloDetector, Behaviour и т.п.
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
#endif
}
