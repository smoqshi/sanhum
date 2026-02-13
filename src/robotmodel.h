#ifndef ROBOTMODEL_H
#define ROBOTMODEL_H

#include <QObject>
#include <QVector2D>
#include <QJsonObject>

class RobotModel : public QObject
{
    Q_OBJECT
public:
    explicit RobotModel(QObject *parent = nullptr);

    // Положение и ориентация робота
    const QVector2D &position() const { return m_pos; }
    double angle() const { return m_angle; }

    // Линейная и угловая скорости
    double linearVelocity() const { return m_v; }
    double angularVelocity() const { return m_w; }

    // Команды
    void setTargetVelocities(double v, double w);
    void emergencyStop(bool on);
    bool emergency() const { return m_emergency; }

    // Стояночный тормоз (для индикации и логики)
    bool parkingBrake() const { return m_parkingBrake; }
    void setParkingBrake(bool on);
    void toggleParkingBrake();

    // Шаг симуляции
    void step(double dt);

    // Сериализация состояния для веб-клиента
    QJsonObject makeStatusJson() const;

signals:
    void stateChanged();

private:
    QVector2D m_pos;
    double m_angle;

    double m_v;
    double m_w;

    double m_targetV;
    double m_targetW;

    bool m_emergency;
    bool m_parkingBrake;  // новый флаг стояночного тормоза

    // внутренние параметры модели, трения и т.п.
    double m_linAccel;
    double m_angAccel;
};

#endif // ROBOTMODEL_H
