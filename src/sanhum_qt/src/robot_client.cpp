#include "robot_client.h"
#include <QTimer>
#include <QJsonDocument>
#include <QJsonObject>

RobotClient::RobotClient(std::shared_ptr<rclcpp::Node> node, QObject *parent)
    : QObject(parent),
    node_(std::move(node))
{
    diag_pub_ = node_->create_publisher<std_msgs::msg::String>("/tcp_status", 10);

    cmd_vel_sub_ = node_->create_subscription<geometry_msgs::msg::Twist>(
        "/cmd_vel", 10,
        [this](geometry_msgs::msg::Twist::SharedPtr msg) {
            if (socket_.state() == QAbstractSocket::ConnectedState) {
                QJsonObject obj;
                obj["type"] = "cmd_vel";
                obj["linear_x"] = msg->linear.x;
                obj["angular_z"] = msg->angular.z;
                QJsonDocument doc(obj);
                socket_.write(doc.toJson(QJsonDocument::Compact));
                socket_.write("\n");
            }
        });

    connect(&socket_, &QTcpSocket::connected,
            this, &RobotClient::onConnected);
    connect(&socket_, &QTcpSocket::readyRead,
            this, &RobotClient::onReadyRead);
    connect(&socket_, &QTcpSocket::disconnected,
            this, &RobotClient::onDisconnected);

    auto *reconnect_timer = new QTimer(this);
    reconnect_timer->setInterval(2000);
    connect(reconnect_timer, &QTimer::timeout,
            this, &RobotClient::connectToServer);
    reconnect_timer->start();

    auto *status_timer = new QTimer(this);
    status_timer->setInterval(500);
    connect(status_timer, &QTimer::timeout,
            this, &RobotClient::sendStatusJson);
    status_timer->start();
}

void RobotClient::connectToServer()
{
    if (socket_.state() == QAbstractSocket::ConnectedState ||
        socket_.state() == QAbstractSocket::ConnectingState)
        return;

    socket_.connectToHost(QHostAddress("192.168.4.1"), 8888);
}

void RobotClient::onConnected()
{
    std_msgs::msg::String msg;
    msg.data = "RobotClient connected";
    diag_pub_->publish(msg);
}

void RobotClient::onReadyRead()
{
    QByteArray data = socket_.readAll();
    processServerJson(data);
}

void RobotClient::onDisconnected()
{
    std_msgs::msg::String msg;
    msg.data = "RobotClient disconnected";
    diag_pub_->publish(msg);
}

void RobotClient::sendStatusJson()
{
    if (socket_.state() != QAbstractSocket::ConnectedState)
        return;

    QJsonObject obj;
    obj["type"] = "status";
    obj["battery"] = 12.5;     // TODO: подставить реальные значения
    obj["temp"] = 35.0;
    QJsonDocument doc(obj);
    socket_.write(doc.toJson(QJsonDocument::Compact));
    socket_.write("\n");
}

void RobotClient::processServerJson(const QByteArray &data)
{
    QList<QByteArray> lines = data.split('\n');
    for (const QByteArray &line : lines) {
        if (line.trimmed().isEmpty())
            continue;
        QJsonDocument doc = QJsonDocument::fromJson(line);
        if (!doc.isObject()) continue;
        QJsonObject obj = doc.object();
        QString type = obj["type"].toString();

        if (type == "ping") {
            QJsonObject pong;
            pong["type"] = "pong";
            QJsonDocument pong_doc(pong);
            socket_.write(pong_doc.toJson(QJsonDocument::Compact));
            socket_.write("\n");
        }
        // здесь можно добавить обработку команд с сервера
    }
}
