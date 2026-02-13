#include "robotmodel.h"
#include "motordriver.h"

#include <QtMath>
#include <QJsonObject>
#include <QFile>
#include <QTextStream>
#include <QRegularExpression>
#include <QProcess>

RobotModel::RobotModel(QObject *parent)
    : QObject(parent)
    , m_pos(0.0f, 0.0f)
    , m_angle(0.0)
    , m_v(0.0)
    , m_w(0.0)
    , m_targetV(0.0)
    , m_targetW(0.0)
    , m_emergency(false)
    , m_ext(0.5)
    , m_grip(0.3)
    , m_turretDeg(0.0)
    , m_batteryV(12.0)
    , m_cpuTemp(40.0)
    , m_boardTemp(35.0)
    , m_motorDriver(new MotorDriver(this))
    , m_halfTrack(0.15)
    , m_maxWheelLinear(0.5)
    , m_parkingBrake(false)
    , m_cpuLoad(0.0)
    , m_wifiSsid()
    , m_wifiRssi(0)
{
}

RobotModel::~RobotModel() = default;

void RobotModel::emergencyStop()
{
    m_emergency = true;
    m_v = 0.0;
    m_w = 0.0;
    updateMotorsFromCommand();
}

void RobotModel::setBaseCommand(double v, double w)
{
    m_targetV = v;
    m_targetW = w;
}

void RobotModel::updateMotorsFromCommand()
{
    if (!m_motorDriver)
        return;

    if (m_emergency || m_parkingBrake) {
        m_motorDriver->setLeftMotor(MotorDirection::Stop, 0);
        m_motorDriver->setRightMotor(MotorDirection::Stop, 0);
        return;
    }

    double vLeft = m_targetV - m_halfTrack * m_targetW;
    double vRight = m_targetV + m_halfTrack * m_targetW;

    auto convert = [this](double vWheel, MotorDirection &dir, int &duty) {
        if (qFuzzyIsNull(vWheel)) {
            dir = MotorDirection::Stop;
            duty = 0;
            return;
        }
        dir = (vWheel > 0) ? MotorDirection::Forward : MotorDirection::Backward;
        double mag = qMin(qAbs(vWheel) / m_maxWheelLinear, 1.0);
        duty = int(mag * 100.0);
    };

    MotorDirection dirL, dirR;
    int dutyL, dutyR;
    convert(vLeft, dirL, dutyL);
    convert(vRight, dirR, dutyR);

    m_motorDriver->setLeftMotor(dirL, dutyL);
    m_motorDriver->setRightMotor(dirR, dutyR);
}

void RobotModel::setArmExtension(double ext01)
{
    m_ext = qBound(0.0, ext01, 1.0);
}

void RobotModel::setGripper(double grip01)
{
    m_grip = qBound(0.0, grip01, 1.0);
}

void RobotModel::setTurretAngle(double angleDeg)
{
    m_turretDeg = angleDeg;
}

static bool isRunningOnRaspberry()
{
#ifdef Q_OS_LINUX
    QFile f("/proc/device-tree/model");
    if (!f.open(QIODevice::ReadOnly))
        return false;
    const QByteArray data = f.readAll();
    return data.contains("Raspberry Pi");
#else
    return false;
#endif
}

static double readBoardTempC()
{
#ifdef Q_OS_LINUX
    QFile f("/sys/class/thermal/thermal_zone0/temp");
    if (f.open(QIODevice::ReadOnly)) {
        QByteArray data = f.readAll();
        bool ok = false;
        double val = data.trimmed().toDouble(&ok);
        if (ok)
            return val / 1000.0;
    }
#endif
    return 0.0;
}

static double readCpuTempC()
{
#ifdef Q_OS_LINUX
    QFile f("/sys/class/thermal/thermal_zone1/temp");
    if (f.open(QIODevice::ReadOnly)) {
        QByteArray data = f.readAll();
        bool ok = false;
        double val = data.trimmed().toDouble(&ok);
        if (ok)
            return val / 1000.0;
    }
#endif
    return 0.0;
}

static double readCpuLoadPercent()
{
#ifdef Q_OS_LINUX
    QFile f("/proc/loadavg");
    if (f.open(QIODevice::ReadOnly)) {
        QTextStream ts(&f);
        double oneMin = 0.0;
        ts >> oneMin;
        return oneMin * 100.0;
    }
#endif
    return 0.0;
}

static void readWifiInfo(QString &ssidOut, int &rssiOut)
{
    ssidOut.clear();
    rssiOut = 0;

#ifdef Q_OS_LINUX
    QProcess proc;
    proc.start("iwconfig");
    proc.waitForFinished(500);
    const QString out = QString::fromLocal8Bit(proc.readAllStandardOutput());

    QRegularExpression reSsid(R"(ESSID:\"([^\"]*)\")");
    QRegularExpression reRssi(R"(Signal level=(-?\d+) dBm)");

    auto m1 = reSsid.match(out);
    if (m1.hasMatch()) {
        ssidOut = m1.captured(1);
    }

    auto m2 = reRssi.match(out);
    if (m2.hasMatch()) {
        rssiOut = m2.captured(1).toInt();
    }
#endif
}

void RobotModel::setParkingBrake(bool on)
{
    if (m_parkingBrake == on)
        return;
    m_parkingBrake = on;
    updateMotorsFromCommand();
}

void RobotModel::toggleParkingBrake()
{
    m_parkingBrake = !m_parkingBrake;
    updateMotorsFromCommand();
}

void RobotModel::step(double dt)
{
    updateMotorsFromCommand();

    if (m_emergency || m_parkingBrake) {
        m_v = 0.0;
        m_w = 0.0;
    } else {
        m_v = m_targetV;
        m_w = m_targetW;
    }

    double dx = m_v * qCos(m_angle) * dt;
    double dy = m_v * qSin(m_angle) * dt;
    m_pos += QVector2D(dx, dy);
    m_angle += m_w * dt;

    if (isRunningOnRaspberry()) {
        m_boardTemp = readBoardTempC();
        m_cpuTemp   = readCpuTempC();
        m_cpuLoad   = readCpuLoadPercent();
        readWifiInfo(m_wifiSsid, m_wifiRssi);

    }

    emit stateChanged();
}

QJsonObject RobotModel::makeStatusJson() const
{
    QJsonObject obj;
    obj.insert(QStringLiteral("x"), m_pos.x());
    obj.insert(QStringLiteral("y"), m_pos.y());
    obj.insert(QStringLiteral("angle"), m_angle);
    obj.insert(QStringLiteral("v"), m_v);
    obj.insert(QStringLiteral("w"), m_w);
    obj.insert(QStringLiteral("emergency"), m_emergency);
    obj.insert(QStringLiteral("parking_brake"), m_parkingBrake);
    obj.insert(QStringLiteral("battery"), m_batteryV);
    obj.insert(QStringLiteral("cpu_temp"), m_cpuTemp);
    obj.insert(QStringLiteral("board_temp"), m_boardTemp);
    obj.insert(QStringLiteral("cpu_load"), m_cpuLoad);
    obj.insert(QStringLiteral("wifi_ssid"), m_wifiSsid);
    obj.insert(QStringLiteral("wifi_rssi"), m_wifiRssi);
    return obj;
}

QJsonObject RobotModel::makeJointStateJson() const
{
    QJsonObject obj;
    obj.insert(QStringLiteral("ext"), m_ext);
    obj.insert(QStringLiteral("grip"), m_grip);
    obj.insert(QStringLiteral("turret"), m_turretDeg);
    return obj;
}


