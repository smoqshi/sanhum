#include <rclcpp/rclcpp.hpp>
#include <memory>
#include <thread>

#ifdef PLATFORM_WINDOWS
#include <QApplication>
#include "main_window.h"
#else
#include "motor_driver.h"
#include "esp32_driver.h"
#include "arduino_sensors.h"
#endif

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);

#ifdef PLATFORM_WINDOWS
    // Windows/WSL: Qt GUI
    QApplication app(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("sanhum_gui");
    MainWindow w(node);
    w.show();
    
    auto spin_thread = std::thread([node]() { 
        rclcpp::spin(node); 
    });
    
    int ret = app.exec();
    rclcpp::shutdown();
    spin_thread.join();
    return ret;
    
#else
    // Raspberry Pi: headless ноды
    RCLCPP_INFO(rclcpp::get_logger("sanhum"), "Starting Sanhum Robot (headless)");
    
    // Создаём ноды для каждого драйвера
    auto motor_node = std::make_shared<rclcpp::Node>("motor_driver");
    auto esp32_node = std::make_shared<rclcpp::Node>("esp32_driver");
    auto sensor_node = std::make_shared<rclcpp::Node>("arduino_sensors");
    
    // Инициализируем драйверы
    auto motor_driver = std::make_shared<MotorDriver>(motor_node);
    auto esp32_driver = std::make_shared<Esp32Driver>(esp32_node);
    auto arduino_sensors = std::make_shared<ArduinoSensors>(sensor_node);
    
    // Запускаем многопоточную обработку
    std::vector<std::thread> threads;
    threads.emplace_back([&]() { rclcpp::spin(motor_node); });
    threads.emplace_back([&]() { rclcpp::spin(esp32_node); });
    threads.emplace_back([&]() { rclcpp::spin(sensor_node); });
    
    // Ждём завершения всех нод
    for (auto& t : threads) {
        t.join();
    }
    
    rclcpp::shutdown();
    return 0;
#endif
}
