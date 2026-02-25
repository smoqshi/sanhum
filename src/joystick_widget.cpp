#include "joystick_widget.h"
#include <QPainter>
#include <QMouseEvent>
#include <QtMath>

JoystickWidget::JoystickWidget(QWidget *parent)
    : QWidget(parent)
{
    setMinimumSize(150, 150);
}

void JoystickWidget::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event);
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing, true);

    int size = qMin(width(), height());
    int radius = size / 2 - 5;
    QPoint center(width() / 2, height() / 2);

    // окружность
    p.setPen(QPen(Qt::gray, 2));
    p.drawEllipse(center, radius, radius);

    // ручка
    QPoint handle(
        center.x() + static_cast<int>(x_ * radius),
        center.y() - static_cast<int>(y_ * radius));

    p.setBrush(Qt::blue);
    p.setPen(Qt::NoPen);
    p.drawEllipse(handle, size / 10, size / 10);
}

void JoystickWidget::mousePressEvent(QMouseEvent *event)
{
    dragging_ = true;
    updateFromMouse(event->pos());
}

void JoystickWidget::mouseMoveEvent(QMouseEvent *event)
{
    if (!dragging_) return;
    updateFromMouse(event->pos());
}

void JoystickWidget::mouseReleaseEvent(QMouseEvent *event)
{
    Q_UNUSED(event);
    dragging_ = false;
    x_ = 0.0;
    y_ = 0.0;
    emit positionChanged(x_, y_);
    update();
}

void JoystickWidget::updateFromMouse(const QPoint &pos)
{
    int size = qMin(width(), height());
    int radius = size / 2 - 5;
    QPoint center(width() / 2, height() / 2);

    QPoint diff = pos - center;
    double dx = static_cast<double>(diff.x()) / radius;
    double dy = -static_cast<double>(diff.y()) / radius;

    double len = std::sqrt(dx*dx + dy*dy);
    if (len > 1.0) {
        dx /= len;
        dy /= len;
    }

    x_ = dx;
    y_ = dy;
    emit positionChanged(x_, y_);
    update();
}
