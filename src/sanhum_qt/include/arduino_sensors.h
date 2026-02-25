#pragma once

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/range.hpp>
#include <QSerialPort>

class ArduinoSensors : public QObject
{
    Q_OBJECT
public:
    explicit ArduinoSensors(std::shared_ptr<rclcpp::Node> node,
                            QObject *parent = nullptr);

private slots:
    void onSerialReadyRead();

private:
    std::shared_ptr<rclcpp::Node> node_;
    QSerialPort serial_;
    std::array<rclcpp::Publisher<sensor_msgs::msg::Range>::SharedPtr, 6> range_pubs_;
};
