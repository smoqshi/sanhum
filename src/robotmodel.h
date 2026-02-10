#pragma once

#include <QObject>
#include <QMutex>
#include <QJsonObject>
#include "MotorDriver.h"

    struct BaseState {
    double x {0.0};
    double y {0.0};
    double heading {0.0};   // rad
    double vLinear {0.0};   // m/s
    double vAngular {0.0};  // rad/s
};

struct ArmState {
    double q1 {0.0};
    double q2 {0.0};
    double q3 {0.0};
    double q4 {0.0};
    double gripper {0.3};   // 0..1
};

class RobotModel : public QObject {
    Q_OBJECT
public:
    explicit RobotModel(QObject *parent = nullptr);

    void setBaseCommand(double vLinear, double vAngular);
    void setArmExtension(double ext);        // 0..1
    void setGripper(double val);             // 0..1
    void setTurretAngle(double angleRad);

    // экстренный тормоз
    void emergencyStop();

    BaseState baseState() const;
    ArmState armState() const;

    QJsonObject makeStatusJson() const;
    QJsonObject makeJointStateJson() const;

public slots:
    void step(double dt);

signals:
    void statusChanged();

private:
    mutable QMutex m_stateMutex;
    QMutex m_hardwareMutex;

    BaseState m_base;
    ArmState  m_arm;

    double m_turretAngle {0.0};
    double m_armExtend   {0.5};

    double m_vLinearCmd  {0.0};
    double m_vAngularCmd {0.0};

    static constexpr double WHEELBASE    = 0.35;  // m
    static constexpr double WHEEL_RADIUS = 0.05;  // m
    static constexpr double MAX_OMEGA    = 10.0;  // rad/s

    MotorDriver m_motorDriver;
};
