#include "gamepad_control.h"
#include <QDebug>

GamepadControl::GamepadControl(QObject *parent)
    : QObject(parent)
    , gamepad_(nullptr)
    , lt_value_(0.0)
    , rt_value_(0.0)
    , lb_pressed_(false)
    , rb_pressed_(false)
{
    // Подписываемся на изменение списка подключённых геймпадов
    auto manager = QGamepadManager::instance();
    connect(manager, &QGamepadManager::connectedGamepadsChanged,
            this, &GamepadControl::onConnectedGamepadsChanged);

    onConnectedGamepadsChanged();
}

GamepadControl::~GamepadControl()
{
    delete gamepad_;
    gamepad_ = nullptr;
}

void GamepadControl::attachToFirstGamepad()
{
    auto manager = QGamepadManager::instance();
    const QList<int> ids = manager->connectedGamepads();
    if (ids.isEmpty()) {
        if (gamepad_) {
            delete gamepad_;
            gamepad_ = nullptr;
        }
        return;
    }

    int id = ids.first();
    if (gamepad_ && gamepad_->deviceId() == id) {
        return;
    }

    if (gamepad_) {
        delete gamepad_;
        gamepad_ = nullptr;
    }

    gamepad_ = new QGamepad(id, this);
    qDebug() << "Gamepad connected, id =" << id;
    emit gamepadConnected(id);

    // Подключаем сигналы осей
    connect(gamepad_, &QGamepad::axisLeftXChanged,
            this, &GamepadControl::onAxisLeftXChanged);
    connect(gamepad_, &QGamepad::axisLeftYChanged,
            this, &GamepadControl::onAxisLeftYChanged);
    connect(gamepad_, &QGamepad::axisRightXChanged,
            this, &GamepadControl::onAxisRightXChanged);
    connect(gamepad_, &QGamepad::axisRightYChanged,
            this, &GamepadControl::onAxisRightYChanged);

    // Триггеры и плечи:
    // L2 (LT), R2 (RT) — в Qt Gamepad часто как оси, но могут быть и как кнопки.
    connect(gamepad_, &QGamepad::buttonL2Changed,
            this, &GamepadControl::onButtonL2Changed);
    connect(gamepad_, &QGamepad::buttonR2Changed,
            this, &GamepadControl::onButtonR2Changed);
    connect(gamepad_, &QGamepad::buttonL1Changed,
            this, &GamepadControl::onButtonL1Changed);
    connect(gamepad_, &QGamepad::buttonR1Changed,
            this, &GamepadControl::onButtonR1Changed);
}

void GamepadControl::onConnectedGamepadsChanged()
{
    auto manager = QGamepadManager::instance();
    const QList<int> ids = manager->connectedGamepads();

    // Уведомим об отключении, если не осталось геймпадов
    if (ids.isEmpty()) {
        if (gamepad_) {
            emit gamepadDisconnected(gamepad_->deviceId());
            delete gamepad_;
            gamepad_ = nullptr;
        }
        return;
    }

    attachToFirstGamepad();
}

// ЛЕВЫЙ СТИК: движение шасси
void GamepadControl::onAxisLeftXChanged(double value)
{
    Q_UNUSED(value);
    // По ТЗ левый стик отвечает только за движение ходовой по Y (вперёд/назад),
    // поворот берём с правого стика X. Если захочешь, можно сюда добавить боковой дрейф.
}

void GamepadControl::onAxisLeftYChanged(double value)
{
    // Обычно вниз = +1, поэтому инвертируем знак
    state_.drive_v = -value;
    emitStateChanged();
}

// ПРАВЫЙ СТИК: поворот и удлинение манипулятора
void GamepadControl::onAxisRightXChanged(double value)
{
    // Поворот робота
    state_.drive_w = value;
    emitStateChanged();
}

void GamepadControl::onAxisRightYChanged(double value)
{
    // Удлинение манипулятора
    state_.manip_extend = -value; // вверх = уменьшение, вниз = увеличение (можно инвертировать)
    emitStateChanged();
}

// LT (L2) и LB: управление высотой манипулятора
void GamepadControl::onButtonL2Changed(double value)
{
    // Значение оси LT: обычно 0..1 или -1..1; нормализуем в 0..1
    lt_value_ = value;
    double norm = lt_value_;
    // Простая схема:
    //  - если LT зажат, а LB НЕ зажат -> поднимать
    //  - если LT зажат и LB зажат -> опускать
    if (norm > 0.1) {
        if (!lb_pressed_) {
            state_.manip_height = +norm;
        } else {
            state_.manip_height = -norm;
        }
    } else {
        state_.manip_height = 0.0;
    }
    emitStateChanged();
}

void GamepadControl::onButtonR2Changed(double value)
{
    // RT: аналогично, но для захвата
    rt_value_ = value;
    double norm = rt_value_;

    // Сжатие/разжатие по нажатию:
    //  - RT без RB -> сжать
    //  - RT + RB   -> разжать
    if (norm > 0.1) {
        if (!rb_pressed_) {
            state_.grip_closed = true;
        } else {
            state_.grip_closed = false;
        }
    }
    emitStateChanged();
}

void GamepadControl::onButtonL1Changed(bool pressed)
{
    lb_pressed_ = pressed;
    // Обновим манипулятор по текущему LT
    onButtonL2Changed(lt_value_);
}

void GamepadControl::onButtonR1Changed(bool pressed)
{
    rb_pressed_ = pressed;
    // Обновим захват по текущему RT
    onButtonR2Changed(rt_value_);
}

void GamepadControl::emitStateChanged()
{
    emit stateChanged(state_);
}
