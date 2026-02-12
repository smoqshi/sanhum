#!/usr/bin/env python3
import sys
import gpiod

GPIO_IN1 = 17
GPIO_IN2 = 27
GPIO_IN3 = 23
GPIO_IN4 = 24

def set_pins(in1, in2, in3, in4):
    chip = gpiod.Chip("/dev/gpiochip0")
    lines = chip.get_lines([GPIO_IN1, GPIO_IN2, GPIO_IN3, GPIO_IN4])
    lines.request(
        consumer="sanhum_py",
        type=gpiod.LINE_REQ_DIR_OUT,
        default_vals=[0, 0, 0, 0],
    )
    try:
        lines.set_values([in1, in2, in3, in4])
    finally:
        lines.release()
        chip.close()

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
