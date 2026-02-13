#include <QCoreApplication>
#include <QTimer>
#include <QProcess>
#include <QDebug>

#include "robotmodel.h"
#include "httpserver.h"

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

    // Запуск демона управления моторами (motor_control.py)
    // Предполагается, что проект лежит в /home/vector/sanhum
    // При необходимости скорректируй путь ниже.
    QProcess *motorProcess = new QProcess(&app);

    // Лог ошибок от Python-скрипта в stdout/stderr приложения
    QObject::connect(motorProcess, &QProcess::readyReadStandardOutput, [motorProcess]() {
        QByteArray data = motorProcess->readAllStandardOutput();
        qInfo().noquote() << "[motor_control.py stdout]" << data.trimmed();
    });
    QObject::connect(motorProcess, &QProcess::readyReadStandardError, [motorProcess]() {
        QByteArray data = motorProcess->readAllStandardError();
        qWarning().noquote() << "[motor_control.py stderr]" << data.trimmed();
    });

    // Автоперезапуск, если скрипт упал
    QObject::connect(motorProcess,
                     QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished),
                     [&app, motorProcess](int code, QProcess::ExitStatus status) {
        qWarning() << "motor_control.py finished with code" << code << "status" << status;
        // Можно сделать автоперезапуск, если нужно
        motorProcess->start();
    });

    // Настройка и запуск процесса
    QString program = "/usr/bin/python3";
    QStringList arguments;
    arguments << "/home/vector/sanhum/src/motor_control.py";

    motorProcess->start(program, arguments);

    if (!motorProcess->waitForStarted(3000)) {
        qFatal("Failed to start motor_control.py");
    }

    RobotModel model;
    HttpServer server(&model);
    if (!server.listen(8080)) {
        qFatal("Failed to listen on port 8080");
    }

    QTimer timer;
    QObject::connect(&timer, &QTimer::timeout, [&model]() {
        constexpr double dt = 0.02;
        model.step(dt);
    });
    timer.start(20);

    return app.exec();
}
