#include "httpserver.h"
#include "robotmodel.h"

#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>

#include <QTcpServer>
#include <QTcpSocket>
#include <QThread>

#ifdef Q_OS_LINUX
#include <QProcess>
#endif

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

HttpServer::HttpServer(RobotModel *model, QObject *parent)
    : QObject(parent)
    , m_server(this)
    , m_model(model)
{
    connect(&m_server, &QTcpServer::newConnection,
            this, &HttpServer::onNewConnection);

#ifdef Q_OS_LINUX
    // CSI: rpicam-vid, без превью, MJPEG в stdout
    m_procCsi.setProgram("rpicam-vid");
    m_procCsi.setArguments({
        "--camera", "0",
        "--timeout", "0",
        "--codec", "mjpeg",
        "--width", "1280",
        "--height", "720",
        "--framerate", "20",
        "--nopreview",
        "-o", "-"
    });
    m_procCsi.setProcessChannelMode(QProcess::SeparateChannels);
    m_procCsi.start();

    // Stereo LEFT: /dev/video8, левая половина кадра
    // ПОДПРАВЬ video_size, если реальное разрешение другое.
    m_procStereoLeft.setProgram("ffmpeg");
    m_procStereoLeft.setArguments({
        "-loglevel", "error",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-framerate", "20",
        "-video_size", "2560x720",
        "-i", "/dev/video8",
        "-filter:v", "crop=iw/2:ih:0:0",
        "-f", "mjpeg",
        "-q:v", "5",
        "pipe:1"
    });
    m_procStereoLeft.setProcessChannelMode(QProcess::SeparateChannels);
    m_procStereoLeft.start();

    // Stereo RIGHT: /dev/video8, правая половина кадра
    m_procStereoRight.setProgram("ffmpeg");
    m_procStereoRight.setArguments({
        "-loglevel", "error",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-framerate", "20",
        "-video_size", "2560x720",
        "-i", "/dev/video8",
        "-filter:v", "crop=iw/2:ih:iw/2:0",
        "-f", "mjpeg",
        "-q:v", "5",
        "pipe:1"
    });
    m_procStereoRight.setProcessChannelMode(QProcess::SeparateChannels);
    m_procStereoRight.start();
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

#ifdef Q_OS_LINUX
static void streamMjpegFromProcess(QTcpSocket *socket, QProcess *proc)
{
    socket->write(
        "HTTP/1.1 200 OK\r\n"
        "Connection: close\r\n"
        "Cache-Control: no-cache\r\n"
        "Pragma: no-cache\r\n"
        "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n"
    );

    QByteArray buf;

    while (socket->state() == QAbstractSocket::ConnectedState) {
        if (!proc->waitForReadyRead(1000))
            continue;

        buf += proc->readAllStandardOutput();

        while (true) {
            int start = buf.indexOf("\xFF\xD8");
            if (start < 0) {
                if (buf.size() > 1024 * 1024)
                    buf.clear();
                break;
            }
            if (start > 0)
                buf.remove(0, start);

            int end = buf.indexOf("\xFF\xD9", 2);
            if (end < 0)
                break;

            int frameLen = end + 2;
            QByteArray frame = buf.left(frameLen);
            buf.remove(0, frameLen);

            QByteArray header;
            header += "--frame\r\n";
            header += "Content-Type: image/jpeg\r\n";
            header += "Content-Length: ";
            header += QByteArray::number(frame.size());
            header += "\r\n\r\n";

            socket->write(header);
            socket->write(frame);
            socket->write("\r\n");
            socket->flush();

            if (!socket->waitForBytesWritten(100))
                return;
        }
    }
}
#endif

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

    // --- MJPEG: CSI ---
    if (method == "GET" && path == "/video/csi") {
#ifdef Q_OS_LINUX
        streamMjpegFromProcess(socket, &m_procCsi);
#else
        socket->write(httpResponse("no signal", "text/plain", 503, "Service Unavailable"));
#endif
        socket->disconnectFromHost();
        return;
    }

    // --- MJPEG: Stereo left ---
    if (method == "GET" && path == "/video/stereo_left") {
#ifdef Q_OS_LINUX
        streamMjpegFromProcess(socket, &m_procStereoLeft);
#else
        socket->write(httpResponse("no signal", "text/plain", 503, "Service Unavailable"));
#endif
        socket->disconnectFromHost();
        return;
    }

    // --- MJPEG: Stereo right ---
    if (method == "GET" && path == "/video/stereo_right") {
#ifdef Q_OS_LINUX
        streamMjpegFromProcess(socket, &m_procStereoRight);
#else
        socket->write(httpResponse("no signal", "text/plain", 503, "Service Unavailable"));
#endif
        socket->disconnectFromHost();
        return;
    }

    // --- index.html ---
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

    // --- static js ---
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

    // --- API: status ---
    if (method == "GET" && path == "/api/status") {
        const QJsonDocument doc(m_model->makeStatusJson());
        const QByteArray data = doc.toJson(QJsonDocument::Compact);
        socket->write(httpResponse(data, "application/json"));
        socket->disconnectFromHost();
        return;
    }

    // --- API: joint_state ---
    if (method == "GET" && path == "/api/joint_state") {
        const QJsonDocument doc(m_model->makeJointStateJson());
        const QByteArray data = doc.toJson(QJsonDocument::Compact);
        socket->write(httpResponse(data, "application/json"));
        socket->disconnectFromHost();
        return;
    }

    // --- API: base ---
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

    // --- API: arm ---
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

    socket->write(httpResponse("404 from default handler", "text/plain", 404, "Not Found"));
    socket->disconnectFromHost();
}

