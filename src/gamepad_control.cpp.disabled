#pragma once

#include <QObject>
#include <QGamepad>
#include <QGamepadManager>

/**
 * @brief GamepadControl
 *
 * Класс-обёртка над QGamepad/QGamepadManager, который:
 *  - выбирает первый доступный геймпад;
 *  - конвертирует его оси/кнопки в абстрактное состояние управления:
 *      * drive_v, drive_w         (движение гусеничного шасси)
 *      * manip_extend, manip_height (манипулятор)
 *      * grip_closed              (состояние захвата)
 *  - дублирует события в виде сигналов, чтобы MainWindow мог их слушать.
 */
class GamepadControl : public QObject
{
    Q_OBJECT
public:
    struct State {
        double drive_v = 0.0;        // -1..1, линейная скорость (левый стик Y)
        double drive_w = 0.0;        // -1..1, поворот (правый стик X)
        double manip_extend = 0.0;   // -1..1, удлинение (правый стик Y)
        double manip_height = 0.0;   // -1..1, высота (LT / LT+LB)
        bool   grip_closed = false;  // RT/RT+RB
    };

    explicit GamepadControl(QObject *parent = nullptr);
    ~GamepadControl() override;

    State state() const { return state_; }

signals:
    void stateChanged(const GamepadControl::State &state);
    void gamepadConnected(int deviceId);
    void gamepadDisconnected(int deviceId);

private slots:
    void onConnectedGamepadsChanged();
    void onAxisLeftXChanged(double value);
    void onAxisLeftYChanged(double value);
    void onAxisRightXChanged(double value);
    void onAxisRightYChanged(double value);
    void onButtonL2Changed(double value);
    void onButtonR2Changed(double value);
    void onButtonL1Changed(bool pressed);
    void onButtonR1Changed(bool pressed);

private:
    void attachToFirstGamepad();
    void emitStateChanged();

    QGamepad *gamepad_;
    State state_;

    // внутренние флаги для комбинаций LT+LB, RT+RB
    double lt_value_;
    double rt_value_;
    bool lb_pressed_;
    bool rb_pressed_;
};
