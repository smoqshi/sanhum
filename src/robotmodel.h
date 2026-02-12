#ifndef ROBOTMODEL_H
#define ROBOTMODEL_H

#include <QObject>
#include <QJsonObject>

class MotorDriver;

/**
 * @brief Математическая модель робота и источник данных статуса для веб‑клиента.
 *
 * Модель:
 *  - принимает команды скорости базы и положения манипулятора;
 *  - в методе step(dt) обновляет внутреннее состояние;
 *  - формирует JSON для эндпоинтов /api/status и /api/joint_state.
 *
 * Построено по рекомендациям учебной литературы по киберфизическим системам:
 * см., например, Ogata K. "Modern Control Engineering" и стандартный подход
 * к дискретизации динамики роботов в шагах dt.[cite:1]
 */
class RobotModel : public QObject
{
    Q_OBJECT
public:
    explicit RobotModel(QObject *parent = nullptr);
    ~RobotModel();

    // ===== /api/base: линейная и угловая скорости =====
    void setBaseCommand(double v, double w);

    // ===== /api/arm: манипулятор =====
    void setArmExtension(double ext01);   // [0;1]
    void setGripper(double grip01);       // [0;1]
    void setTurretAngle(double angleDeg); // [-180;180]

    // ===== аварийная остановка =====
    void emergencyStop();

    // ===== главный шаг модели (вызывается из таймера) =====
    void step(double dt);

    // ===== JSON для веб‑клиента =====
    QJsonObject makeStatusJson() const;      // /api/status
    QJsonObject makeJointStateJson() const;  // /api/joint_state

private:
    // --- команды на базу ---
    double m_v;          // линейная скорость команды, м/с
    double m_w;          // угловая скорость команды, рад/с
    bool   m_emergency;  // признак аварийной остановки

    // --- состояние манипулятора ---
    double m_ext;        // вылет звена, 0..1
    double m_grip;       // положение захвата, 0..1
    double m_turretDeg;  // азимут башни, градусы

    // --- псевдодиагностика (для не‑Raspberry окружения) ---
    double m_batteryV;
    double m_cpuTemp;
    double m_boardTemp;

    // --- драйвер моторов (абстрактный) ---
    MotorDriver *m_motorDriver;

    // --- параметры базы (геометрия и масштаб ШИМ) ---
    double m_halfTrack;      // половина колеи, м
    double m_maxWheelLinear; // макс. линейная скорость колеса при duty=100%, м/с

    // --- внутреннее интегрированное состояние базы (для симуляции) ---
    double m_x;      // положение по X, м
    double m_y;      // положение по Y, м
    double m_theta;  // ориентация, рад

    // пересчёт (v,w) -> (направление, duty) для моторов
    void updateMotorsFromCommand();

    // дискретное интегрирование позы (модель дифф‑привода)
    void integratePose(double dt);
};

#endif // ROBOTMODEL_H
