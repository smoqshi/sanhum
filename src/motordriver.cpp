#include "motordriver.h"

#include <QCoreApplication>
#include <QProcess>
#include <QDebug>

static int dirToInt(MotorDirection d)
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
    m_updateTimer.setInterval(50);   // 20 Гц
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
    applyCommand();
}

void MotorDriver::applyCommand()
{
    QString program = "python3";
    QString baseDir = QCoreApplication::applicationDirPath();
    QString script  = baseDir + "/src/motor_control.py";

    int leftDuty  = m_leftDuty;
    int rightDuty = m_rightDuty;
    MotorDirection leftDir  = m_leftDir;
    MotorDirection rightDir = m_rightDir;

    if (m_brake) {
        // спец‑режим тормоза, как договорились: отрицательный duty
        leftDuty  = -100;
        rightDuty = -100;
        leftDir   = MotorDirection::Stop;
        rightDir  = MotorDirection::Stop;
    }

    QStringList args;
    args << script
         << QString::number(dirToInt(leftDir))
         << QString::number(dirToInt(rightDir))
         << QString::number(leftDuty)
         << QString::number(rightDuty);

    QProcess *proc = new QProcess(this);
    connect(proc, &QProcess::finished,
            proc, &QProcess::deleteLater);

    proc->start(program, args);
}

