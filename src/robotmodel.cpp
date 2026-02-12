#include "robotmodel.h"
#include "motordriver.h"

#include <QDebug>
#include <QFile>
#include <QProcess>
#include <QRegularExpression>
#include <QTextStream>
#include <QtGlobal>

#include <algorithm>
#include <cmath>

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ СТАТУСА (платформозависимые) =====

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
        // Грубая оценка загрузки в %
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
    // TODO: подключить реальный АЦП/датчик на целевом железе
    return 0.0;
}

// ===== КОНСТРУКТОР / ДЕСТРУКТОР =====

RobotModel::RobotModel(QObject *parent)
    : QObject(parent)
    , m_v(0.0)
    , m_w(0.0)
    , m_emergency(false)
    , m_ext(0.5)
    , m_grip(0.3)
    , m_turretDeg(0.0)
    , m_batteryV(12.0)
    , m_cpuTemp(40.0)
    , m_boardTemp(35.0)
    , m_motorDriver(new MotorDriver(this))
    , m_halfTrack(0.15)        // плечо базы, м
    , m_maxWheelLinear(0.5)    // м/с при duty=100%
    , m_x(0.0)
    , m_y(0.0)
    , m_theta(0.0)
{
}

RobotModel::~RobotModel() = default;

// ===== АВАРИЙНАЯ ОСТАНОВКА =====

void RobotModel::emergencyStop()
{
    m_emergency = true;
    m_v = 0.0;
    m_w = 0.0;

    m_motorDriver->setLeftMotor(MotorDirection::Stop, 0);
    m_motorDriver->setRightMotor(MotorDirection::Stop, 0);

    qDebug() << "Emergency stop activated";
}

// ===== /api/base: КОМАНДА ОТ ВЕБ‑КЛИЕНТА =====

void RobotModel::setBaseCommand(double v, double w)
{
    qDebug() << "BaseCommand v=" << v << "w=" << w;

    m_v = v;
    m_w = w;
    m_emergency = false;

    // Немедленно обновляем ШИМ, чтобы база реагировала без ожидания следующего шага
    updateMotorsFromCommand();
}

// ===== ГЛАВНЫЙ ШАГ МОДЕЛИ (СИМУЛЯЦИЯ ВРЕМЕНИ) =====

void RobotModel::step(double dt)
{
    if (dt <= 0.0)
        return;

    if (m_emergency) {
        m_motorDriver->setLeftMotor(MotorDirection::Stop, 0);
        m_motorDriver->setRightMotor(MotorDirection::Stop, 0);
        return;
    }

    // 1) пересчитать команду скоростей в команды для моторов
    updateMotorsFromCommand();

    // 2) проинтегрировать позу базы (x, y, theta)
    integratePose(dt);
}

// ===== ПЕРЕСЧЁТ (v,w) -> (НАПРАВЛЕНИЕ, ШИМ) =====

void RobotModel::updateMotorsFromCommand()
{
    // Модель дифф‑привода: vL = v - w * L/2, vR = v + w * L/2 [cite:1]
    const double vL = m_v - m_w * m_halfTrack;
    const double vR = m_v + m_w * m_halfTrack;

    double nL = 0.0;
    double nR = 0.0;

    if (m_maxWheelLinear > 1e-6) {
        nL = vL / m_maxWheelLinear;
        nR = vR / m_maxWheelLinear;
    }

    // ограничение диапазона duty [-1;1]
    nL = std::max(-1.0, std::min(1.0, nL));
    nR = std::max(-1.0, std::min(1.0, nR));

    auto toDirAndDuty = [](double norm) {
        MotorDirection dir;
        if (norm > 1e-3)
            dir = MotorDirection::Forward;
        else if (norm < -1e-3)
            dir = MotorDirection::Backward;
        else
            dir = MotorDirection::Stop;

        const int duty = static_cast<int>(std::lround(std::fabs(norm) * 100.0));
        return std::make_pair(dir, duty);
    };

    auto left  = toDirAndDuty(nL);
    auto right = toDirAndDuty(nR);

    m_motorDriver->setLeftMotor(left.first, left.second);
    m_motorDriver->setRightMotor(right.first, right.second);

    qDebug() << "updateMotorsFromCommand:"
             << "v=" << m_v << "w=" << m_w
             << "vL=" << vL << "vR=" << vR
             << "nL=" << nL << "nR=" << nR
             << "dutyL=" << left.second << "dutyR=" << right.second;
}

// ===== ИНТЕГРИРОВАНИЕ ПОЗЫ БАЗЫ =====

void RobotModel::integratePose(double dt)
{
    // Простая дискретизация уравнений кинематики дифф‑привода:
    // x_{k+1} = x_k + v * cos(theta) * dt
    // y_{k+1} = y_k + v * sin(theta) * dt
    // theta_{k+1} = theta_k + w * dt [cite:1]

    const double dx = m_v * std::cos(m_theta) * dt;
    const double dy = m_v * std::sin(m_theta) * dt;
    const double dtheta = m_w * dt;

    m_x     += dx;
    m_y     += dy;
    m_theta += dtheta;

    // Нормализация угла к [-pi; pi]
    while (m_theta > M_PI)
        m_theta -= 2.0 * M_PI;
    while (m_theta < -M_PI)
        m_theta += 2.0 * M_PI;
}

// ===== МАНИПУЛЯТОР =====

void RobotModel::setArmExtension(double ext01)
{
    if (ext01 < 0.0)
        ext01 = 0.0;
    if (ext01 > 1.0)
        ext01 = 1.0;

    m_ext = ext01;
}

void RobotModel::setGripper(double grip01)
{
    if (grip01 < 0.0)
        grip01 = 0.0;
    if (grip01 > 1.0)
        grip01 = 1.0;

    m_grip = grip01;
}

void RobotModel::setTurretAngle(double angleDeg)
{
    while (angleDeg > 180.0)
        angleDeg -= 360.0;
    while (angleDeg < -180.0)
        angleDeg += 360.0;

    m_turretDeg = angleDeg;
}

// ===== JSON ДЛЯ WEB‑КЛИЕНТА: /api/status =====

QJsonObject RobotModel::makeStatusJson() const
{
    QJsonObject obj;

    // Обязательные поля состояния, ожидаемые фронтендом
    obj.insert(QStringLiteral("emergency"), m_emergency);

    // Положение базы (симуляция)
    obj.insert(QStringLiteral("x"), m_x);
    obj.insert(QStringLiteral("y"), m_y);
    obj.insert(QStringLiteral("theta_deg"), m_theta * 180.0 / M_PI);

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
        // Симуляционный/настольный режим
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

// ===== JSON ДЛЯ WEB‑КЛИЕНТА: /api/joint_state =====

QJsonObject RobotModel::makeJointStateJson() const
{
    QJsonObject obj;
    obj.insert(QStringLiteral("turret_deg"), m_turretDeg);
    obj.insert(QStringLiteral("arm_ext"),    m_ext);
    obj.insert(QStringLiteral("gripper"),    m_grip);
    return obj;
}

