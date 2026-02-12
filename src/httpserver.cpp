#include "httpserver.h"
#include "robotmodel.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QThread>

#ifdef Q_OS_LINUX
#include <QProcess>
#endif

#include <QTcpServer>
#include <QTcpSocket>

// Вспомогательный HTTP-ответ
static QByteArray httpResponse(const QByteArray &body,
                               const QByteArray &contentType,
                               int statusCode = 200,
                               const QByteArray &statusText = "OK")
{
    QByteArray resp;
    resp.reserve(128 + body.size());
    resp += "HTTP/1.1 ";
    resp += QByteArray::number(statusCode);
    resp += " ";
    resp += statusText;
    resp += "\r\nConnection: close\r\nContent-Type: ";
    resp += contentType;
    resp += "\r\nContent-Length: ";
    resp += QByteArray::number(body.size());
    resp += "\r\n\r\n";
    resp += body;
    return resp;
}

// Прокси для HTTP-потока (используется для CSI через локальный MJPEG-сервер)
static void proxyHttpStream(QTcpSocket *client,
                            const QString &host,
                            quint16 port,
                            const QByteArray &path)
{
    QTcpSocket upstream;
    upstream.connectToHost(host, port);
    if (!upstream.waitForConnected(1000)) {
        client->write(httpResponse("no upstream", "text/plain", 503, "Service Unavailable"));
        client->disconnectFromHost();
        return;
    }

    QByteArray req = "GET ";
    req += path;
    req += " HTTP/1.1\r\nHost: ";
    req += host.toUtf8();
    req += "\r\nConnection: close\r\n\r\n";
    upstream.write(req);
    upstream.flush();

    while (upstream.state() == QAbstractSocket::ConnectedState) {
        if (!upstream.waitForReadyRead(500))
            continue;
        const QByteArray chunk = upstream.readAll();
        if (chunk.isEmpty())
            break;
        client->write(chunk);
        client->flush();
    }

    upstream.disconnectFromHost();
    client->disconnectFromHost();
}

// =================== HttpServer ===================

HttpServer::HttpServer(RobotModel *model, QObject *parent)
    : QObject(parent)
    , m_server(this)
    , m_model(model)
{
    connect(&m_server, &QTcpServer::newConnection,
            this, &HttpServer::onNewConnection);

#ifdef Q_OS_LINUX
    // --- CSI камера: как в исходном проекте, libcamera-vid -> локальный HTTP (8081) ---

    m_procCsi.setProgram("bash");
    m_procCsi.setArguments({
        "-lc",
        "libcamera-vid "
        "--camera 0 "
        "--width 1280 --height 720 "
        "--framerate 20 "
        "--codec mjpeg "
        "--quality 70 "
        "--timeout 0 "
        "--nopreview "
        "-o - "
        "| python3 -m mjpeg_http_streamer -l 127.0.0.1 -p 8081"
    });
    m_procCsi.setProcessChannelMode(QProcess::MergedChannels);
    m_procCsi.startDetached();

    // --- Stereo USB камера: ffmpeg -> stdout, читаем в Qt и отдаём MJPEG сами ---

    m_procStereo.setProgram("ffmpeg");
    m_procStereo.setArguments({
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-framerate", "20",
        "-video_size", "1280x720",
        "-i", "/dev/video8",
        "-f", "mjpeg",
        "-q:v", "5",
        "pipe:1"
    });
    m_procStereo.setProcessChannelMode(QProcess::SeparateChannels);

    connect(&m_procStereo, &QProcess::readyReadStandardOutput, this, [this]() {
        // Дописываем новые байты
        m_lastStereoFrame += m_procStereo.readAllStandardOutput();

        // Ищем последний полный JPEG по маркерам FF D8 ... FF D9
        int start = m_lastStereoFrame.lastIndexOf("\xFF\xD8");
        int end   = m_lastStereoFrame.lastIndexOf("\xFF\xD9");
        if (start >= 0 && end > start) {
            QByteArray frame = m_lastStereoFrame.mid(start, end - start + 2);
            // сохраняем только последний полный кадр
            m_lastStereoFrame = frame;
        } else if (start > 0) {
            // Отбрасываем мусор до начала потенциального JPEG
            m_lastStereoFrame = m_lastStereoFrame.mid(start);
        }
    });

    m_procStereo.start();
#endif
}

bool HttpServer::listen(quint16 port)
{
    return m_server.listen(QHostAddress::Any, port);
}

void HttpServer::onNewConnection()
{
    while (m_server.hasPendingConnections()) {
        QTcpSocket *socket = m_server.nextPendingConnection();
        connect(socket, &QTcpSocket::readyRead,
                this, &HttpServer::onReadyRead);
        connect(socket, &QTcpSocket::disconnected,
                this, &HttpServer::onDisconnected);
    }
}

void HttpServer::onReadyRead()
{
    QTcpSocket *socket = qobject_cast<QTcpSocket *>(sender());
    if (!socket)
        return;

    const QByteArray req = socket->readAll();
    handleRequest(socket, req);
}

void HttpServer::onDisconnected()
{
    QTcpSocket *socket = qobject_cast<QTcpSocket *>(sender());
    if (socket)
        socket->deleteLater();
}

