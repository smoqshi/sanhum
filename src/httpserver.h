#pragma once

#include <QObject>
#include <QTcpServer>
#include <QTcpSocket>
#include "RobotModel.h"

    class HttpServer : public QObject
{
    Q_OBJECT
public:
    explicit HttpServer(RobotModel *model, QObject *parent = nullptr);

    bool listen(quint16 port = 8080);

private slots:
    void onNewConnection();
    void onReadyRead();
    void onDisconnected();

private:
    void handleRequest(QTcpSocket *socket, const QByteArray &request);

    QTcpServer m_server;
    RobotModel *m_model;
};
