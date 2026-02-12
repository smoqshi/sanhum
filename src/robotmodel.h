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

    // команды от /api/base
    void setBaseCommand(double vLinear, double vAngular);

    // команды от /api/arm
    void setArmExtension(double ext01);
    void setGripper(double grip01);
    void setTurretAngle(double angleDeg);

    void emergencyStop();

    // шаг симуляции
    void step(double dt);

    // данные для фронтенда
    QJsonObject makeStatusJson() const;      // /api/status
    QJsonObject makeJointStateJson() const;  // /api/joint_state

private:
    // командные скорости
    double m_vCmd;           // м/с
    double m_wCmd;           // рад/с

    // фактические скорости (то, что отправляем назад на UI)
    double m_vActual;        // м/с
    double m_wActual;        // рад/с

    bool   m_emergency;

    // состояние базы (поза)
    double m_x;              // м
    double m_y;              // м
    double m_theta;          // рад

    // манипулятор
    double m_ext;            // 0..1
    double m_grip;           // 0..1
    double m_turretDeg;      // градусы

    // псевдодиагностика
    double m_batteryV;
    double m_cpuTemp;
    double m_boardTemp;

    MotorDriver *m_motorDriver;

    // параметры дифф‑привода
    double m_halfTrack;      // м
    double m_maxWheelLinear; // м/с при duty=100%

    void updateMotorsFromCommand();
    void integratePose(double dt);
};

#endif // ROBOTMODEL_H

