QT       += core gui network widgets concurrent

CONFIG   += c++17 console
CONFIG   -= app_bundle

TARGET    = Sanhum
TEMPLATE  = app

SOURCES  += \
    src/main.cpp \
    src/armkinematics.cpp \
    src/httpserver.cpp \
    src/motordriver.cpp \
    src/robotmodel.cpp

HEADERS  += \
    src/armkinematics.h \
    src/httpserver.h \
    src/motordriver.h \
    src/robotmodel.h

RESOURCES += resources.qrc

# КРОССПЛАТФОРМЕННОСТЬ (ИСПРАВЛЕНИЕ)
win32 {
    LIBS += -lws2_32
    DEFINES += _WIN32_WINNT=0x0601
}

unix:!macx {
    LIBS += -lpthread
    # Raspberry Pi ARM
    contains(QT_ARCH, arm.*): {
        QMAKE_CXXFLAGS += -march=armv8-a -mfpu=neon-fp-armv8
    }
}

macx {
    LIBS += -framework IOKit -framework CoreFoundation
}

# ОПТИМИЗАЦИЯ + ОТЛАДКА
QMAKE_CXXFLAGS += -O2 -Wall -Wextra
QMAKE_CXXFLAGS_DEBUG += -g -O0

# Кросс-компиляция
CONFIG(raspberrypi) {
    QMAKE_CXXFLAGS += -DRASPBERRY_PI
}
