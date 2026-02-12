#include "motordriver.h"

#include <QDebug>
#include <algorithm>

// BCM GPIO – подставь свои реальные номера по схеме
static constexpr int GPIO_IN1 = 17;
static constexpr int GPIO_IN2 = 27;
static constexpr int GPIO_IN3 = 23;
static constexpr int GPIO_IN4 = 24;

MotorDriver::MotorDriver(QObject *parent)
    : QObject(parent)
    , m_chip("gpiochip0")
    , m_request( gpiod::request_builder{}.do_request() ) // временный пустой, сразу перезатрём
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
    using namespace gpiod;

    // Конфигурация линий [web:18][web:27]
    line_settings settings;
    settings.set_direction(line::direction::OUTPUT);
    settings.set_output_value(line::value::INACTIVE);

    line_config lcfg;
    lcfg.add_line_settings(
        line::offsets{ static_cast<unsigned int>(m_idxIn1),
                       static_cast<unsigned int>(m_idxIn2),
                       static_cast<unsigned int>(m_idxIn3),
                       static_cast<unsigned int>(m_idxIn4) },
        settings
    );

    request_config rcfg;
    rcfg.set_consumer("sanhum_motors");

    request_builder builder;
    builder.set_chip(m_chip);
    builder.set_request_config(rcfg);
    builder.set_line_config(lcfg);

    try {
        m_request = builder.do_request();
    } catch (const std::exception &e) {
        qWarning() << "MotorDriver: builder.do_request failed:" << e.what();
        return false;
    }

    return true;
}

void MotorDriver::setLine(int offset, int value)
{
    if (!m_request)
        return;

    try {
        m_request.set_value(
            static_cast<unsigned int>(offset),
            value ? gpiod::line::value::ACTIVE : gpiod::line::value::INACTIVE
        );
    } catch (const std::exception &e) {
        qWarning() << "MotorDriver: set_value failed on offset"
                   << offset << ":" << e.what();
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
