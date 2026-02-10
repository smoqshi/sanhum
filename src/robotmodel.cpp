#include "RobotModel.h"
#include "MotorDriver.h"

#include <QtMath>
#include <algorithm>

// Конструктор/деструктор – оставь как было у тебя, я даю пример.

RobotModel::RobotModel(QObject *parent)
    : QObject(parent),
m_motorDriver(this),
m_emergency(false),
m_v(0.0),
m_w(0.0)
{
}

RobotModel::~RobotModel() = default;

// ===== АВАРИЙНАЯ ОСТАНОВКА =====

void RobotModel::emergencyStop()
{
    m_emergency = true;
    m_v = 0.0;
    m_w = 0.0;

    // Оба мотора стоп, 0% скважность
    m_motorDriver.setLeftMotor(MotorDirection::Stop, 0);
    m_motorDriver.setRightMotor(MotorDirection::Stop, 0);
}

// Сюда, как и раньше, прилетает команда /api/base (линейная v и угловая w)
void RobotModel::setBaseCommand(double v, double w)
{
    m_v = v;
    m_w = w;
    m_emergency = false; // если ручной ресет нужен – можешь убрать
}

// ===== ГЛАВНЫЙ ШАГ МОДЕЛИ БАЗЫ =====

void RobotModel::step(double dt)
{
    Q_UNUSED(dt);

    if (m_emergency) {
        // на всякий случай дублируем
        m_motorDriver.setLeftMotor(MotorDirection::Stop, 0);
        m_motorDriver.setRightMotor(MotorDirection::Stop, 0);
        return;
    }

    // === ПАРАМЕТРЫ РОБОТА ===
    // Максимальная линейная скорость колеса (м/с) – подставь свою
    const double maxWheelLinear = 0.5;
    // Полу‑база (половина расстояния между колёсами), м
    const double halfTrack = 0.15;

    // === ПОЛУЧАЕМ v, w ИЗ ПОЛЕЙ (их тебе выставляет HTTP/GAMEPAD) ===
    const double v = m_v; // м/с
    const double w = m_w; // рад/с

    // === ИНВЕРСНАЯ КИНЕМАТИКА ДИФФ. ПРИВОДА ===
    // vL = v - w * L, vR = v + w * L
    const double vL = v - w * halfTrack;
    const double vR = v + w * halfTrack;

    // Нормируем к −1..1 по maxWheelLinear
    double nL = 0.0;
    double nR = 0.0;

    if (maxWheelLinear > 1e-6) {
        nL = vL / maxWheelLinear;
        nR = vR / maxWheelLinear;
    }

    // Ограничение −1..1
    nL = std::max(-1.0, std::min(1.0, nL));
    nR = std::max(-1.0, std::min(1.0, nR));

    // === ПРЕОБРАЗУЕМ В НАПРАВЛЕНИЕ + % СКОРОСТИ ===

    auto toDirAndDuty = [](double norm) {
        MotorDirection dir;
        if (norm > 1e-3)
            dir = MotorDirection::Forward;
        else if (norm < -1e-3)
            dir = MotorDirection::Backward;
        else
            dir = MotorDirection::Stop;

        const int duty = static_cast<int>(std::round(std::abs(norm) * 100.0));
        return std::make_pair(dir, duty);
    };

    auto left  = toDirAndDuty(nL);
    auto right = toDirAndDuty(nR);

    m_motorDriver.setLeftMotor(left.first, left.second);
    m_motorDriver.setRightMotor(right.first, right.second);
}
