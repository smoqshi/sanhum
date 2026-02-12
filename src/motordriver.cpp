#include "motordriver.h"

#include <QHostAddress>
#include <QCoreApplication>
#include <QDir>
#include <QDebug>

static qint8 dirToInt(MotorDirection d)
{
    switch (d) {
    case MotorDirection::Forward:  return 1;
    case MotorDirection::Backward: return -1;
    case MotorDirection::Stop:
    default:                       return 0;
    }
}

MotorDriver::MotorDriver(QObject *parent)
    : QObject(parent)
    , m_leftDir(MotorDirection::Stop)
    , m_rightDir(MotorDirection::Stop)
    , m_leftDuty(0)
    , m_rightDuty(0)
    , m_brake(false)
{
    // запустить Python‑демон мотор‑контроллера
    startPythonDaemon();

    m_updateTimer.setInterval(10);
    connect(&m_updateTimer, &QTimer::timeout,
            this, &MotorDriver::onUpdateTimer);
    m_updateTimer.start();
}

void MotorDriver::setLeftMotor(MotorDirection dir, int duty)
{
    m_leftDir  = dir;
    m_leftDuty = duty;
}

void MotorDriver::setRightMotor(MotorDirection dir, int duty)
{
    m_rightDir  = dir;
    m_rightDuty = duty;
}

void MotorDriver::emergencyBrake()
{
    m_brake = true;
}

void MotorDriver::onUpdateTimer()
{
    sendCommand();
}

void MotorDriver::sendCommand()
{
    qint8 leftDir   = dirToInt(m_leftDir);
    qint8 rightDir  = dirToInt(m_rightDir);
    qint8 leftDuty  = static_cast<qint8>(qBound(0, m_leftDuty, 100));
    qint8 rightDuty = static_cast<qint8>(qBound(0, m_rightDuty, 100));
    qint8 brake     = m_brake ? 1 : 0;

    QByteArray datagram;
    datagram.resize(1 + 5);
    char *p = datagram.data();
    p[0] = static_cast<char>(1);
    p[1] = static_cast<char>(leftDir);
    p[2] = static_cast<char>(rightDir);
    p[3] = static_cast<char>(leftDuty);
    p[4] = static_cast<char>(rightDuty);
    p[5] = static_cast<char>(brake);

    qint64 sent = m_socket.writeDatagram(
        datagram,
        QHostAddress::LocalHost,
        5005
    );

    if (sent != datagram.size()) {
        qWarning() << "MotorDriver: failed to send UDP command";
    }
}

void MotorDriver::startPythonDaemon()
{
#ifdef Q_OS_LINUX
    // ищем motor_control.py рядом с бинарём в ./motor/motor_control.py
    const QString appDir = QCoreApplication::applicationDirPath();
    QString scriptPath = appDir + QStringLiteral("/motor_control.py");

    if (!QFile::exists(scriptPath)) {
        // альтернатива: в подкаталоге motor/
        const QString alt = appDir + QStringLiteral("/motor/motor_control.py");
        if (QFile::exists(alt)) {
            scriptPath = alt;
        } else {
            qWarning() << "MotorDriver: motor_control.py not found near binary";
            return;
        }
    }

    m_motorProcess.setProgram(QStringLiteral("python3"));
    m_motorProcess.setArguments({ scriptPath });
    m_motorProcess.setProcessChannelMode(QProcess::MergedChannels);
    QObject::connect(&m_motorProcess, &QProcess::readyReadStandardOutput, [this]() {
        const QByteArray out = m_motorProcess.readAllStandardOutput();
        if (!out.isEmpty())
            qDebug().noquote() << "[motor_control]" << out.trimmed();
    });
    QObject::connect(&m_motorProcess,
                     QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished),
                     this,
                     [](int code, QProcess::ExitStatus status) {
        qWarning() << "motor_control.py finished, code" << code << "status" << status;
    });

    m_motorProcess.start();
    if (!m_motorProcess.waitForStarted(2000)) {
        qWarning() << "MotorDriver: failed to start motor_control.py";
    } else {
        qDebug() << "MotorDriver: motor_control.py started";
    }
#else
    qDebug() << "MotorDriver: Python motor daemon is only used on Linux";
#endif
}

void MotorDriver::stopPythonDaemon()
{
#ifdef Q_OS_LINUX
    if (m_motorProcess.state() == QProcess::Running) {
        m_motorProcess.terminate();
        if (!m_motorProcess.waitForFinished(1000)) {
            m_motorProcess.kill();
            m_motorProcess.waitForFinished(1000);
        }
    }
#endif
}

