#include "robotmodel.h"
#include "motordriver.h"

#include <QFile>
#include <QJsonObject>
#include <QProcess>
#include <QRegularExpression>
#include <QTextStream>
#include <QtGlobal>
#include <cmath>
#include <algorithm>

// ===== служебные чтения статуса (как раньше) =====

static bool isRunningOnRaspberry()
{
#ifdef Q_OS_LINUX
    QFile f("/proc/device-tree/model");
    if (!f.open(QIODevice::ReadOnly))
        return false;
    const QByteArray model = f.readAll().toLower();
    return model.contains("raspberry");
#else
    return false;
#endif
}

static double readCpuTempC()
{
#ifdef Q_OS_LINUX
    QFile f("/sys/class/thermal/thermal_zone0/temp");
    if (f.open(QIODevice::ReadOnly)) {
        QByteArray b = f.readAll().trimmed();
        bool ok = false;
        const double milli = b.toDouble(&ok);
        if (ok)
            return milli / 1000.0;
    }
#endif
    return 0.0;
}

static double readBoardTempC()
{
#ifdef Q_OS_LINUX
    return readCpuTempC();
#else
    return 0.0;
#endif
}

static double readCpuLoadPercent()
{
#ifdef Q_OS_LINUX
    QFile f("/proc/loadavg");
    if (f.open(QIODevice::ReadOnly)) {
        QTextStream ts(&f);
        double l1 = 0.0;
        ts >> l1;
        return std::clamp(l1 * 100.0, 0.0, 400.0);
    }
#endif
    return 0.0;
}

static void readWifiInfo(QString &ssidOut, int &rssiOut)
{
    ssidOut = QStringLiteral("--");
    rssiOut = 0;
#ifdef Q_OS_LINUX
    QProcess proc;
    proc.start(QStringLiteral("iwconfig"), QStringList() << QStringLiteral("wlan0"));
    if (!proc.waitForFinished(200))
        return;
    const QString out = QString::fromLocal8Bit(proc.readAllStandardOutput());

    QRegularExpression essidRe(R"(ESSID:\"([^\"]*)\")");
    QRegularExpression sigRe(R"(Signal level=([-0-9]+)\s*dBm)");

    auto m1 = essidRe.match(out);
    if (m1.hasMatch())
        ssidOut = m1.captured(1);

    auto m2 = sigRe.match(out);
    if (m2.hasMatch()) {
        bool ok = false;
        int val = m2.captured(1).toInt(&ok);
        if (ok)
            rssiOut = val;
    }
#endif
}

static double readBatteryVoltage()
{
    return 0.0;
}

// ===== конструктор / деструктор =====

RobotModel::RobotModel(QObject *parent)
    : QObject(parent)
    , m_vCmd(0.0)
    , m_wCmd(0.0)
    , m_vActual(0.0)
    , m_wActual(0.0)
    , m_emergency(false)
    , m_x(0.0)
    , m_y(0.0)
    , m_theta(0.0)
    , m_ext(0.5)
    , m_grip(0.3)
    , m_turretDeg(0.0)
    , m_batteryV(12.0)
    , m_cpuTemp(40.0)
    , m_boardTemp(35.0)
    , m_motorDriver(new MotorDriver(this))
    , m_halfTrack(0.15)
    , m_maxWheelLinear(0.5)
{
}

RobotModel::~RobotModel() = default;

// ===== /api/base =====

void RobotModel::setBaseCommand(double vLinear, double vAngular)
{
    // команды из UI (в м/с и рад/с)
    m_vCmd = vLinear;
    m_wCmd = vAngular;
    m_emergency = false;
    updateMotorsFromCommand();
}

void RobotModel::emergencyStop()
{
    m_emergency = true;
    m_vCmd = 0.0;
    m_wCmd = 0.0;

    m_motorDriver->setLeftMotor(MotorDirection::Stop, 0);
    m_motorDriver->setRightMotor(MotorDirection::Stop, 0);
}

// ===== /api/arm =====

void RobotModel::setArmExtension(double ext01)
{
    if (ext01 < 0.0) ext01 = 0.0;
    if (ext01 > 1.0) ext01 = 1.0;
    m_ext = ext01;
}

void RobotModel::setGripper(double grip01)
{
    if (grip01 < 0.0) grip01 = 0.0;
    if (grip01 > 1.0) grip01 = 1.0;
    m_grip = grip01;
}

void RobotModel::setTurretAngle(double angleDeg)
{
    while (angleDeg > 180.0) angleDeg -= 360.0;
    while (angleDeg < -180.0) angleDeg += 360.0;
    m_turretDeg = angleDeg;
}

// ===== шаг симуляции =====

void RobotModel::step(double dt)
{
    if (dt <= 0.0)
        return;

    if (m_emergency) {
        m_vActual = 0.0;
        m_wActual = 0.0;
        return;
    }

    // простая модель: фактическая скорость ≈ командная (можно добавить фильтр)
    m_vActual = m_vCmd;
    m_wActual = m_wCmd;

    integratePose(dt);
}

