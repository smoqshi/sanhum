// ... все include как в проекте ...
#include "httpserver.h"
#include "robotmodel.h"

#include <QTcpServer>
#include <QTcpSocket>
#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>

// (весь код как в репозитории до блока /api/base)

    // ---------- API: base ----------
    if (method == "POST" && path == "/api/base") {
        const QJsonDocument doc = QJsonDocument::fromJson(body);
        const QJsonObject obj = doc.object();

        const bool emergency = obj.value(QStringLiteral("emergency")).toBool(false);
        const bool parkingBrake = obj.value(QStringLiteral("parkingBrake")).toBool(false);

        if (emergency) {
            m_model->emergencyStop();
        } else {
            const double vLin = obj.value(QStringLiteral("vLinear")).toDouble();
            const double vAng = obj.value(QStringLiteral("vAngular")).toDouble();
            m_model->setBaseCommand(vLin, vAng);
        }

        if (parkingBrake) {
            m_model->toggleParkingBrake();
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
        const double ext = obj.value(QStringLiteral("extend")).toDouble();
        const double grip = obj.value(QStringLiteral("gripper")).toDouble();
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

    // ---------- Остальное ----------
    socket->write(httpResponse("404 from default handler", "text/plain", 404, "Not Found"));
    socket->disconnectFromHost();
}


