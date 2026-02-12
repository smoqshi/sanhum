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
    QString program = "python3";

    QString baseDir = QCoreApplication::applicationDirPath();
    QString script  = baseDir + "/src/motor_control.py";

    QStringList args;
    args << script
         << QString::number(dirToInt(m_leftDir))
         << QString::number(dirToInt(m_rightDir))
         << QString::number(m_leftDuty)
         << QString::number(m_rightDuty);

    QProcess *proc = new QProcess(this);
    connect(proc, &QProcess::finished, this, [proc](int code, QProcess::ExitStatus st) {
        qDebug() << "motor_control.py finished, code=" << code << "status=" << st;
        qDebug() << "stdout:" << proc->readAllStandardOutput();
        qDebug() << "stderr:" << proc->readAllStandardError();
        proc->deleteLater();
    });

    proc->start(program, args);
    if (!proc->waitForStarted(1000)) {
        qWarning() << "Failed to start motor_control.py" << proc->errorString();
    }
}


