TEMPLATE = app
TARGET = sanhum_qt
QT += core gui widgets network serialport gamepad

SOURCES += \
    src/main.cpp \
    src/main_window.cpp \
    src/wifi_server.cpp \
    src/gamepad_control.cpp \
    src/robot_client.cpp \
    src/motor_driver.cpp \
    src/esp32_driver.cpp \
    src/arduino_sensors.cpp \
    src/cameras.cpp \
    src/yolo_detector.cpp

HEADERS += \
    include/main_window.h \
    include/wifi_server.h \
    include/gamepad_control.h \
    include/robot_client.h \
    include/motor_driver.h \
    include/esp32_driver.h \
    include/arduino_sensors.h \
    include/cameras.h \
    include/yolo_detector.h

win32 {
    DEFINES += PLATFORM_WINDOWS
} else {
    DEFINES += PLATFORM_LINUX PLATFORM_PI
}
