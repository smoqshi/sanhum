#include "motordriver.h"
#include <QCoreApplication>
#include <QProcess>
#include <QDebug>
#include <algorithm>

static int dirToInt(MotorDirection d)
{
    switch (d) {
    case MotorDirection::Forward:  return 1;
    case MotorDirection::Backward: return -1;
    case MotorDirection::Stop:
    default:                       return 0;
    }
}

void MotorDriver::applyCommand()
{
    QString program = "python3";

    // бинарник лежит в корне проекта, src/motor_control.py — рядом относительно него
    QString baseDir = QCoreApplication::applicationDirPath();
    QString script  = baseDir + "/src/motor_control.py";

    QStringList args;
    args << script
         << QString::number(dirToInt(m_leftDir))
         << QString::number(dirToInt(m_rightDir))
         << QString::number(m_leftDuty)
         << QString::number(m_rightDuty);

    QProcess *proc = new QProcess(this);
    connect(proc, &QProcess::finished, proc, &QProcess::deleteLater);
    proc->start(program, args);
}
