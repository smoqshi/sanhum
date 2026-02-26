#include "joystick_widget.h"
#include <QPainter>
#include <QMouseEvent>
#include <QtMath>

JoystickWidget::JoystickWidget(QWidget *parent)
    : QWidget(parent)
{
    setMinimumSize(150, 150);
}

void JoystickWidget::setAxes(double x, double y)
{
    x_ = qBound(-1.0, x, 1.0);
    y_ = qBound(-1.0, y, 1.0);
    update();
}

void JoystickWidget::setLabel(const QString &text)
{
    label_ = text;
    update();
}

void JoystickWidget::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event);
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing, true);

    int w = width();
    int h = height();

    // Отделим место под подпись (если есть)
    int textHeight = 0;
    if (!label_.isEmpty()) {
        QFontMetrics fm(p.font());
        textHeight = fm.height() + 4;
    }

    int size = qMin(w, h - textHeight);
    int radius = size / 2 - 5;
    QPoint center(w / 2, (h - textHeight) / 2);

    // Окружность
    p.setPen(QPen(Qt::gray, 2));
    p.setBrush(Qt::NoBrush);
    p.drawEllipse(center, radius, radius);

    // Ручка
    QPoint handle(
        center.x() + static_cast<int>(x_ * radius),
        center.y() - static_cast<int>(y_ * radius));

    p.setBrush(Qt::blue);
    p.setPen(Qt::NoPen);
    p.drawEllipse(handle, size / 10, size / 10);

    // Подпись
    if (!label_.isEmpty()) {
        p.setPen(Qt::white);
        QRect textRect(0, h - textHeight, w, textHeight);
        p.drawText(textRect, Qt::AlignCenter, label_);
    }
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
    int w = width();
    int h = height();

    int textHeight = 0;
    if (!label_.isEmpty()) {
        QFontMetrics fm(font());
        textHeight = fm.height() + 4;
    }

    int size = qMin(w, h - textHeight);
    int radius = size / 2 - 5;
    QPoint center(w / 2, (h - textHeight) / 2);

    QPoint diff = pos - center;
    double dx = static_cast<double>(diff.x()) / radius;
    double dy = -static_cast<double>(diff.y()) / radius;

    double len = std::sqrt(dx * dx + dy * dy);
    if (len > 1.0) {
        dx /= len;
        dy /= len;
    }

    x_ = dx;
    y_ = dy;

    emit positionChanged(x_, y_);
    update();
}
