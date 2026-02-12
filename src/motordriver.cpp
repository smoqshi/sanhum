#include "motordriver.h"

#include <QDebug>
#include <algorithm>
#include <cmath>

// Номера GPIO по твоей схеме (BCM) — проверь и при необходимости поправь.
static constexpr int GPIO_IN1 = 17;
static constexpr int GPIO_IN2 = 27;
static constexpr int GPIO_IN3 = 23;
static constexpr int GPIO_IN4 = 24;
static constexpr int GPIO_ENA = 22;
static constexpr int GPIO_ENB = 18;

MotorDriver::MotorDriver(QObject *parent)
    : QObject(parent)
    , m_chip("gpiochip0")  // Pi 5: "pinctrl-rp1" виден как gpiochip0 [web:5]
    , m_in1()
    , m_in2()
    , m_in3()
    , m_in4()
    , m_ena()
    , m_enb()
    , m_leftDir(MotorDirection::Stop)
    , m_rightDir(MotorDirection::Stop)
    , m_leftDuty(0)
    , m_rightDuty(0)
    , m_pwmCounter(0)
{
    try {
        if (!initLines()) {
            qWarning() << "MotorDriver: failed to init GPIO lines via libgpiod2";
        }
    } catch (const std::exception &e) {
        qWarning() << "MotorDriver: exception in constructor:" << e.what();
    }

    // Если раньше PWM тикал изнутри, можно включить таймер здесь.
    // В твоём проекте pwmTick уже дергается извне, поэтому оставляю закомментированным.
    //
    // QTimer *timer = new QTimer(this);
    // connect(timer, &QTimer::timeout, this, &MotorDriver::pwmTick);
    // timer->start(1);
}

MotorDriver::~MotorDriver()
{
    try {
        if (m_in1.is_requested()) m_in1.release();
        if (m_in2.is_requested()) m_in2.release();
        if (m_in3.is_requested()) m_in3.release();
        if (m_in4.is_requested()) m_in4.release();
        if (m_ena.is_requested()) m_ena.release();
        if (m_enb.is_requested()) m_enb.release();
    } catch (const std::exception &e) {
        qWarning() << "MotorDriver: exception in destructor:" << e.what();
    }
}

bool MotorDriver::initLines()
{
    // Берём линии по номеру из gpiochip0 [web:5].
    m_in1 = m_chip.get_line(GPIO_IN1);
    m_in2 = m_chip.get_line(GPIO_IN2);
    m_in3 = m_chip.get_line(GPIO_IN3);
    m_in4 = m_chip.get_line(GPIO_IN4);
    m_ena = m_chip.get_line(GPIO_ENA);
    m_enb = m_chip.get_line(GPIO_ENB);

    auto requestOut = [](gpiod::line &line, const char *consumer, int initVal) {
        if (!line) {
            qWarning() << "MotorDriver: line for" << consumer << "is invalid";
            return false;
        }
        gpiod::line_request req{
            consumer,
            gpiod::line_request::DIRECTION_OUTPUT,
            initVal ? gpiod::line_request::FLAG_ACTIVE_LOW : 0
        };
        try {
            line.request(req, initVal ? 1 : 0);
        } catch (const std::exception &e) {
            qWarning() << "MotorDriver: line.request failed for" << consumer << ":" << e.what();
            return false;
        }
        return true;
    };

    bool ok = true;
    ok = ok && requestOut(m_in1, "sanhum_in1", 0);
    ok = ok && requestOut(m_in2, "sanhum_in2", 0);
    ok = ok && requestOut(m_in3, "sanhum_in3", 0);
    ok = ok && requestOut(m_in4, "sanhum_in4", 0);
    ok = ok && requestOut(m_ena, "sanhum_ena", 0);
    ok = ok && requestOut(m_enb, "sanhum_enb", 0);

    return ok;
}

void MotorDriver::setLine(gpiod::line &line, int value)
{
    if (!line) return;
    try {
        line.set_value(value ? 1 : 0);
    } catch (const std::exception &e) {
        qWarning() << "MotorDriver: set_value failed:" << e.what();
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
                                   gpiod::line &inA, gpiod::line &inB, gpiod::line &en)
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


