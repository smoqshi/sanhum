#ifndef HTTPSERVER_H
#define HTTPSERVER_H

#include <QObject>
#include <QTcpServer>
#include <QTcpSocket>
#include <QByteArray>

class RobotModel;

#ifdef Q_OS_LINUX
#include <QProcess>
#endif

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

#ifdef Q_OS_LINUX
    QProcess m_procCsi;
    QProcess m_procStereo;
#endif

    // буферы для последних кадров
    QByteArray m_lastStereoFrame;
    QByteArray m_lastCsiFrame;
};

#endif // HTTPSERVER_H
