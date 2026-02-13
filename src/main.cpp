#include <QCoreApplication>
#include <QTimer>
#include <QProcess>
#include <QDebug>
#include <QDir>

#include "robotmodel.h"
#include "httpserver.h"

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

    // Считаем, что бинарь лежит в корне проекта (там же, где и папка src)
    // Например: /home/vector/Desktop/sanhum/sanhum_binary
    // Тогда motor_control.py находится по пути: ./src/motor_control.py
    QDir appDir(QCoreApplication::applicationDirPath());
    QString motorScriptPath = appDir.filePath("src/motor_control.py");

    qInfo().noquote() << "motor_control.py path:" << motorScriptPath;

    QProcess *motorProcess = new QProcess(&app);

    QObject::connect(motorProcess, &QProcess::readyReadStandardOutput, [motorProcess]() {
        QByteArray data = motorProcess->readAllStandardOutput();
        if (!data.isEmpty())
            qInfo().noquote() << "[motor_control.py stdout]" << data.trimmed();
    });
    QObject::connect(motorProcess, &QProcess::readyReadStandardError, [motorProcess]() {
        QByteArray data = motorProcess->readAllStandardError();
        if (!data.isEmpty())
            qWarning().noquote() << "[motor_control.py stderr]" << data.trimmed();
    });

    QString program = "/usr/bin/python3";
    QStringList arguments;
    arguments << motorScriptPath;

    motorProcess->start(program, arguments);

    if (!motorProcess->waitForStarted(3000)) {
        qFatal("Failed to start motor_control.py at path %s",
               qPrintable(motorScriptPath));
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

