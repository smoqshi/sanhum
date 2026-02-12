#include <QApplication>
#include <QCoreApplication>
#include <QFile>
#include <QProcess>
#include <QDebug>

#include "mainwindow.h"
#include "robotmodel.h"
#include "httpserver.h"

static void ensureMotorDaemonRunning()
{
    QString baseDir = QCoreApplication::applicationDirPath();
    QString script  = baseDir + "/src/motor_control.py";

    if (!QFile::exists(script)) {
        qWarning() << "motor_control.py not found at" << script;
        return;
    }

    QString program = "python3";
    QStringList args;
    args << script;

    qint64 pid = 0;
    bool ok = QProcess::startDetached(program, args, baseDir, &pid);
    if (!ok) {
        qWarning() << "Failed to start motor_control.py";
    } else {
        qDebug() << "motor_control.py started, pid =" << pid;
    }
}

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);

    // автозапуск демона управления моторами/манипулятором
    ensureMotorDaemonRunning();

    RobotModel model;
    HttpServer server(&model);

    MainWindow w(&model);
    w.show();

    return app.exec();
}
