#ifndef MOTORDRIVER_H
#define MOTORDRIVER_H

#include <QObject>

enum class MotorDirection {
    Stop = 0,
    Forward,
    Backward
};

class MotorDriver : public QObject
{
    Q_OBJECT
public:
    explicit MotorDriver(QObject *parent = nullptr);

    void setLeftMotor(MotorDirection dir, int duty);
    void setRightMotor(MotorDirection dir, int duty);

private:
    void applyCommand();

    MotorDirection m_leftDir;
    MotorDirection m_rightDir;
    int m_leftDuty;
    int m_rightDuty;
};

#endif // MOTORDRIVER_H
