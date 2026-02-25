#pragma once

#include <QObject>
#include <QTcpSocket>
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <std_msgs/msg/string.hpp>

class RobotClient : public QObject
{
    Q_OBJECT
public:
    explicit RobotClient(std::shared_ptr<rclcpp::Node> node,
                         QObject *parent = nullptr);

private slots:
    void connectToServer();
    void onConnected();
    void onReadyRead();
    void onDisconnected();

private:
    void sendStatusJson();
    void processServerJson(const QByteArray &data);

    std::shared_ptr<rclcpp::Node> node_;
    QTcpSocket socket_;

    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr diag_pub_;
};
