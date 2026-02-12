#ifndef MOTORDRIVER_H
#define MOTORDRIVER_H

#include <QObject>
#include <QTimer>

struct gpiod_chip;
struct gpiod_line;

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

    // вызывать периодически (у тебя уже висит QTimer с 1 мс)
    void pwmTick();

private:
    // libgpiod
    gpiod_chip *m_chip;

    gpiod_line *m_in1;
    gpiod_line *m_in2;
    gpiod_line *m_in3;
    gpiod_line *m_in4;
    gpiod_line *m_ena;
    gpiod_line *m_enb;

    // внутреннее состояние PWM
    MotorDirection m_leftDir;
    MotorDirection m_rightDir;
    int m_leftDuty;   // 0..100
    int m_rightDuty;  // 0..100

    int m_pwmCounter;    // 0..PWM_PERIOD-1
    static constexpr int PWM_PERIOD = 100; // 100 шагов = 1 кГц при тике 10 мкс, но мы тикаем 1мс => 10 Гц, нам ок

    // внутренняя инициализация
    bool initLines();
    void setLine(gpiod_line *line, int value);
    void updateBridgeSide(MotorDirection dir, int duty, gpiod_line *inA, gpiod_line *inB, gpiod_line *en);
};

#endif // MOTORDRIVER_H

