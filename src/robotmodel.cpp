#include "robotmodel.h"
#include "motordriver.h"

#include <QtGlobal>
#include <QJsonObject>
#include <QJsonArray>
#include <algorithm>
#include <cmath>

// Конструктор/деструктор
RobotModel::RobotModel(QObject *parent)
    : QObject(parent)
    , m_motorDriver(this)
    , m_emergency(false)
    , m_v(0.0)
    , m_w(0.0)
    , m_ext(0.5)
    , m_grip(0.3)
    , m_turretDeg(0.0)
    , m_batteryV(12.0)
    , m_cpuTemp(40.0)
    , m_boardTemp(35.0)
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

// Сюда приходят команды /api/base (линейная v и угловая w)
void RobotModel::setBaseCommand(double v, double w)
{
    m_v = v;
    m_w = w;
    m_emergency = false; // если нужен ручной сброс, можно убрать
}

// ===== ГЛАВНЫЙ ШАГ МОДЕЛИ БАЗЫ =====
void RobotModel::step(double dt)
{
    Q_UNUSED(dt);

    if (m_emergency) {
        // дублируем на всякий случай
        m_motorDriver.setLeftMotor(MotorDirection::Stop, 0);
        m_motorDriver.setRightMotor(MotorDirection::Stop, 0);
        return;
    }

    // === ПАРАМЕТРЫ РОБОТА ===
    // Максимальная линейная скорость колеса (м/с)
    const double maxWheelLinear = 0.5;
    // Полу‑база (половина расстояния между колёсами), м
    const double halfTrack = 0.15;

    // === ИНВЕРСНАЯ КИНЕМАТИКА ДИФФ. ПРИВОДА ===
    // vL = v - w * L, vR = v + w * L
    const double vL = m_v - m_w * halfTrack;
    const double vR = m_v + m_w * halfTrack;

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

        const int duty =
            static_cast<int>(std::lround(std::fabs(norm) * 100.0));

        return std::make_pair(dir, duty);
    };

    auto left  = toDirAndDuty(nL);
    auto right = toDirAndDuty(nR);

    m_motorDriver.setLeftMotor(left.first, left.second);
    m_motorDriver.setRightMotor(right.first, right.second);
}

// ===== МАНИПУЛЯТОР / ЭФФЕКТОР =====

void RobotModel::setArmExtension(double ext01)
{
    if (ext01 < 0.0)
        ext01 = 0.0;
    if (ext01 > 1.0)
        ext01 = 1.0;
    m_ext = ext01;
}

void RobotModel::setGripper(double grip01)
{
    if (grip01 < 0.0)
        grip01 = 0.0;
    if (grip01 > 1.0)
        grip01 = 1.0;
    m_grip = grip01;
}

void RobotModel::setTurretAngle(double angleDeg)
{
    // нормируем к [-180; 180]
    while (angleDeg > 180.0) angleDeg -= 360.0;
    while (angleDeg < -180.0) angleDeg += 360.0;
    m_turretDeg = angleDeg;
}

// ===== JSON ДЛЯ WEB‑КЛИЕНТА =====

QJsonObject RobotModel::makeStatusJson() const
{
    QJsonObject obj;
    obj.insert(QStringLiteral("emergency"), m_emergency);
    obj.insert(QStringLiteral("battery_v"), m_batteryV);
    obj.insert(QStringLiteral("cpu_temp_c"), m_cpuTemp);
    obj.insert(QStringLiteral("board_temp_c"), m_boardTemp);

    // Можно добавить больше полей по мере появления реальных датчиков
    return obj;
}

QJsonObject RobotModel::makeJointStateJson() const
{
    QJsonObject obj;
    obj.insert(QStringLiteral("turret_deg"), m_turretDeg);
    obj.insert(QStringLiteral("arm_ext"), m_ext);
    obj.insert(QStringLiteral("gripper"), m_grip);

    return obj;
}

