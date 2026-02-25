#include "wifi_server.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QBuffer>
#include <QImage>
#include <QByteArray>

#include <cv_bridge/cv_bridge.hpp>
#include <opencv2/imgcodecs.hpp>

WifiServer::WifiServer(std::shared_ptr<rclcpp::Node> node, QObject *parent)
    : QObject(parent),
    node_(std::move(node))
{
    connect(&server_, &QTcpServer::newConnection,
            this, &WifiServer::onNewConnection);
    server_.listen(QHostAddress::Any, 8888);

    cmd_vel_pub_ = node_->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);

    mono_sub_ = node_->create_subscription<sensor_msgs::msg::Image>(
        "/mono/image_raw", 5,
        [this](sensor_msgs::msg::Image::SharedPtr msg) {
            sendImageToClient(msg);
        });

    diag_sub_ = node_->create_subscription<std_msgs::msg::String>(
        "/diagnostics", 10,
        [this](std_msgs::msg::String::SharedPtr msg) {
            sendDiagnosticsToClient(msg);
        });
}

void WifiServer::onNewConnection()
{
    client_ = server_.nextPendingConnection();
    connect(client_, &QTcpSocket::readyRead,
            this, &WifiServer::onClientData);
    connect(client_, &QTcpSocket::disconnected,
            this, &WifiServer::onClientDisconnected);
}

void WifiServer::onClientData()
{
    if (!client_) return;
    QByteArray data = client_->readAll();
    processJsonMessage(data);
}

void WifiServer::onClientDisconnected()
{
    client_ = nullptr;
}

void WifiServer::processJsonMessage(const QByteArray &data)
{
    QList<QByteArray> lines = data.split('\n');
    for (const QByteArray &line : lines) {
        if (line.trimmed().isEmpty())
            continue;

        QJsonDocument doc = QJsonDocument::fromJson(line);
        if (!doc.isObject()) continue;
        QJsonObject obj = doc.object();

        QString type = obj["type"].toString();
        if (type == "cmd_vel") {
            geometry_msgs::msg::Twist msg;
            msg.linear.x  = obj["linear_x"].toDouble();
            msg.angular.z = obj["angular_z"].toDouble();
            cmd_vel_pub_->publish(msg);
        }
        else if (type == "status") {
            // можно пробрасывать статус в /tcp_status
            auto pub = node_->create_publisher<std_msgs::msg::String>("/tcp_status", 10);
            std_msgs::msg::String s;
            s.data = QString("battery=%1 temp=%2")
                         .arg(obj["battery"].toDouble())
                         .arg(obj["temp"].toDouble())
                         .toStdString();
            pub->publish(s);
        }
    }
}

void WifiServer::sendImageToClient(const sensor_msgs::msg::Image::SharedPtr &msg)
{
    if (!client_) return;

    try {
        cv::Mat img = cv_bridge::toCvCopy(msg, "bgr8")->image;
        std::vector<uchar> buf;
        cv::imencode(".jpg", img, buf);
        QByteArray jpeg_data(reinterpret_cast<const char*>(buf.data()),
                             static_cast<int>(buf.size()));
        QByteArray base64 = jpeg_data.toBase64();

        QJsonObject obj;
        obj["type"] = "image";
        obj["camera"] = "mono";
        obj["data"] = QString::fromLatin1(base64);

        QJsonDocument doc(obj);
        client_->write(doc.toJson(QJsonDocument::Compact));
        client_->write("\n");
    } catch (const cv_bridge::Exception &e) {
        RCLCPP_ERROR(node_->get_logger(), "WifiServer cv_bridge error: %s", e.what());
    }
}

void WifiServer::sendDiagnosticsToClient(const std_msgs::msg::String::SharedPtr &msg)
{
    if (!client_) return;

    QJsonObject obj;
    obj["type"] = "diagnostics";
    obj["text"] = QString::fromStdString(msg->data);

    QJsonDocument doc(obj);
    client_->write(doc.toJson(QJsonDocument::Compact));
    client_->write("\n");
}

