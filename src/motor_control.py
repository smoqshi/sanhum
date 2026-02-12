#!/usr/bin/env python3
import sys
import time
import gpiod
from gpiod.line import Direction, Value

# D0..D3 согласно даташиту драйвера
GPIO_D0 = 17  # MOTOR 1 input D0
GPIO_D1 = 27  # MOTOR 1 input D1
GPIO_D2 = 23  # MOTOR 2 input D2
GPIO_D3 = 24  # MOTOR 2 input D3

CHIP_PATH = "/dev/gpiochip0"

PWM_FREQ_HZ = 100.0          # частота ШИМ
UPDATE_WINDOW = 0.2          # сколько секунд крутить с заданными параметрами


def drive_one_motor(dir_, duty, pin_fwd, pin_rev, values, period, req):
    """
    dir_: -1 (reverse), 0 (stop), 1 (forward)
    duty: 0..100 (проценты), отрицательные можно использовать для тормоза
    pin_fwd, pin_rev: номера линей для данного мотора
    values: общий словарь значений для начала цикла
    period: период ШИМ
    req: запрос линий gpiod
    """

    duty = max(-100, min(100, duty))

    # Brake: договоримся, что duty < 0 => тормоз (оба входа = 1)
    if duty < 0:
        values[pin_fwd] = Value.ACTIVE
        values[pin_rev] = Value.ACTIVE
        return 0.0, 0.0  # без ШИМ, просто удерживаем 1/1

    if duty == 0 or dir_ == 0:
        # Stop: оба входа 0
        values[pin_fwd] = Value.INACTIVE
        values[pin_rev] = Value.INACTIVE
        return 0.0, 0.0

    duty = max(0, min(100, duty))
    on_time = period * (duty / 100.0)

    # Forward: PWM на pin_fwd, pin_rev = 0
    if dir_ > 0:
        values[pin_fwd] = Value.ACTIVE
        values[pin_rev] = Value.INACTIVE
        return on_time, pin_fwd

    # Reverse: PWM на pin_rev, pin_fwd = 0
    else:
        values[pin_fwd] = Value.INACTIVE
        values[pin_rev] = Value.ACTIVE
        return on_time, pin_rev


def apply_drive(left_dir, right_dir, left_duty, right_duty):
    period = 1.0 / PWM_FREQ_HZ

    config = {
        GPIO_D0: gpiod.LineSettings(direction=Direction.OUTPUT,
                                    output_value=Value.INACTIVE),
        GPIO_D1: gpiod.LineSettings(direction=Direction.OUTPUT,
                                    output_value=Value.INACTIVE),
        GPIO_D2: gpiod.LineSettings(direction=Direction.OUTPUT,
                                    output_value=Value.INACTIVE),
        GPIO_D3: gpiod.LineSettings(direction=Direction.OUTPUT,
                                    output_value=Value.INACTIVE),
    }

    with gpiod.request_lines(CHIP_PATH, consumer="sanhum_py", config=config) as req:
        start = time.time()
        while time.time() - start < UPDATE_WINDOW:
            values = {}

            # Настраиваем начальные значения на начало периода
            left_on_time, left_pwm_pin = drive_one_motor(
                left_dir, left_duty, GPIO_D0, GPIO_D1, values, period, req
            )
            right_on_time, right_pwm_pin = drive_one_motor(
                right_dir, right_duty, GPIO_D2, GPIO_D3, values, period, req
            )

            req.set_values(values)

            max_on = max(left_on_time, right_on_time)
            if max_on <= 0.0:
                # оба мотора либо стоп, либо тормоз — просто держим состояние
                time.sleep(period)
                continue

            if max_on >= period:
                # фактически 100% — держим линию постоянно активной
                time.sleep(period)
                continue

            # Фаза "ON"
            time.sleep(max_on)

            # Фаза "OFF" для тех линий, которые были в PWM
            off_values = {}
            if 0.0 < left_on_time < period:
                off_values[left_pwm_pin] = Value.INACTIVE
            if 0.0 < right_on_time < period:
                off_values[right_pwm_pin] = Value.INACTIVE

            if off_values:
                req.set_values(off_values)

            time.sleep(period - max_on)


def main():
    if len(sys.argv) != 5:
        print("Usage: motor_control.py left_dir right_dir left_duty right_duty")
        sys.exit(1)

    left_dir = int(sys.argv[1])    # -1,0,1
    right_dir = int(sys.argv[2])   # -1,0,1
    left_duty = int(sys.argv[3])   # 0..100, <0 -> тормоз
    right_duty = int(sys.argv[4])

    apply_drive(left_dir, right_dir, left_duty, right_duty)


if __name__ == "__main__":
    main()

