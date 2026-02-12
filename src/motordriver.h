#ifndef MOTORDRIVER_H
#define MOTORDRIVER_H

#include <QObject>
#include <QTimer>

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
    // libgpiod2 C++ API
    gpiod::chip m_chip;

    gpiod::line m_in1;
    gpiod::line m_in2;
    gpiod::line m_in3;
    gpiod::line m_in4;
    gpiod::line m_ena;
    gpiod::line m_enb;

    // внутреннее состояние PWM
    MotorDirection m_leftDir;
    MotorDirection m_rightDir;
    int m_leftDuty;   // 0..100
    int m_rightDuty;  // 0..100

    int m_pwmCounter;
    static constexpr int PWM_PERIOD = 100;

    bool initLines();
    void setLine(gpiod::line &line, int value);
    void updateBridgeSide(MotorDirection dir, int duty,
                          gpiod::line &inA, gpiod::line &inB, gpiod::line &en);
};

#endif // MOTORDRIVER_H

