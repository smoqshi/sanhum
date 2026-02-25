#include "arduino_sensors.h"
#include <sensor_msgs/msg/range.hpp>
#include <QTextStream>

ArduinoSensors::ArduinoSensors(std::shared_ptr<rclcpp::Node> node, QObject *parent)
    : QObject(parent),
    node_(std::move(node))
{
    // Порты можно взять из параметров
    serial_.setPortName("/dev/ttyUSB0");
    serial_.setBaudRate(QSerialPort::Baud115200);
    serial_.setDataBits(QSerialPort::Data8);
    serial_.setParity(QSerialPort::NoParity);
    serial_.setStopBits(QSerialPort::OneStop);
    serial_.setFlowControl(QSerialPort::NoFlowControl);
    serial_.open(QIODevice::ReadOnly);

    connect(&serial_, &QSerialPort::readyRead,
            this, &ArduinoSensors::onSerialReadyRead);

    for (size_t i = 0; i < range_pubs_.size(); ++i) {
        std::string topic = "/obstacle_sensor_" + std::to_string(i);
        range_pubs_[i] = node_->create_publisher<sensor_msgs::msg::Range>(topic, 10);
    }
}

void ArduinoSensors::onSerialReadyRead()
{
    static QByteArray buffer;
    buffer.append(serial_.readAll());

    int idx;
    while ((idx = buffer.indexOf('\n')) != -1) {
        QByteArray line = buffer.left(idx).trimmed();
        buffer.remove(0, idx + 1);

        if (line.isEmpty()) continue;

        // Ожидаемый формат: d1,d2,d3,d4,d5,d6 (в мм)
        QList<QByteArray> parts = line.split(',');
        if (parts.size() != 6) continue;

        for (int i = 0; i < 6; ++i) {
            bool ok = false;
            double dist_mm = parts[i].toDouble(&ok);
            if (!ok) continue;
            double dist_m = dist_mm / 1000.0;

            sensor_msgs::msg::Range msg;
            msg.header.stamp = node_->now();
            msg.header.frame_id = "sensor_" + std::to_string(i);
            msg.radiation_type = sensor_msgs::msg::Range::INFRARED;
            msg.field_of_view = 0.5;   // пример
            msg.min_range = 0.02;
            msg.max_range = 4.0;
            msg.range = dist_m;

            range_pubs_[i]->publish(msg);
        }
    }
}
