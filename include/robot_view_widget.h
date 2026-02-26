#ifndef ROBOT_VIEW_WIDGET_H
#define ROBOT_VIEW_WIDGET_H

#include <QWidget>
#include <array>

class QPainter;

class RobotViewWidget : public QWidget
{
    Q_OBJECT

public:
    explicit RobotViewWidget(QWidget *parent = nullptr);

    // Поза робота в глобальной системе (для симуляции)
    void setPose(double x, double y, double theta);

    // Позиции звеньев манипулятора (4 DoF, углы в радианах)
    void setJointPositions(const std::array<double, 4> &joints);

    // Скорости гусениц (для визуальной индикации, м/с)
    void setTrackSpeeds(double left_speed, double right_speed);

    // Состояние захвата
    void setGripperClosed(bool closed);

protected:
    void paintEvent(QPaintEvent *event) override;

private:
    void drawTrackedBase(QPainter &p, double scale);
    void drawManipulator(QPainter &p, double scale);

private:
    // Поза робота
    double x_;
    double y_;
    double theta_;

    // Скорости гусениц
    double left_speed_;
    double right_speed_;

    // Манипулятор
    std::array<double, 4> joints_;
    bool gripper_closed_;
};

#endif // ROBOT_VIEW_WIDGET_H
