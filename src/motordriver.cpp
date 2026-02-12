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
{
}

void MotorDriver::setLeftMotor(MotorDirection dir, int duty)
{
    m_leftDir  = dir;
    m_leftDuty = duty;
    applyCommand();
}

void MotorDriver::setRightMotor(MotorDirection dir, int duty)
{
    m_rightDir  = dir;
    m_rightDuty = duty;
    applyCommand();
}

void MotorDriver::applyCommand()
{
    auto *proc = new QProcess(this);
    QString program = "python3";
    QString baseDir = QCoreApplication::applicationDirPath();
    QString script  = baseDir + "/src/motor_control.py";

    QStringList args;
    args << script
         << QString::number(dirToInt(m_leftDir))
         << QString::number(dirToInt(m_rightDir))
         << QString::number(m_leftDuty)
         << QString::number(m_rightDuty);

    connect(proc, &QProcess::finished,
            proc, &QProcess::deleteLater);

    proc->start(program, args);
    // максимум: короткая проверка на старт
    // proc->waitForStarted(100);
}


