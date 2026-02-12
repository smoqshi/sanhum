#include "motordriver.h"

#include <QDebug>
#include <algorithm>
#include <cmath>

// BCM GPIO под твою схему — поменяй на свои реально используемые номера
static constexpr int GPIO_IN1 = 17;
static constexpr int GPIO_IN2 = 27;
static constexpr int GPIO_IN3 = 23;
static constexpr int GPIO_IN4 = 24;

MotorDriver::MotorDriver(QObject *parent)
    : QObject(parent)
    , m_chip("gpiochip0")
    , m_request()
    , m_idxIn1(GPIO_IN1)
    , m_idxIn2(GPIO_IN2)
    , m_idxIn3(GPIO_IN3)
    , m_idxIn4(GPIO_IN4)
    , m_leftDir(MotorDirection::Stop)
    , m_rightDir(MotorDirection::Stop)
    , m_leftDuty(0)
    , m_rightDuty(0)
    , m_pwmCounter(0)
{
    try {
        if (!initRequest()) {
            qWarning() << "MotorDriver: failed to init GPIO line_request";
        }
    } catch (const std::exception &e) {
        qWarning() << "MotorDriver: exception in constructor:" << e.what();
    }
}

MotorDriver::~MotorDriver()
{
    try {
        if (m_request) {
            m_request.release();
        }
    } catch (const std::exception &e) {
        qWarning() << "MotorDriver: exception in destructor:" << e.what();
    }
}

bool MotorDriver::initRequest()
{
    gpiod::line_config line_cfg;
    gpiod::line_settings settings;

    settings.set_direction(gpiod::line::direction::OUTPUT);
    settings.set_output_value(gpiod::line::value::INACTIVE);

    line_cfg.add_line_settings(
        { m_idxIn1, m_idxIn2, m_idxIn3, m_idxIn4 },
        settings
    );

    gpiod::request_config req_cfg;
    req_cfg.set_consumer("sanhum_motors");

    try {
        m_request = m_chip.request_lines(req_cfg, line_cfg);
    } catch (const std::exception &e) {
        qWarning() << "MotorDriver: request_lines failed:" << e.what();
        return false;
    }

    return true;
}

void MotorDriver::setLine(int offset, int value)
{
    if (!m_request) return;

    try {
        m_request.set_value(offset,
                            value ? gpiod::line::value::ACTIVE
                                  : gpiod::line::value::INACTIVE);
    } catch (const std::exception &e) {
        qWarning() << "MotorDriver: set_value failed on offset" << offset << ":" << e.what();
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
                                   int offsetInA, int offsetInB)
{
    // Программный PWM по IN‑линиям: duty определяет, сколько времени INA активен/INB неактивен и наоборот.
    int phaseA = 0;
    int phaseB = 0;

    switch (dir) {
    case MotorDirection::Stop:
        phaseA = 0;
        phaseB = 0;
        break;

    case MotorDirection::Forward:
        phaseA = (m_pwmCounter < duty) ? 1 : 0;
        phaseB = 0;
        break;

    case MotorDirection::Backward:
        phaseA = 0;
        phaseB = (m_pwmCounter < duty) ? 1 : 0;
        break;
    }

    setLine(offsetInA, phaseA);
    setLine(offsetInB, phaseB);
}

void MotorDriver::pwmTick()
{
    m_pwmCounter++;
    if (m_pwmCounter >= PWM_PERIOD)
        m_pwmCounter = 0;

    updateBridgeSide(m_leftDir,  m_leftDuty,  m_idxIn1, m_idxIn2);
    updateBridgeSide(m_rightDir, m_rightDuty, m_idxIn3, m_idxIn4);
}
