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
    // обновляем моторы 10 раз в секунду (можно сделать 50 для ещё меньшей задержки)
    m_updateTimer.setInterval(100);
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

void MotorDriver::onUpdateTimer()
{
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
            this,
            [proc](int code, QProcess::ExitStatus st) {
                if (code != 0 || st != QProcess::NormalExit) {
                    qWarning() << "motor_control.py finished, code=" << code
                               << "status=" << st;
                    qWarning() << "stderr:" << proc->readAllStandardError();
                }
                proc->deleteLater();
            });

    proc->start(program, args);
}




