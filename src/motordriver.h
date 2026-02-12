#ifndef MOTORDRIVER_H
#define MOTORDRIVER_H

#include <QObject>
#include <gpiod.hpp>

enum class MotorDirection {
    Stop,
    Forward,
    Backward
};

class MotorDriver : public QObject
{
    Q_OBJECT
public:
    explicit MotorDriver(QObject *parent = nullptr);
    ~MotorDriver();

    void setLeftMotor(MotorDirection dir, int dutyPercent);
    void setRightMotor(MotorDirection dir, int dutyPercent);

    // вызывать периодически (как и раньше)
    void pwmTick();

private:
    // libgpiod C++ API 2.x
    gpiod::chip m_chip;
    gpiod::line_request m_request;

    // номера линий в этом запросе (BCM)
    int m_idxIn1;
    int m_idxIn2;
    int m_idxIn3;
    int m_idxIn4;
    int m_idxEnA;
    int m_idxEnB;

    // состояние
    MotorDirection m_leftDir;
    MotorDirection m_rightDir;
    int m_leftDuty;   // 0..100
    int m_rightDuty;  // 0..100
    int m_pwmCounter;
    static constexpr int PWM_PERIOD = 100;

    bool initRequest();
    void setLine(int offset, int value);
    void updateBridgeSide(MotorDirection dir, int duty,
                          int offsetInA, int offsetInB, int offsetEn);
};

#endif // MOTORDRIVER_H