// ===== обновление моторов =====

void RobotModel::updateMotorsFromCommand()
{
    const double vL = m_vCmd - m_wCmd * m_halfTrack;
    const double vR = m_vCmd + m_wCmd * m_halfTrack;

    double nL = 0.0;
    double nR = 0.0;

    if (m_maxWheelLinear > 1e-6) {
        nL = vL / m_maxWheelLinear;
        nR = vR / m_maxWheelLinear;
    }

    nL = std::max(-1.0, std::min(1.0, nL));
    nR = std::max(-1.0, std::min(1.0, nR));

    auto toDirDuty = [](double n) {
        MotorDirection dir;
        if (n > 1e-3)      dir = MotorDirection::Forward;
        else if (n < -1e-3) dir = MotorDirection::Backward;
        else               dir = MotorDirection::Stop;
        int duty = static_cast<int>(std::lround(std::fabs(n) * 100.0));
        return std::make_pair(dir, duty);
    };

    auto left  = toDirDuty(nL);
    auto right = toDirDuty(nR);

    m_motorDriver->setLeftMotor(left.first, left.second);
    m_motorDriver->setRightMotor(right.first, right.second);
}

// ===== интегрирование позы =====

void RobotModel::integratePose(double dt)
{
    const double dx = m_vActual * std::cos(m_theta) * dt;
    const double dy = m_vActual * std::sin(m_theta) * dt;
    const double dtheta = m_wActual * dt;

    m_x     += dx;
    m_y     += dy;
    m_theta += dtheta;

    while (m_theta > M_PI)  m_theta -= 2.0 * M_PI;
    while (m_theta < -M_PI) m_theta += 2.0 * M_PI;
}

// ===== /api/status =====

QJsonObject RobotModel::makeStatusJson() const
{
    QJsonObject obj;

    obj.insert(QStringLiteral("emergency"), m_emergency);

    obj.insert(QStringLiteral("x"), m_x);
    obj.insert(QStringLiteral("y"), m_y);
    obj.insert(QStringLiteral("theta_deg"), m_theta * 180.0 / M_PI);

    // скорости для dashboard (используются в uiControls.js)
    obj.insert(QStringLiteral("v_linear"), m_vActual);
    obj.insert(QStringLiteral("v_angular_deg"), m_wActual * 180.0 / M_PI);

#ifdef Q_OS_LINUX
    if (isRunningOnRaspberry()) {
        const double cpuTemp   = readCpuTempC();
        const double boardTemp = readBoardTempC();
        const double cpuLoad   = readCpuLoadPercent();
        obj.insert(QStringLiteral("cpu_temp_c"), cpuTemp);
        obj.insert(QStringLiteral("board_temp_c"), boardTemp);
        obj.insert(QStringLiteral("cpu_load_percent"), cpuLoad);

        const double batt = (m_batteryV > 0.0) ? m_batteryV : readBatteryVoltage();
        obj.insert(QStringLiteral("battery_v"), batt);

        obj.insert(QStringLiteral("current_total_a"), 0.0);
        obj.insert(QStringLiteral("current_5v_a"), 0.0);
        obj.insert(QStringLiteral("current_12v_a"), 0.0);
        obj.insert(QStringLiteral("current_motors_a"), 0.0);
        obj.insert(QStringLiteral("current_gpio_ma"), 0.0);

        QString ssid;
        int rssi = 0;
        readWifiInfo(ssid, rssi);
        obj.insert(QStringLiteral("wifi_ssid"), ssid);
        obj.insert(QStringLiteral("wifi_rssi_dbm"), rssi);
    } else
#endif
    {
        obj.insert(QStringLiteral("cpu_temp_c"), m_cpuTemp);
        obj.insert(QStringLiteral("board_temp_c"), m_boardTemp);
        obj.insert(QStringLiteral("cpu_load_percent"), 0.0);

        obj.insert(QStringLiteral("battery_v"), m_batteryV);
        obj.insert(QStringLiteral("current_total_a"), 0.0);
        obj.insert(QStringLiteral("current_5v_a"), 0.0);
        obj.insert(QStringLiteral("current_12v_a"), 0.0);
        obj.insert(QStringLiteral("current_motors_a"), 0.0);
        obj.insert(QStringLiteral("current_gpio_ma"), 0.0);

        obj.insert(QStringLiteral("wifi_ssid"), QStringLiteral("--"));
        obj.insert(QStringLiteral("wifi_rssi_dbm"), 0);
    }

    return obj;
}

// ===== /api/joint_state =====

QJsonObject RobotModel::makeJointStateJson() const
{
    QJsonObject obj;
    obj.insert(QStringLiteral("turret_deg"), m_turretDeg);
    obj.insert(QStringLiteral("arm_ext"),    m_ext);
    obj.insert(QStringLiteral("gripper"),    m_grip);
    return obj;
}

