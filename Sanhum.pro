QT       += core gui network
greaterThan(QT_MAJOR_VERSION, 5): QT += widgets

TARGET = Sanhum
TEMPLATE = app

CONFIG += c++17
CONFIG += release

SOURCES += \
    src/main.cpp \
    src/httpserver.cpp \
    src/robotmodel.cpp \
    src/motordriver.cpp \
    src/armkinematics.cpp

HEADERS += \
    src/httpserver.h \
    src/robotmodel.h \
    src/motordriver.h \
    src/armkinematics.h

RESOURCES += resources.qrc

DISTFILES += \
    www/index.html \
    www/js/robotState.js \
    www/js/network.js \
    www/js/chassis.js \
    www/js/manipulator.js \
    www/js/uiControls.js \
    www/js/main.js

win32 {
    QMAKE_POST_LINK += xcopy /E /I /Y \"$$PWD\\www\" \"$$OUT_PWD\\www\" & echo.
} else {
    # На Linux / Raspberry Pi собираем в исходной директории,
    # папка www уже лежит рядом с бинарём, лишнее копирование не нужно.
}
