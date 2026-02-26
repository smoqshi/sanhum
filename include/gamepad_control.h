#pragma once

#include <QObject>
#include <QTimer>

/**
 * @brief GamepadControl
 *
 * Реализация поддержки геймпада на Windows через XInput.
 * Периодически опрашивает XInput, собирает:
 *  - drive_v, drive_w         (ходовая: левый Y, правый X)
 *  - manip_extend, manip_height
 *  - grip_closed
 *
 * Модель:
 *  - левый стик (Y)       -> drive_v
 *  - правый стик (X)      -> drive_w
 *  - правый стик (Y)      -> manip_extend
 *  - LT (+LB)             -> manip_height
 *  - RT (+RB)             -> grip_closed
 */
class GamepadControl : public QObject
{
    Q_OBJECT
public:
    struct State {
        double drive_v = 0.0;        // -1..1, линейная скорость
        double drive_w = 0.0;        // -1..1, поворот
        double manip_extend = 0.0;   // -1..1, удлинение манипулятора
        double manip_height = 0.0;   // -1..1, высота манипулятора
        bool   grip_closed = false;  // состояние захвата
    };

    explicit GamepadControl(QObject *parent = nullptr);
    ~GamepadControl() override = default;

    State state() const { return state_; }

signals:
    void stateChanged(const GamepadControl::State &state);
    void gamepadConnected(int index);
    void gamepadDisconnected(int index);

private slots:
    void pollGamepad();

private:
    bool updateStateFromXInput();
    void emitStateChanged();

    QTimer poll_timer_;
    State state_;

    bool last_connected_;
    int  connected_index_;

    // Внутренние флаги для комбинаций LT+LB, RT+RB
    double lt_value_;
    double rt_value_;
    bool   lb_pressed_;
    bool   rb_pressed_;
};
