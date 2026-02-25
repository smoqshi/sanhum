#pragma once

#include <QWidget>
#include <array>

class RobotViewWidget : public QWidget
{
    Q_OBJECT
public:
    explicit RobotViewWidget(QWidget *parent = nullptr);

    void setPose(double x, double y, double theta);
    void setJointPositions(const std::array<double,4> &joints);
    void setTrackSpeeds(double left_speed, double right_speed);

protected:
    void paintEvent(QPaintEvent *event) override;

private:
    double x_{0.0}, y_{0.0}, theta_{0.0};
    std::array<double,4> joints_{{0,0,0,0}};
    double left_speed_{0.0};
    double right_speed_{0.0};
};
