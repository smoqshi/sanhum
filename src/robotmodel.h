#ifndef ROBOTMODEL_H
#define ROBOTMODEL_H

#include <QObject>
#include <QVector2D>
#include <QJsonObject>

class MotorDriver;

class RobotModel : public QObject
{
    Q_OBJECT
public:
    explicit RobotModel(QObject *parent = nullptr);
    ~RobotModel();

    const QVector2D &position() const { return m_pos; }
    double angle() const { return m_angle; }

    double linearVelocity() const { return m_v; }
    double angularVelocity() const { return m_w; }

    // Базовое управление
    void setBaseCommand(double v, double w);
    void emergencyStop();
    bool isEmergency() const { return m_emergency; }

    // Манипулятор
    double armExtension() const { return m_ext; }
    double gripper() const { return m_grip; }
    double turretAngleDeg() const { return m_turretDeg; }

    void setArmExtension(double ext01);
    void setGripper(double grip01);
    void setTurretAngle(double angleDeg);

    // Состояние платформы
    double batteryVoltage() const { return m_batteryV; }
    double cpuTemperature() const { return m_cpuTemp; }
    double boardTemperature() const { return m_boardTemp; }

    // Шаг симуляции
    void step(double dt);

    // Состояние для веб-клиента
    QJsonObject makeStatusJson() const;
    QJsonObject makeJointStateJson() const;

    // Стояночный тормоз (для индикации/логики)
    bool parkingBrake() const { return m_parkingBrake; }
    void setParkingBrake(bool on);
    void toggleParkingBrake();

signals:
    void stateChanged();

private:
    void updateMotorsFromCommand();

    double m_cpuLoad;
    QString m_wifiSsid;
    int m_wifiRssi;

    QVector2D m_pos;
    double m_angle;

    double m_v;
    double m_w;

    double m_targetV;
    double m_targetW;

    bool m_emergency;

    double m_ext;
    double m_grip;
    double m_turretDeg;

    double m_batteryV;
    double m_cpuTemp;
    double m_boardTemp;

    MotorDriver *m_motorDriver;

    double m_halfTrack;
    double m_maxWheelLinear;

    bool m_parkingBrake;   // новый флаг
};

#endif // ROBOTMODEL_H