void HttpServer::handleRequest(QTcpSocket *socket, const QByteArray &request)
{
    const int firstLineEnd = request.indexOf("\r\n");
    if (firstLineEnd < 0) {
        socket->write(httpResponse("Bad Request", "text/plain", 400, "Bad Request"));
        socket->disconnectFromHost();
        return;
    }

    const QByteArray firstLine = request.left(firstLineEnd);
    const QList<QByteArray> parts = firstLine.split(' ');
    if (parts.size() < 2) {
        socket->write(httpResponse("Bad Request", "text/plain", 400, "Bad Request"));
        socket->disconnectFromHost();
        return;
    }

    const QByteArray method = parts[0];
    const QByteArray path   = parts[1];

    QByteArray body;
    const int headerEnd = request.indexOf("\r\n\r\n");
    if (headerEnd >= 0 && headerEnd + 4 < request.size())
        body = request.mid(headerEnd + 4);

    QString wwwRoot = QCoreApplication::applicationDirPath() + QStringLiteral("/www");
    if (!QDir(wwwRoot).exists()) {
        wwwRoot = QCoreApplication::applicationDirPath() + QStringLiteral("/../www");
    }

    // ---------- MJPEG-видео: CSI через прокси ----------
    if (method == "GET" && path == "/video/csi") {
#ifdef Q_OS_LINUX
        proxyHttpStream(socket, QStringLiteral("127.0.0.1"), 8081, "/stream");
#else
        socket->write(httpResponse("no signal", "text/plain", 503, "Service Unavailable"));
        socket->disconnectFromHost();
#endif
        return;
    }

    // ---------- MJPEG-видео: Stereo USB /dev/video8, отдаём сами ----------
    if (method == "GET" && path == "/video/stereo") {
#ifdef Q_OS_LINUX
        socket->write(
            "HTTP/1.1 200 OK\r\n"
            "Connection: close\r\n"
            "Cache-Control: no-cache\r\n"
            "Pragma: no-cache\r\n"
            "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n"
        );

        while (socket->state() == QAbstractSocket::ConnectedState) {
            if (!m_lastStereoFrame.isEmpty()) {
                QByteArray header;
                header += "--frame\r\n";
                header += "Content-Type: image/jpeg\r\n";
                header += "Content-Length: ";
                header += QByteArray::number(m_lastStereoFrame.size());
                header += "\r\n\r\n";
                socket->write(header);
                socket->write(m_lastStereoFrame);
                socket->write("\r\n");
                socket->flush();
            }
            QThread::msleep(50); // ~20 кадров в секунду
            if (!socket->waitForBytesWritten(10))
                break;
        }
#else
        socket->write(httpResponse("no signal", "text/plain", 503, "Service Unavailable"));
#endif
        socket->disconnectFromHost();
        return;
    }

    // ---------- index.html ----------
    if (method == "GET" && (path == "/" || path == "/index.html")) {
        QFile f(wwwRoot + "/index.html");
        if (!f.open(QIODevice::ReadOnly)) {
            socket->write(httpResponse("index.html not found", "text/plain", 404, "Not Found"));
        } else {
            const QByteArray data = f.readAll();
            socket->write(httpResponse(data, "text/html"));
        }
        socket->disconnectFromHost();
        return;
    }

    // ---------- статика js ----------
    if (method == "GET" && path.startsWith("/js/")) {
        const QString name = QString::fromUtf8(path.mid(4));
        QFile f(wwwRoot + "/js/" + name);
        if (!f.open(QIODevice::ReadOnly)) {
            socket->write(httpResponse("js not found", "text/plain", 404, "Not Found"));
        } else {
            const QByteArray data = f.readAll();
            socket->write(httpResponse(data, "application/javascript"));
        }
        socket->disconnectFromHost();
        return;
    }

    // ---------- API: status ----------
    if (method == "GET" && path == "/api/status") {
        const QJsonDocument doc(m_model->makeStatusJson());
        const QByteArray data = doc.toJson(QJsonDocument::Compact);
        socket->write(httpResponse(data, "application/json"));
        socket->disconnectFromHost();
        return;
    }

    // ---------- API: joint_state ----------
    if (method == "GET" && path == "/api/joint_state") {
        const QJsonDocument doc(m_model->makeJointStateJson());
        const QByteArray data = doc.toJson(QJsonDocument::Compact);
        socket->write(httpResponse(data, "application/json"));
        socket->disconnectFromHost();
        return;
    }

    // ---------- API: base ----------
    if (method == "POST" && path == "/api/base") {
        const QJsonDocument doc = QJsonDocument::fromJson(body);
        const QJsonObject obj = doc.object();

        const bool emergency = obj.value(QStringLiteral("emergency")).toBool(false);
        if (emergency) {
            m_model->emergencyStop();
        } else {
            const double vLin = obj.value(QStringLiteral("vLinear")).toDouble();
            const double vAng = obj.value(QStringLiteral("vAngular")).toDouble();
            m_model->setBaseCommand(vLin, vAng);
        }

        QJsonObject reply;
        reply.insert(QStringLiteral("ok"), true);
        const QByteArray data = QJsonDocument(reply).toJson(QJsonDocument::Compact);
        socket->write(httpResponse(data, "application/json"));
        socket->disconnectFromHost();
        return;
    }

    // ---------- API: arm ----------
    if (method == "POST" && path == "/api/arm") {
        const QJsonDocument doc = QJsonDocument::fromJson(body);
        const QJsonObject obj = doc.object();

        const double ext    = obj.value(QStringLiteral("extend")).toDouble();
        const double grip   = obj.value(QStringLiteral("gripper")).toDouble();
        const double turret = obj.value(QStringLiteral("turretAngle")).toDouble();

        m_model->setArmExtension(ext);
        m_model->setGripper(grip);
        m_model->setTurretAngle(turret);

        QJsonObject reply;
        reply.insert(QStringLiteral("ok"), true);
        const QByteArray data = QJsonDocument(reply).toJson(QJsonDocument::Compact);
        socket->write(httpResponse(data, "application/json"));
        socket->disconnectFromHost();
        return;
    }

    // ---------- 404 ----------
    socket->write(httpResponse("404 from default handler", "text/plain", 404, "Not Found"));
    socket->disconnectFromHost();
}
