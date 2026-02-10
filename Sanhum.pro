QT       += core network
CONFIG   += console c++17
CONFIG   -= app_bundle

# libgpiod для Raspberry Pi 5
LIBS += -lgpiodcxx -lgpiod

TEMPLATE = app
TARGET   = Sanhum

SOURCES += \
    src/armkinematics.cpp \
    src/httpserver.cpp \
    src/main.cpp \
    src/motordriver.cpp \
    src/robotmodel.cpp

HEADERS += \
    src/armkinematics.h \
    src/httpserver.h \
    src/motordriver.h \
    src/robotmodel.h

DISTFILES += \
    www/index.html \
    www/js/cameras.js \
    www/js/main.js \
    www/js/robotState.js \
    www/js/chassis.js \
    www/js/manipulator.js \
    www/js/uiControls.js \
    www/js/network.js

