#!/usr/bin/env python3
import socket
import struct
import time
import threading
from typing import Optional

import gpiod
from gpiod.line import Direction, Value

try:
    import serial
except ImportError:
    serial = None

GPIO_D0 = 17  # MOTOR 1 D0
GPIO_D1 = 27  # MOTOR 1 D1
GPIO_D2 = 23  # MOTOR 2 D2
GPIO_D3 = 24  # MOTOR 2 D3

CHIP_PATH = "/dev/gpiochip0"

PWM_FREQ_HZ = 100.0
PERIOD = 1.0 / PWM_FREQ_HZ

UPDATE_HZ = 100.0
UPDATE_DT = 1.0 / UPDATE_HZ

UDP_HOST = "127.0.0.1"
UDP_PORT = 5005

# 1 байт тип, дальше 5 байт int8:
# left_dir, right_dir, left_duty, right_duty, brake_toggle
MOTOR_PKT_FMT = "bbbbb"


class MotorCommand:
    __slots__ = ("left_dir", "right_dir", "left_duty", "right_duty", "brake_toggle")

    def __init__(self):
        self.left_dir = 0
        self.right_dir = 0
        self.left_duty = 0
        self.right_duty = 0
        self.brake_toggle = 0


motor_cmd = MotorCommand()
motor_lock = threading.Lock()

# внутренний флаг стояночного тормоза
parking_brake = False


def drive_one_motor(dir_, duty, pin0, pin1, values):
    duty = max(0, min(100, duty))
    if duty == 0 or dir_ == 0:
        values[pin0] = Value.INACTIVE
        values[pin1] = Value.INACTIVE
        return 0.0, None

    on_time = PERIOD * (duty / 100.0)

    if dir_ > 0:
        values[pin0] = Value.ACTIVE
        values[pin1] = Value.INACTIVE
        pwm_pin = pin0
    else:
        values[pin0] = Value.INACTIVE
        values[pin1] = Value.ACTIVE
        pwm_pin = pin1

    return on_time, pwm_pin


def motor_control_loop():
    global parking_brake

    config = {
        GPIO_D0: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
        GPIO_D1: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
        GPIO_D2: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
        GPIO_D3: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
    }

    with gpiod.request_lines(CHIP_PATH, consumer="sanhum_py", config=config) as req:
        last_time = time.time()

        while True:
            now = time.time()
            dt = now - last_time
            if dt < UPDATE_DT:
                time.sleep(UPDATE_DT - dt)
            last_time = time.time()

            with motor_lock:
                left_dir = motor_cmd.left_dir
                right_dir = motor_cmd.right_dir
                left_duty = motor_cmd.left_duty
                right_duty = motor_cmd.right_duty
                brake_toggle = motor_cmd.brake_toggle
                motor_cmd.brake_toggle = 0  # сбрасываем одноразовый флаг

            # Обработка стояночного тормоза (toggle по кнопке B)
            if brake_toggle:
                parking_brake = not parking_brake

            values = {}

            if parking_brake:
                # Стояночный тормоз: 1 на все пины
                values[GPIO_D0] = Value.ACTIVE
                values[GPIO_D1] = Value.ACTIVE
                values[GPIO_D2] = Value.ACTIVE
                values[GPIO_D3] = Value.ACTIVE
                req.set_values(values)
                time.sleep(PERIOD)
                continue

            # Обычное управление без «авто-рекуперации»
            left_on, left_pwm_pin = drive_one_motor(
                left_dir, left_duty, GPIO_D0, GPIO_D1, values
            )
            right_on, right_pwm_pin = drive_one_motor(
                right_dir, right_duty, GPIO_D2, GPIO_D3, values
            )

            req.set_values(values)

            max_on = max(left_on, right_on)

            if max_on <= 0.0:
                time.sleep(PERIOD)
                continue

            if max_on >= PERIOD:
                time.sleep(PERIOD)
                continue

            time.sleep(max_on)

            off_values = {}
            if left_pwm_pin is not None:
                off_values[left_pwm_pin] = Value.INACTIVE
            if right_pwm_pin is not None:
                off_values[right_pwm_pin] = Value.INACTIVE

            if off_values:
                req.set_values(off_values)

            time.sleep(PERIOD - max_on)


def open_esp32_serial(port="/dev/ttyUSB0", baudrate=115200) -> Optional["serial.Serial"]:
    if serial is None:
        return None
    try:
        return serial.Serial(port=port, baudrate=baudrate, timeout=0.1)
    except Exception:
        return None


def handle_manipulator_packet(data: bytes, ser: Optional["serial.Serial"]) -> None:
    if ser is None:
        return
    if len(data) < 1:
        return

    cmd = data[0]

    if cmd == 1 and len(data) >= 4:
        joint_id = data[1]
        value = int.from_bytes(data[2:4], byteorder="little", signed=True)
        line = f"J {joint_id} {value}\n"
        try:
            ser.write(line.encode("ascii"))
        except Exception:
            pass


def udp_server_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_HOST, UDP_PORT))

    ser = open_esp32_serial()

    while True:
        data, addr = sock.recvfrom(64)
        if not data:
            continue

        pkt_type = data[0]

        if pkt_type == 1:
            need = 1 + struct.calcsize(MOTOR_PKT_FMT)
            if len(data) < need:
                continue

            _, left_dir, right_dir, left_duty, right_duty, brake_toggle = struct.unpack(
                "B" + MOTOR_PKT_FMT, data[:need]
            )

            with motor_lock:
                motor_cmd.left_dir = int(left_dir)
                motor_cmd.right_dir = int(right_dir)
                motor_cmd.left_duty = int(left_duty)
                motor_cmd.right_duty = int(right_duty)
                # brake_toggle трактуем как «была нажата B в этом пакете»
                motor_cmd.brake_toggle = 1 if brake_toggle else 0

        elif pkt_type == 2:
            handle_manipulator_packet(data[1:], ser)


def main():
    motor_thread = threading.Thread(target=motor_control_loop, daemon=True)
    motor_thread.start()

    udp_server_loop()


if __name__ == "__main__":
    main()
