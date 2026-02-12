#include "motordriver.h"

#include <QDebug>
#include <algorithm>
#include <cmath>
#include <cerrno>
#include <cstring>

// BCM-номера GPIO по твоей схеме — при необходимости поправь
static constexpr int GPIO_IN1 = 17;
static constexpr int GPIO_IN2 = 27;
static constexpr int GPIO_IN3 = 23;
static constexpr int GPIO_IN4 = 24;
static constexpr int GPIO_ENA = 22;
static constexpr int GPIO_ENB = 18;

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
        qWarning() << "MotorDriver: failed to init GPIO lines via gpiod";
    }

    // Если раньше PWM тикал изнутри, можно включить таймер здесь.
    // В твоём проекте pwmTick вызывается извне, поэтому не включаю.
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
    // Pi 5: все обычные GPIO2..27 на gpiochip0 (pinctrl-rp1) [web:5].
    m_chip = gpiod_chip_open_by_name("gpiochip0");
    if (!m_chip) {
        qWarning() << "MotorDriver: gpiod_chip_open_by_name(gpiochip0) failed:" << strerror(errno);
        return false;
    }

    auto getLine = [this](int num, const char *name) -> gpiod_line* {
        gpiod_line *line = gpiod_chip_get_line(m_chip, num);
        if (!line) {
            qWarning() << "MotorDriver: gpiod_chip_get_line failed for" << name
                       << "num" << num << ":" << strerror(errno);
        }
        return line;
    };

    m_in1 = getLine(GPIO_IN1, "IN1");
    m_in2 = getLine(GPIO_IN2, "IN2");
    m_in3 = getLine(GPIO_IN3, "IN3");
    m_in4 = getLine(GPIO_IN4, "IN4");
    m_ena = getLine(GPIO_ENA, "ENA");
    m_enb = getLine(GPIO_ENB, "ENB");

    if (!m_in1 || !m_in2 || !m_in3 || !m_in4 || !m_ena || !m_enb) {
        qWarning() << "MotorDriver: some GPIO lines are null";
        return false;
    }

    auto requestOut = [](gpiod_line *line, const char *consumer, int initVal) {
        int ret = gpiod_line_request_output(line, consumer, initVal ? 1 : 0);
        if (ret < 0) {
            qWarning() << "MotorDriver: gpiod_line_request_output failed for"
                       << consumer << ":" << strerror(errno);
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
        qWarning() << "MotorDriver: gpiod_line_set_value failed:" << strerror(errno);
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

void MotorDriver::updateBridgeSide(MotorDirection dir, int duty,
                                   gpiod_line *inA, gpiod_line *inB, gpiod_line *en)
{
    switch (dir) {
    case MotorDirection::Stop:
        setLine(inA, 0);
        setLine(inB, 0);
        setLine(en, 0);
        break;
    case MotorDirection::Forward:
        setLine(inA, 1);
        setLine(inB, 0);
        break;
    case MotorDirection::Backward:
        setLine(inA, 0);
        setLine(inB, 1);
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
    m_pwmCounter++;
    if (m_pwmCounter >= PWM_PERIOD)
        m_pwmCounter = 0;

    updateBridgeSide(m_leftDir,  m_leftDuty,  m_in1, m_in2, m_ena);
    updateBridgeSide(m_rightDir, m_rightDuty, m_in3, m_in4, m_enb);
}


