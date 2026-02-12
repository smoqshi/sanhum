#!/usr/bin/env python3
import socket
import struct
import time
import threading
from typing import Tuple

import gpiod
from gpiod.line import Direction, Value

try:
    import serial  # для ESP32, если нет – манипулятор просто не будет активен
except ImportError:
    serial = None

# -------------------------------
# Настройки
# -------------------------------

# GPIO для колес (D0..D3 по таблице драйвера)
GPIO_D0 = 17  # MOTOR 1 D0
GPIO_D1 = 27  # MOTOR 1 D1
GPIO_D2 = 23  # MOTOR 2 D2
GPIO_D3 = 24  # MOTOR 2 D3

CHIP_PATH = "/dev/gpiochip0"

PWM_FREQ_HZ = 100.0           # частота ШИМ для колес
PERIOD = 1.0 / PWM_FREQ_HZ
UPDATE_HZ = 100.0             # частота опроса команд / обновления моторов
UPDATE_DT = 1.0 / UPDATE_HZ

# UDP сервер для команд от Qt
UDP_HOST = "127.0.0.1"
UDP_PORT = 5005

# Протокол колес:
# 5 целых (int8): left_dir, right_dir, left_duty, right_duty, brake
#   dir: -1,0,1
#   duty: 0..100
#   brake: 0/1 (1 = принудительный тормоз)
MOTOR_PKT_FMT = "bbbbb"  # 5 * int8

# Протокол манипулятора:
# пока сделаем очень просто:
#   1 байт: командный код
#   N байт: параметры (зависит от команды)
# Код 1: установить положение звена (joint), формат:
#   1 (cmd) | joint_id (uint8) | value (int16, little endian)
# Это можно будет адаптировать под прошивку ESP32.

# -------------------------------
# Глобальное состояние команд
# -------------------------------

class MotorCommand:
    __slots__ = ("left_dir", "right_dir", "left_duty", "right_duty", "brake")

    def __init__(self):
        self.left_dir = 0
        self.right_dir = 0
        self.left_duty = 0
        self.right_duty = 0
        self.brake = 0


motor_cmd = MotorCommand()
motor_lock = threading.Lock()

# Для манипулятора можно хранить последний пакет целиком или уже распарсенные команды.
# Для простоты будем просто сразу пересылать команды на ESP32 по мере прихода.

# -------------------------------
# GPIO для колес
# -------------------------------

def drive_one_motor(dir_, duty, pin0, pin1, values):
    """
    Реализация таблицы:
      Forward: (Speed regulation) -> PWM на D0/D2, второй вход 0
      Reverse: (Speed regulation) -> PWM на D1/D3, второй вход 0
      Stop: 0/0
      Brake: 1/1

    duty >= 0: скорость, 0..100
    brake = обрабатывается выше, здесь предполагаем, что если brake активен,
    вызывающий код сам выставил duty<0 и мы вернём (0,0).
    """
    duty = max(0, min(100, duty))

    if duty == 0 or dir_ == 0:
        values[pin0] = Value.INACTIVE
        values[pin1] = Value.INACTIVE
        return 0.0, None  # нет PWM

    on_time = PERIOD * (duty / 100.0)

    if dir_ > 0:
        # Forward: PWM на pin0, pin1 = 0
        values[pin0] = Value.ACTIVE
        values[pin1] = Value.INACTIVE
        pwm_pin = pin0
    else:
        # Reverse: PWM на pin1, pin0 = 0
        values[pin0] = Value.INACTIVE
        values[pin1] = Value.ACTIVE
        pwm_pin = pin1

    return on_time, pwm_pin


def motor_control_loop():
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
        last_time = time.time()
        while True:
            now = time.time()
            if now - last_time < UPDATE_DT:
                time.sleep(UPDATE_DT - (now - last_time))
            last_time = time.time()

            with motor_lock:
                left_dir = motor_cmd.left_dir
                right_dir = motor_cmd.right_dir
                left_duty = motor_cmd.left_duty
                right_duty = motor_cmd.right_duty
                brake = motor_cmd.brake

            values = {}

            # Экстренный тормоз: оба входа мотора = 1
            if brake:
                values[GPIO_D0] = Value.ACTIVE
                values[GPIO_D1] = Value.ACTIVE
                values[GPIO_D2] = Value.ACTIVE
                values[GPIO_D3] = Value.ACTIVE
                req.set_values(values)
                # держим тормоз на всём периоде
                time.sleep(PERIOD)
                continue

            # Обычное управление
            left_on, left_pwm_pin = drive_one_motor(left_dir, left_duty,
                                                    GPIO_D0, GPIO_D1, values)
            right_on, right_pwm_pin = drive_one_motor(right_dir, right_duty,
                                                      GPIO_D2, GPIO_D3, values)

            req.set_values(values)

            max_on = max(left_on, right_on)
            if max_on <= 0.0:
                # стоп / без PWM
                time.sleep(PERIOD)
                continue

            if max_on >= PERIOD:
                # фактически 100% заполнение
                time.sleep(PERIOD)
                continue

            # фаза ON
            time.sleep(max_on)

            # фаза OFF только для тех линий, где был PWM
            off_values = {}
            if left_pwm_pin is not None:
                off_values[left_pwm_pin] = Value.INACTIVE
            if right_pwm_pin is not None:
                off_values[right_pwm_pin] = Value.INACTIVE
            if off_values:
                req.set_values(off_values)

            time.sleep(PERIOD - max_on)


# -------------------------------
# Работа с ESP32 для манипулятора
# -------------------------------

def open_esp32_serial(port="/dev/ttyUSB0", baudrate=115200):
    if serial is None:
        return None
    try:
        return serial.Serial(port=port, baudrate=baudrate, timeout=0.1)
    except Exception:
        return None


def handle_manipulator_packet(data: bytes, ser):
    """
    Очень простой протокол:
      cmd = data[0]
      если cmd == 1:
        joint_id = data[1]
        value = int16 little-endian (data[2:4])
        отправляем строку вида: "J {joint_id} {value}\n"
    Всё это можно адаптировать под прошивку ESP32.
    """
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
    # здесь можно добавить другие команды (gripper, режимы и т.п.)


# -------------------------------
# UDP сервер
# -------------------------------

def udp_server_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_HOST, UDP_PORT))

    ser = open_esp32_serial()

    while True:
        data, addr = sock.recvfrom(64)
        if not data:
            continue

        # Первый байт: тип пакета
        pkt_type = data[0]

        # Тип 1: команда колес
        if pkt_type == 1:
            # ожидаем 1 + 5 байт payload (по MOTOR_PKT_FMT)
            if len(data) < 1 + struct.calcsize(MOTOR_PKT_FMT):
                continue
            _, left_dir, right_dir, left_duty, right_duty, brake = struct.unpack(
                "B" + MOTOR_PKT_FMT, data[:1 + struct.calcsize(MOTOR_PKT_FMT)]
            )
            with motor_lock:
                motor_cmd.left_dir = int(left_dir)
                motor_cmd.right_dir = int(right_dir)
                motor_cmd.left_duty = int(left_duty)
                motor_cmd.right_duty = int(right_duty)
                motor_cmd.brake = int(brake)

        # Тип 2: команда манипулятора (прозрачно пересылаем на ESP32)
        elif pkt_type == 2:
            handle_manipulator_packet(data[1:], ser)


# -------------------------------
# entry point
# -------------------------------

def main():
    motor_thread = threading.Thread(target=motor_control_loop, daemon=True)
    motor_thread.start()

    udp_server_loop()


if __name__ == "__main__":
    main()

