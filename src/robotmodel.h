#ifndef ROBOTMODEL_H
#define ROBOTMODEL_H

#include <QObject>
#include <QJsonObject>

#include "motordriver.h"

class RobotModel : public QObject
{
    Q_OBJECT
public:
    explicit RobotModel(QObject *parent = nullptr);
    ~RobotModel();

    // База
    void emergencyStop();
    void setBaseCommand(double v, double w);
    void step(double dt);

    // Манипулятор + эффектор
    void setArmExtension(double ext01);
    void setGripper(double grip01);
    void setTurretAngle(double angleDeg);

    // Формирование JSON для web‑клиента
    QJsonObject makeStatusJson() const;
    QJsonObject makeJointStateJson() const;

private:
    MotorDriver m_motorDriver;

    bool   m_emergency;
    double m_v;
    double m_w;

    double m_ext;
    double m_grip;
    double m_turretDeg;

    double m_batteryV;
    double m_cpuTemp;
    double m_boardTemp;
};

#endif // ROBOTMODEL_H
