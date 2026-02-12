#include "motordriver.h"

#include <QDebug>
#include <gpiod.h>
#include <cmath>
#include <algorithm>

MotorDriver::MotorDriver(QObject *parent)
    : QObject(parent)
    , m_chip(nullptr)
    , m_in1(nullptr)
    , m_in2(nullptr)
    , m_in3(nullptr)
    , m_in4(nullptr)
    , m_ena(nullptr)
    , m_enb(nullptr)
    , m_leftDir(MotorDirection::Stop)
    , m_rightDir(MotorDirection::Stop)
    , m_leftDuty(0)
    , m_rightDuty(0)
    , m_pwmCounter(0)
{
    if (!initLines()) {
        qWarning() << "MotorDriver: failed to init GPIO lines via libgpiod";
    }

    // если у тебя раньше pwmTick дергался от своего таймера в этом классе — верни это:
    // QTimer *timer = new QTimer(this);
    // connect(timer, &QTimer::timeout, this, &MotorDriver::pwmTick);
    // timer->start(1);
}

MotorDriver::~MotorDriver()
{
    if (m_in1) gpiod_line_release(m_in1);
    if (m_in2) gpiod_line_release(m_in2);
    if (m_in3) gpiod_line_release(m_in3);
    if (m_in4) gpiod_line_release(m_in4);
    if (m_ena) gpiod_line_release(m_ena);
    if (m_enb) gpiod_line_release(m_enb);
    if (m_chip) gpiod_chip_close(m_chip);
}

bool MotorDriver::initLines()
{
    // На Pi 5 твои "обычные" GPIO 17, 22, 23, 24 находятся в gpiochip0 [web:5].
    // Предположим старую разводку:
    //  IN1 = GPIO17, IN2 = GPIO27, IN3 = GPIO23, IN4 = GPIO24
    //  ENA = GPIO22, ENB = GPIO18
    // Если у тебя другая схема — просто поправь номера ниже на нужные (по gpioinfo).
    const int gpioIn1 = 17;
    const int gpioIn2 = 27;
    const int gpioIn3 = 23;
    const int gpioIn4 = 24;
    const int gpioEnA = 22;
    const int gpioEnB = 18;

    m_chip = gpiod_chip_open_by_name("gpiochip0");
    if (!m_chip) {
        qWarning() << "MotorDriver: gpiod_chip_open_by_name(gpiochip0) failed";
        return false;
    }

    auto getLine = [this](int num, const char *name) -> gpiod_line* {
        gpiod_line *line = gpiod_chip_get_line(m_chip, num);
        if (!line) {
            qWarning() << "MotorDriver: gpiod_chip_get_line failed for" << name << "num" << num;
        }
        return line;
    };

    m_in1 = getLine(gpioIn1, "IN1");
    m_in2 = getLine(gpioIn2, "IN2");
    m_in3 = getLine(gpioIn3, "IN3");
    m_in4 = getLine(gpioIn4, "IN4");
    m_ena = getLine(gpioEnA, "ENA");
    m_enb = getLine(gpioEnB, "ENB");

    bool ok = m_in1 && m_in2 && m_in3 && m_in4 && m_ena && m_enb;
    if (!ok) {
        qWarning() << "MotorDriver: some GPIO lines are null";
        return false;
    }

    auto requestOut = [](gpiod_line *line, const char *consumer, int initVal) {
        int ret = gpiod_line_request_output(line, consumer, initVal);
        if (ret < 0) {
            qWarning() << "MotorDriver: gpiod_line_request_output failed for" << consumer << "ret=" << ret;
            return false;
        }
        return true;
    };

    if (!requestOut(m_in1, "sanhum_in1", 0)) return false;
    if (!requestOut(m_in2, "sanhum_in2", 0)) return false;
    if (!requestOut(m_in3, "sanhum_in3", 0)) return false;
    if (!requestOut(m_in4, "sanhum_in4", 0)) return false;
    if (!requestOut(m_ena, "sanhum_ena", 0)) return false;
    if (!requestOut(m_enb, "sanhum_enb", 0)) return false;

    return true;
}

void MotorDriver::setLine(gpiod_line *line, int value)
{
    if (!line) return;
    int ret = gpiod_line_set_value(line, value ? 1 : 0);
    if (ret < 0) {
        qWarning() << "MotorDriver: gpiod_line_set_value failed, value=" << value;
    }
}

void MotorDriver::setLeftMotor(MotorDirection dir, int dutyPercent)
{
    dutyPercent = std::clamp(dutyPercent, 0, 100);
    m_leftDir = dir;
    m_leftDuty = dutyPercent;
}

void MotorDriver::setRightMotor(MotorDirection dir, int dutyPercent)
{
    dutyPercent = std::clamp(dutyPercent, 0, 100);
    m_rightDir = dir;
    m_rightDuty = dutyPercent;
}

void MotorDriver::updateBridgeSide(MotorDirection dir, int duty, gpiod_line *inA, gpiod_line *inB, gpiod_line *en)
{
    // Простейший программный PWM: duty по EN, направление по IN1/IN2
    switch (dir) {
    case MotorDirection::Stop:
        setLine(inA, 0);
        setLine(inB, 0);
        setLine(en, 0);
        break;
    case MotorDirection::Forward:
        setLine(inA, 1);
        setLine(inB, 0);
        // EN будет управляться duty ниже
        break;
    case MotorDirection::Backward:
        setLine(inA, 0);
        setLine(inB, 1);
        // EN будет управляться duty ниже
        break;
    }

    if (dir == MotorDirection::Stop) {
        setLine(en, 0);
    } else {
        int level = (m_pwmCounter < duty) ? 1 : 0;
        setLine(en, level);
    }
}

void MotorDriver::pwmTick()
{
    // увеличиваем счётчик PWM
    m_pwmCounter++;
    if (m_pwmCounter >= PWM_PERIOD)
        m_pwmCounter = 0;

    updateBridgeSide(m_leftDir,  m_leftDuty,  m_in1, m_in2, m_ena);
    updateBridgeSide(m_rightDir, m_rightDuty, m_in3, m_in4, m_enb);
}




