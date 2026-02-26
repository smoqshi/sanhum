#pragma once

#include <QWidget>
#include <QString>

/**
 * @brief JoystickWidget
 *
 * Простой виджет визуализации джойстика:
 *  - рисует окружность и ручку (x_, y_) в диапазоне [-1;1];
 *  - позволяет управлять положением мышью;
 *  - может получать положение извне через setAxes();
 *  - может отображать подпись (label_) под кругом.
 */
class JoystickWidget : public QWidget
{
    Q_OBJECT
public:
    explicit JoystickWidget(QWidget *parent = nullptr);

    // Программная установка положения ручки (для геймпада/клавиатуры)
    void setAxes(double x, double y);

    // Подпись под джойстиком
    void setLabel(const QString &text);

signals:
    // Сигнал при изменении положения ручки мышью
    void positionChanged(double x, double y);

protected:
    void paintEvent(QPaintEvent *event) override;
    void mousePressEvent(QMouseEvent *event) override;
    void mouseMoveEvent(QMouseEvent *event) override;
    void mouseReleaseEvent(QMouseEvent *event) override;

private:
    void updateFromMouse(const QPoint &pos);

    double x_ = 0.0;       // -1..1
    double y_ = 0.0;       // -1..1
    bool   dragging_ = false;
    QString label_;
};
