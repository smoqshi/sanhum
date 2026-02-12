#ifndef HTTPSERVER_H
#define HTTPSERVER_H

#include <QObject>
#include <QTcpServer>
#include <QTcpSocket>

class RobotModel;

class HttpServer : public QObject
{
    Q_OBJECT
public:
    explicit HttpServer(RobotModel *model, QObject *parent = nullptr);

    bool listen(quint16 port);

private slots:
    void onNewConnection();
    void onReadyRead();
    void onDisconnected();

private:
    void handleRequest(QTcpSocket *socket, const QByteArray &request);

    QTcpServer m_server;
    RobotModel *m_model;
};

#endif // HTTPSERVER_H
