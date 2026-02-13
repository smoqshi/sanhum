#ifndef ROBOTMODEL_H
#define ROBOTMODEL_H

#include <QObject>
#include <QJsonObject>

class MotorDriver;

class RobotModel : public QObject
{
    Q_OBJECT
public:
    explicit RobotModel(QObject *parent = nullptr);
    ~RobotModel();

    // /api/base
    void setBaseCommand(double v, double w);

    // манипулятор
    void setArmExtension(double ext01);
    void setGripper(double grip01);
    void setTurretAngle(double angleDeg);

    // аварийная остановка
    void emergencyStop();

    // шаг модели (вызывается из таймера)
    void step(double dt);

    // JSON для веб‑клиента
    QJsonObject makeStatusJson() const;
    QJsonObject makeJointStateJson() const;

private:
    // динамика базы
    double m_v;          // линейная скорость команды, м/с
    double m_w;          // угловая скорость команды, рад/с
    bool   m_emergency;

    // манипулятор
    double m_ext;        // 0..1
    double m_grip;       // 0..1
    double m_turretDeg;  // градусы

    // диагностика (для не‑Raspberry окружения)
    double m_batteryV;
    double m_cpuTemp;
    double m_boardTemp;

    // драйвер моторов
    MotorDriver *m_motorDriver;

    // параметры базы
    double m_halfTrack;      // половина колеи, м
    double m_maxWheelLinear; // макс. линейная скорость колеса при duty=100%, м/с

    void updateMotorsFromCommand();
};

#endif // ROBOTMODEL_H
