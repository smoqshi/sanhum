#pragma once

#include <QObject>
#include <QTimer>
#include <atomic>

// Направление мотора
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

    // Управление моторами.
    // speed_percent: 0..100 (модуль скорости), направление задаётся MotorDirection.
    void setLeftMotor(MotorDirection dir, int speed_percent);
    void setRightMotor(MotorDirection dir, int speed_percent);

private slots:
    void pwmTick(); // периодический тик софт‑PWM

private:
    // ===== НОМЕРА GPIO (ПОДСТАВЬ СВОИ, ЕСЛИ ДРУГИЕ) =====
    int m_leftIn1;   // например GPIO25
    int m_leftIn2;   // например GPIO8
    int m_rightIn1;  // например GPIO7
    int m_rightIn2;  // например GPIO1

    // файловые дескрипторы /sys/class/gpio/.../value
    int m_leftFdIn1;
    int m_leftFdIn2;
    int m_rightFdIn1;
    int m_rightFdIn2;

    // Параметры PWM
    std::atomic<int>          m_leftDuty;   // 0..100
    std::atomic<int>          m_rightDuty;  // 0..100
    std::atomic<MotorDirection> m_leftDir;
    std::atomic<MotorDirection> m_rightDir;

    int    m_phase;    // 0..99 – фаза PWM
    QTimer m_pwmTimer;

    // Вспомогательные методы работы с sysfs GPIO
    int  exportGpio(int gpio);
    int  setGpioDirection(int gpio, bool output);
    int  openGpioValue(int gpio);
    void writeGpio(int fd, bool value);

    // Применить один шаг PWM к конкретному мосту
    void applyPhaseForMotor(int fdA,
                            int fdB,
                            MotorDirection dir,
                            int duty,
                            int phase);
};

