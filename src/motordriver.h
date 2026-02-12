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
    void pwmTick();

private:
    gpiod::chip m_chip;
    gpiod::line_request m_request;

    // offsets BCM для четырёх линий
    int m_idxIn1;
    int m_idxIn2;
    int m_idxIn3;
    int m_idxIn4;

    MotorDirection m_leftDir;
    MotorDirection m_rightDir;
    int m_leftDuty;   // 0..100
    int m_rightDuty;  // 0..100
    int m_pwmCounter;
    static constexpr int PWM_PERIOD = 100;

    bool initRequest();
    void setLine(int offset, int value);
    void updateBridgeSide(MotorDirection dir, int duty,
                          int offsetInA, int offsetInB);
};

#endif // MOTORDRIVER_H
