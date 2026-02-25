#pragma once

#include <QObject>
#include <QTcpServer>
#include <QTcpSocket>
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <std_msgs/msg/string.hpp>

class WifiServer : public QObject
{
    Q_OBJECT
public:
    explicit WifiServer(std::shared_ptr<rclcpp::Node> node, QObject *parent = nullptr);

private slots:
    void onNewConnection();
    void onClientData();
    void onClientDisconnected();

private:
    void processJsonMessage(const QByteArray &data);
    void sendImageToClient(const sensor_msgs::msg::Image::SharedPtr &msg);
    void sendDiagnosticsToClient(const std_msgs::msg::String::SharedPtr &msg);

    std::shared_ptr<rclcpp::Node> node_;
    QTcpServer server_;
    QTcpSocket *client_{nullptr};

    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr mono_sub_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr diag_sub_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
};
