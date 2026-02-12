#ifndef MOTORDRIVER_H
#define MOTORDRIVER_H

#include <QObject>
#include <QTimer>

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

private slots:
    void onUpdateTimer();

private:
    void applyCommand();

    MotorDirection m_leftDir;
    MotorDirection m_rightDir;
    int m_leftDuty;
    int m_rightDuty;

    QTimer m_updateTimer;
};

#endif // MOTORDRIVER_H
