#ifndef ROBOTMODEL_H
#define ROBOTMODEL_H

#include <QObject>
#include <QJsonObject>

#include "motordriver.h"

// Модель мобильного робота и манипулятора
class RobotModel : public QObject
{
    Q_OBJECT
public:
    explicit RobotModel(QObject *parent = nullptr);
    ~RobotModel();

    // База
    void emergencyStop();
    void setBaseCommand(double v, double w);      // v [м/с], w [рад/с]
    void step(double dt);                         // шаг интегратора

    // Манипулятор + эффектор
    void setArmExtension(double ext01);           // [0..1]
    void setGripper(double grip01);              // [0..1]
    void setTurretAngle(double angleDeg);        // [град]

    // Формирование JSON для web‑клиента
    QJsonObject makeStatusJson() const;
    QJsonObject makeJointStateJson() const;

private:
    MotorDriver m_motorDriver;

    // База
    bool   m_emergency;
    double m_v;           // линейная скорость, м/с
    double m_w;           // угловая скорость, рад/с

    // Состояние манипулятора
    double m_ext;         // [0..1] относительное выдвижение
    double m_grip;        // [0..1] захват
    double m_turretDeg;   // [град]

    // датчики / служебные поля (заглушки)
    double m_batteryV;
    double m_cpuTemp;
    double m_boardTemp;
};

#endif // ROBOTMODEL_H
