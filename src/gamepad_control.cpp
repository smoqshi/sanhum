#include "gamepad_control.h"

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <Xinput.h>
#pragma comment(lib, "XInput.lib")
#endif

#include <QtMath>
#include <QDebug>

/*
 * Вариант с XInput основан на типичных учебных примерах:
 * опрос XInputGetState для индексов 0..3, нормализация
 * значений стиков и триггеров, учёт dead zone.[web:85][web:87]
 */

namespace
{
#ifdef _WIN32
    double normalizeThumb(SHORT v, SHORT deadzone, SHORT maxValue)
    {
        if (qAbs(v) < deadzone)
            return 0.0;
        double val = static_cast<double>(v);
        if (val > 0)
            return (val - deadzone) / (maxValue - deadzone);
        else
            return (val + deadzone) / (maxValue - deadzone);
    }
#endif
}

GamepadControl::GamepadControl(QObject *parent)
    : QObject(parent)
    , last_connected_(false)
    , connected_index_(-1)
    , lt_value_(0.0)
    , rt_value_(0.0)
    , lb_pressed_(false)
    , rb_pressed_(false)
{
    poll_timer_.setInterval(16); // ~60 Гц
    connect(&poll_timer_, &QTimer::timeout, this, &GamepadControl::pollGamepad);
    poll_timer_.start();
}

void GamepadControl::pollGamepad()
{
    bool connectedNow = updateStateFromXInput();

    if (connectedNow != last_connected_) {
        if (connectedNow) {
            qDebug() << "Gamepad connected at index" << connected_index_;
            emit gamepadConnected(connected_index_);
        } else {
            qDebug() << "Gamepad disconnected";
            emit gamepadDisconnected(connected_index_);
            connected_index_ = -1;
        }
        last_connected_ = connectedNow;
    }

    if (connectedNow) {
        emitStateChanged();
    }
}

bool GamepadControl::updateStateFromXInput()
{
#ifndef _WIN32
    return false;
#else
    XINPUT_STATE state;
    ZeroMemory(&state, sizeof(XINPUT_STATE));

    bool found = false;
    int foundIndex = -1;

    // Ищем первый подключённый геймпад
    for (DWORD i = 0; i < XUSER_MAX_COUNT; ++i) {
        if (XInputGetState(i, &state) == ERROR_SUCCESS) {
            found = true;
            foundIndex = static_cast<int>(i);
            break;
        }
    }

    if (!found) {
        // Обнуляем состояние
        state_.drive_v = 0.0;
        state_.drive_w = 0.0;
        state_.manip_extend = 0.0;
        state_.manip_height = 0.0;
        state_.grip_closed = false;
        return false;
    }

    connected_index_ = foundIndex;

    const XINPUT_GAMEPAD &pad = state.Gamepad;

    // Параметры dead zone для стиков (как в документации XInput)
    const SHORT DEADZONE_L = XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE;
    const SHORT DEADZONE_R = XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE;
    const SHORT MAX_THUMB  = 32767;

    double lx = normalizeThumb(pad.sThumbLX, DEADZONE_L, MAX_THUMB);
    double ly = normalizeThumb(pad.sThumbLY, DEADZONE_L, MAX_THUMB);
    double rx = normalizeThumb(pad.sThumbRX, DEADZONE_R, MAX_THUMB);
    double ry = normalizeThumb(pad.sThumbRY, DEADZONE_R, MAX_THUMB);

    // Триггеры: 0..255
    double lt = static_cast<double>(pad.bLeftTrigger) / 255.0;
    double rt = static_cast<double>(pad.bRightTrigger) / 255.0;

    bool lb = (pad.wButtons & XINPUT_GAMEPAD_LEFT_SHOULDER) != 0;
    bool rb = (pad.wButtons & XINPUT_GAMEPAD_RIGHT_SHOULDER) != 0;

    // Левый стик: движение ходовой
    state_.drive_v = -ly;  // вверх = вперёд
    // Правый стик: поворот
    state_.drive_w = rx;
    // Правый стик Y: удлинение манипулятора
    state_.manip_extend = -ry;

    // LT + LB: высота манипулятора
    lt_value_ = lt;
    lb_pressed_ = lb;
    if (lt_value_ > 0.1) {
        if (!lb_pressed_) {
            state_.manip_height = +lt_value_;
        } else {
            state_.manip_height = -lt_value_;
        }
    } else {
        state_.manip_height = 0.0;
    }

    // RT + RB: захват
    rt_value_ = rt;
    rb_pressed_ = rb;
    if (rt_value_ > 0.1) {
        if (!rb_pressed_) {
            state_.grip_closed = true;
        } else {
            state_.grip_closed = false;
        }
    }

    return true;
#endif
}

void GamepadControl::emitStateChanged()
{
    emit stateChanged(state_);
}
