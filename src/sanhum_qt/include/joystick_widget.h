#pragma once

#include <QWidget>

class JoystickWidget : public QWidget
{
    Q_OBJECT
public:
    explicit JoystickWidget(QWidget *parent = nullptr);

    // нормализованные значения [-1..1]
    double x() const { return x_; }
    double y() const { return y_; }

signals:
    void positionChanged(double x, double y);

protected:
    void paintEvent(QPaintEvent *event) override;
    void mousePressEvent(QMouseEvent *event) override;
    void mouseMoveEvent(QMouseEvent *event) override;
    void mouseReleaseEvent(QMouseEvent *event) override;

private:
    void updateFromMouse(const QPoint &pos);

    double x_{0.0};
    double y_{0.0};
    bool dragging_{false};
};
