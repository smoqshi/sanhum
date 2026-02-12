#!/usr/bin/env python3
import sys
import gpiod
from gpiod.line import Direction, Value

GPIO_IN1 = 17
GPIO_IN2 = 27
GPIO_IN3 = 23
GPIO_IN4 = 24

CHIP_PATH = "/dev/gpiochip0"


def set_pins(in1, in2, in3, in4):
    # Словарь: номер линии -> стартовое значение
    config = {
        GPIO_IN1: gpiod.LineSettings(
            direction=Direction.OUTPUT,
            output_value=Value.ACTIVE if in1 else Value.INACTIVE,
        ),
        GPIO_IN2: gpiod.LineSettings(
            direction=Direction.OUTPUT,
            output_value=Value.ACTIVE if in2 else Value.INACTIVE,
        ),
        GPIO_IN3: gpiod.LineSettings(
            direction=Direction.OUTPUT,
            output_value=Value.ACTIVE if in3 else Value.INACTIVE,
        ),
        GPIO_IN4: gpiod.LineSettings(
            direction=Direction.OUTPUT,
            output_value=Value.ACTIVE if in4 else Value.INACTIVE,
        ),
    }

    # Открываем чип, запрашиваем линии, удерживаем их пока объект жив
    with gpiod.request_lines(
        CHIP_PATH,
        consumer="sanhum_py",
        config=config,
    ) as request:
        # Можно ещё раз явно задать значения (на случай, если хочешь обновлять)
        values = {
            GPIO_IN1: Value.ACTIVE if in1 else Value.INACTIVE,
            GPIO_IN2: Value.ACTIVE if in2 else Value.INACTIVE,
            GPIO_IN3: Value.ACTIVE if in3 else Value.INACTIVE,
            GPIO_IN4: Value.ACTIVE if in4 else Value.INACTIVE,
        }
        request.set_values(values)


def main():
    if len(sys.argv) != 5:
        print("Usage: motor_control.py left_dir right_dir left_duty right_duty")
        sys.exit(1)

    left_dir = int(sys.argv[1])   # -1,0,1
    right_dir = int(sys.argv[2])
    left_duty = int(sys.argv[3])
    right_duty = int(sys.argv[4])

    left_on = left_duty > 0
    right_on = right_duty > 0

    in1 = int(left_on and left_dir > 0)
    in2 = int(left_on and left_dir < 0)
    in3 = int(right_on and right_dir > 0)
    in4 = int(right_on and right_dir < 0)

    set_pins(in1, in2, in3, in4)


if __name__ == "__main__":
    main()

