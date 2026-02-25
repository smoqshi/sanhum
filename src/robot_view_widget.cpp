#include "robot_view_widget.h"
#include <QPainter>
#include <QtMath>

RobotViewWidget::RobotViewWidget(QWidget *parent)
    : QWidget(parent)
{
    setMinimumSize(300, 300);
}

void RobotViewWidget::setPose(double x, double y, double theta)
{
    x_ = x;
    y_ = y;
    theta_ = theta;
    update();
}

void RobotViewWidget::setJointPositions(const std::array<double,4> &joints)
{
    joints_ = joints;
    update();
}

void RobotViewWidget::setTrackSpeeds(double left_speed, double right_speed)
{
    left_speed_ = left_speed;
    right_speed_ = right_speed;
    update();
}

void RobotViewWidget::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event);
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing, true);

    p.fillRect(rect(), Qt::black);

    QPoint center(width()/2, height()/2);

    p.translate(center);
    p.rotate(theta_ * 180.0 / M_PI);

    int body_w = 120;
    int body_h = 180;

    // корпус
    p.setBrush(QColor(60,60,60));
    p.setPen(Qt::NoPen);
    p.drawRect(-body_w/2, -body_h/2, body_w, body_h);

    // гусеницы
    QColor left_color  = (left_speed_  > 0.01) ? Qt::green :
                            (left_speed_  < -0.01) ? Qt::red : Qt::darkGray;
    QColor right_color = (right_speed_ > 0.01) ? Qt::green :
                             (right_speed_ < -0.01) ? Qt::red : Qt::darkGray;

    p.setBrush(left_color);
    p.drawRect(-body_w/2 - 20, -body_h/2, 20, body_h);

    p.setBrush(right_color);
    p.drawRect(body_w/2, -body_h/2, 20, body_h);

    // манипулятор (простая кинематика сверху)
    p.setPen(QPen(Qt::yellow, 4));
    QPointF base(0, -body_h/2);
    double len1 = 50, len2 = 40, len3 = 30, len4 = 20;
    double a1 = joints_[0], a2 = joints_[1], a3 = joints_[2], a4 = joints_[3];

    QPointF j1(base.x() + len1 * std::cos(a1), base.y() - len1 * std::sin(a1));
    QPointF j2(j1.x() + len2 * std::cos(a1+a2), j1.y() - len2 * std::sin(a1+a2));
    QPointF j3(j2.x() + len3 * std::cos(a1+a2+a3), j2.y() - len3 * std::sin(a1+a2+a3));
    QPointF j4(j3.x() + len4 * std::cos(a1+a2+a3+a4), j3.y() - len4 * std::sin(a1+a2+a3+a4));

    p.drawLine(base, j1);
    p.drawLine(j1, j2);
    p.drawLine(j2, j3);
    p.drawLine(j3, j4);
}
