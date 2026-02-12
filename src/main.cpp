#include <QCoreApplication>
#include <QTimer>

#include "robotmodel.h"
#include "httpserver.h"

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

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
