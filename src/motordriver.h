#ifndef MOTORDRIVER_H
#define MOTORDRIVER_H

#include <QObject>
#include <QTimer>
#include <QUdpSocket>
#include <QProcess>

enum class MotorDirection {
    Stop = 0,
    Forward,
    Backward
};

class MotorDriver : public QObject
{
    Q_OBJECT
public:
    explicit MotorDriver(QObject *parent = nullptr);

    void setLeftMotor(MotorDirection dir, int duty);
    void setRightMotor(MotorDirection dir, int duty);

    void emergencyBrake();

private slots:
    void onUpdateTimer();

private:
    void sendCommand();
    void startPythonDaemon();
    void stopPythonDaemon();

    MotorDirection m_leftDir;
    MotorDirection m_rightDir;
    int m_leftDuty;
    int m_rightDuty;
    bool m_brake;

    QTimer m_updateTimer;
    QUdpSocket m_socket;

    QProcess m_motorProcess;
};

#endif // MOTORDRIVER_H
