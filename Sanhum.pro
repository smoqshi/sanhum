QT += core network gui

CONFIG += c++17 console
CONFIG -= app_bundle

TARGET = Sanhum
TEMPLATE = app

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

# Платформо-зависимые библиотеки
win32 {
    # под Windows libgpiod нет – не линкуем
} else {
    # под Linux линкуем libgpiod/libgpiodcxx
    LIBS += -lgpiodcxx -lgpiod
}

DISTFILES += \
    www/index.html \
    www/js/cameras.js \
    www/js/main.js \
    www/js/robotState.js \
    www/js/chassis.js \
    www/js/manipulator.js \
    www/js/uiControls.js \
    www/js/network.js

# Автоматическое копирование папки www рядом с .exe
win32 {
    QMAKE_POST_LINK += xcopy /E /I /Y \"$$PWD\\www\" \"$$OUT_PWD\\www\" & echo.
} else {
    QMAKE_POST_LINK += cp -r \"$$PWD/www\" \"$$OUT_PWD/www\"
}
