#include "motordriver.h"

#include <QFile>
#include <QTextStream>
#include <QThread>
#include <QTimer>
#include <QDebug>
#include <algorithm>

#include <fcntl.h>
#include <unistd.h>

// ===== ЛОКАЛЬНЫЙ ХЕЛПЕР ДЛЯ ЗАПИСИ ТЕКСТА В ФАЙЛ =====
static void writeTextFile(const QString &path, const QString &value)
{
    QFile f(path);
    if (!f.open(QIODevice::WriteOnly | QIODevice::Truncate))
        return;

    QTextStream ts(&f);
    ts << value;
    f.close();
}

// ===== КОНСТРУКТОР / ДЕСТРУКТОР =====
MotorDriver::MotorDriver(QObject *parent)
    : QObject(parent)
    // подставь реальные GPIO, если другие
    , m_leftIn1(17)
    , m_leftIn2(27)
    , m_rightIn1(23)
    , m_rightIn2(24)
    , m_leftFdIn1(-1)
    , m_leftFdIn2(-1)
    , m_rightFdIn1(-1)
    , m_rightFdIn2(-1)
    , m_leftDuty(0)
    , m_rightDuty(0)
    , m_leftDir(MotorDirection::Stop)
    , m_rightDir(MotorDirection::Stop)
    , m_phase(0)
{
    // Экспорт GPIO
    exportGpio(m_leftIn1);
    exportGpio(m_leftIn2);
    exportGpio(m_rightIn1);
    exportGpio(m_rightIn2);

    // Направление – вывод
    setGpioDirection(m_leftIn1, true);
    setGpioDirection(m_leftIn2, true);
    setGpioDirection(m_rightIn1, true);
    setGpioDirection(m_rightIn2, true);

    // Открываем value как файлы
    m_leftFdIn1  = openGpioValue(m_leftIn1);
    m_leftFdIn2  = openGpioValue(m_leftIn2);
    m_rightFdIn1 = openGpioValue(m_rightIn1);
    m_rightFdIn2 = openGpioValue(m_rightIn2);

    // Таймер «квантования» PWM: 1 мс
    connect(&m_pwmTimer, &QTimer::timeout,
            this, &MotorDriver::pwmTick);
    m_pwmTimer.start(1); // 1 ms
}

MotorDriver::~MotorDriver()
{
    if (m_leftFdIn1  >= 0) ::close(m_leftFdIn1);
    if (m_leftFdIn2  >= 0) ::close(m_leftFdIn2);
    if (m_rightFdIn1 >= 0) ::close(m_rightFdIn1);
    if (m_rightFdIn2 >= 0) ::close(m_rightFdIn2);
}

// ===== РАБОТА С SYSFS GPIO =====
int MotorDriver::exportGpio(int gpio)
{
    writeTextFile("/sys/class/gpio/export", QString::number(gpio));
    // Небольшая пауза, чтобы ядро создало gpioX/
    QThread::msleep(5);
    return 0;
}

int MotorDriver::setGpioDirection(int gpio, bool output)
{
    const QString path =
        QString("/sys/class/gpio/gpio%1/direction").arg(gpio);
    writeTextFile(path, output ? "out" : "in");
    return 0;
}

int MotorDriver::openGpioValue(int gpio)
{
    const QString path =
        QString("/sys/class/gpio/gpio%1/value").arg(gpio);
    int fd = ::open(path.toLocal8Bit().constData(), O_WRONLY);
    return fd;
}

void MotorDriver::writeGpio(int fd, bool value)
{
    if (fd < 0)
        return;

    const char c = value ? '1' : '0';
    ::lseek(fd, 0, SEEK_SET);
    ::write(fd, &c, 1);
}

// ===== ПРИМЕНЕНИЕ PWM К ОДНОМУ МОСТУ (ШИРИНА ЧЕРЕЗ ПЕРИОД) =====
void MotorDriver::applyPhaseForMotor(int fdA,
                                     int fdB,
                                     MotorDirection dir,
                                     int duty,
                                     int phase)
{
    // duty: 0..100 — интерпретируем как «уровень команды»
    // phase: счётчик миллисекунд

    if (duty <= 0 || dir == MotorDirection::Stop) {
        writeGpio(fdA, false);
        writeGpio(fdB, false);
        return;
    }

    // Задаём минимальный и максимальный период импульсов (мс)
    // Малый duty → большой период (редкие импульсы)
    // Большой duty → малый период (частые импульсы)
    const int minPeriod = 10;   // 10 мс (≈100 Гц)
    const int maxPeriod = 200;  // 200 мс (5 Гц)

    // dutyNorm в (0,1]
    double dutyNorm = static_cast<double>(duty) / 100.0;
    dutyNorm = std::clamp(dutyNorm, 0.01, 1.0);

    // Период обратно пропорционален duty: чем меньше команда, тем длиннее период
    const double inv = 1.0 / dutyNorm;
    int period = static_cast<int>(
        minPeriod + (maxPeriod - minPeriod) * (inv - 1.0)
        );
    if (period < minPeriod) period = minPeriod;
    if (period > maxPeriod) period = maxPeriod;

    // Счётчик фазы: для каждого мотора мы используем общий phase (мс) по модулю периода
    const int localPhase = period > 0 ? (phase % period) : 0;

    // Доля времени, когда мотор включён (формируем мягкую «скважность» внутри периода)
    const double onFraction = dutyNorm; // можно сделать нелинейной, если надо
    const int onTime = static_cast<int>(period * onFraction);

    const bool on = (localPhase < onTime);
    if (!on) {
        // выключено
        writeGpio(fdA, false);
        writeGpio(fdB, false);
        return;
    }

    // включено в нужном направлении
    switch (dir) {
    case MotorDirection::Forward:
        writeGpio(fdA, true);
        writeGpio(fdB, false);
        break;
    case MotorDirection::Backward:
        writeGpio(fdA, false);
        writeGpio(fdB, true);
        break;
    default:
        writeGpio(fdA, false);
        writeGpio(fdB, false);
        break;
    }
}

// ===== ПУБЛИЧНЫЕ МЕТОДЫ =====
void MotorDriver::setLeftMotor(MotorDirection dir, int speed_percent)
{
    qDebug() << "Left motor dir=" << int(dir) << "duty=" << speed_percent;

    if (speed_percent < 0) speed_percent = 0;
    if (speed_percent > 100) speed_percent = 100;

    m_leftDir.store(dir);
    m_leftDuty.store(speed_percent);
}

void MotorDriver::setRightMotor(MotorDirection dir, int speed_percent)
{
    qDebug() << "Right motor dir=" << int(dir) << "duty=" << speed_percent;

    if (speed_percent < 0) speed_percent = 0;
    if (speed_percent > 100) speed_percent = 100;

    m_rightDir.store(dir);
    m_rightDuty.store(speed_percent);
}



// ===== ТИК PWM =====
void MotorDriver::pwmTick()
{
    // phase — глобальный счётчик миллисекунд
    m_phase++;
    if (m_phase > 1000000)
        m_phase = 0;

    const int leftDuty   = m_leftDuty.load();
    const int rightDuty  = m_rightDuty.load();
    const MotorDirection leftDir  = m_leftDir.load();
    const MotorDirection rightDir = m_rightDir.load();

    applyPhaseForMotor(m_leftFdIn1,  m_leftFdIn2,
                       leftDir, leftDuty, m_phase);
    applyPhaseForMotor(m_rightFdIn1, m_rightFdIn2,
                       rightDir, rightDuty, m_phase);
}




