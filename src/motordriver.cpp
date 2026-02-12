#include "motordriver.h"

#include <QHostAddress>
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
    m_updateTimer.setInterval(50);              // 20 Гц
    connect(&m_updateTimer, &QTimer::timeout,
            this, &MotorDriver::onUpdateTimer);
    m_updateTimer.start();
}

void MotorDriver::setLeftMotor(MotorDirection dir, int duty)
{
    m_leftDir  = dir;
    m_leftDuty = duty;
    // m_brake = false; // если хочешь, чтобы любое движение снимало тормоз
}

void MotorDriver::setRightMotor(MotorDirection dir, int duty)
{
    m_rightDir  = dir;
    m_rightDuty = duty;
    // m_brake = false;
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
    // Формат пакета (должен совпадать с motor_control.py):
    // 1 байт: тип = 1 (моторы)
    // 5 байт int8: left_dir, right_dir, left_duty, right_duty, brake

    qint8 leftDir   = dirToInt(m_leftDir);
    qint8 rightDir  = dirToInt(m_rightDir);
    qint8 leftDuty  = static_cast<qint8>(qBound(0, m_leftDuty, 100));
    qint8 rightDuty = static_cast<qint8>(qBound(0, m_rightDuty, 100));
    qint8 brake     = m_brake ? 1 : 0;

    QByteArray datagram;
    datagram.resize(1 + 5);
    char *p = datagram.data();
    p[0] = static_cast<char>(1);          // тип пакета
    p[1] = static_cast<char>(leftDir);
    p[2] = static_cast<char>(rightDir);
    p[3] = static_cast<char>(leftDuty);
    p[4] = static_cast<char>(rightDuty);
    p[5] = static_cast<char>(brake);

    qint64 sent = m_socket.writeDatagram(
        datagram,
        QHostAddress::LocalHost,
        5005         // UDP_PORT в motor_control.py
    );

    if (sent != datagram.size()) {
        qWarning() << "MotorDriver: failed to send UDP command";
    }
}
