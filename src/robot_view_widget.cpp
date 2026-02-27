#include "robot_view_widget.h"
#include <QPainter>
#include <QtMath>

RobotViewWidget::RobotViewWidget(QWidget *parent)
    : QWidget(parent)
    , x_(0.0)
    , y_(0.0)
    , theta_(0.0)
    , left_speed_(0.0)
    , right_speed_(0.0)
    , gripper_closed_(false)
{
    setMinimumSize(300, 300);

    joints_.fill(0.0);
}

void RobotViewWidget::setPose(double x, double y, double theta)
{
    x_ = x;
    y_ = y;
    theta_ = theta;
    update();
}

void RobotViewWidget::setJointPositions(const std::array<double, 4> &joints)
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

void RobotViewWidget::setGripperClosed(bool closed)
{
    gripper_closed_ = closed;
    update();
}

void RobotViewWidget::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event);
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing, true);

    // Заливаем фоном (не чёрный прямоугольник, а светлый фон)
    p.fillRect(rect(), QColor(30, 30, 30));

    // Рисуем круговую арену
    QPoint center(width() / 2, height() / 2);
    int radius = qMin(width(), height()) / 2 - 10;

    p.setPen(QPen(Qt::gray, 2));
    p.setBrush(QColor(10, 10, 10));
    p.drawEllipse(center, radius, radius);

    // Переходим в систему координат арены
    p.translate(center);

    // Масштаб: приведём миллиметры к пикселям
    // Берём масштаб так, чтобы робот хорошо помещался в круг
    // Робот: ширина 280 мм, длина 370 мм
    double robot_width_mm = 280.0;
    double robot_length_mm = 370.0;
    double scale = (radius * 0.6) / (robot_length_mm / 2.0); // длина по вертикали

    // Одометрическое смещение по x_, y_ (в метрах) -> мм -> пиксели
    double x_mm = x_ * 1000.0;
    double y_mm = y_ * 1000.0;

    p.translate(x_mm * scale / 1000.0, -y_mm * scale / 1000.0);
    p.rotate(theta_ * 180.0 / M_PI);

    // Рисуем корпус робота (мнимое 3D сверху)
    drawTrackedBase(p, scale);
    drawManipulator(p, scale);
}

void RobotViewWidget::drawTrackedBase(QPainter &p, double scale)
{
    // Основной корпус как прямоугольник 280x370 мм
    double body_w_mm = 280.0;
    double body_l_mm = 370.0;

    double body_w = body_w_mm * scale / 1000.0;
    double body_l = body_l_mm * scale / 1000.0;

    QRectF bodyRect(-body_w / 2.0, -body_l / 2.0, body_w, body_l);

    p.save();
    p.setPen(Qt::NoPen);
    p.setBrush(QColor(80, 80, 80)); // Solid color for the body

    p.drawRect(bodyRect);

    // Передняя сторона (по -Y) подчеркнута цветом
    p.setBrush(QColor(120, 120, 120));
    QRectF frontRect(-body_w / 2.0, -body_l / 2.0, body_w, body_l * 0.15);
    p.drawRect(frontRect);

    // Гусеницы: ширина 50 мм, расстояние между ними 185 мм
    double track_w_mm = 50.0;
    double track_gap_mm = 185.0;

    double track_w = track_w_mm * scale / 1000.0;
    double track_gap = track_gap_mm * scale / 1000.0;

    double tracks_total_w = track_gap + 2.0 * track_w;

    double left_x = -tracks_total_w / 2.0;
    double right_x = tracks_total_w / 2.0 - track_w;

    QColor left_color = (left_speed_ > 0.01) ? Qt::green :
                        (left_speed_ < -0.01) ? Qt::red : Qt::darkGray;
    QColor right_color = (right_speed_ > 0.01) ? Qt::green :
                         (right_speed_ < -0.01) ? Qt::red : Qt::darkGray;

    p.setBrush(left_color);
    p.drawRect(QRectF(left_x, -body_l / 2.0, track_w, body_l));

    p.setBrush(right_color);
    p.drawRect(QRectF(right_x, -body_l / 2.0, track_w, body_l));

    p.restore();
}

void RobotViewWidget::drawManipulator(QPainter &p, double scale)
{
    // База манипулятора в передней части корпуса
    double body_l_mm = 370.0;
    double body_l = body_l_mm * scale / 1000.0;

    QPointF base(0.0, -body_l / 2.0);

    p.save();
    p.setPen(QPen(Qt::cyan, 4, Qt::SolidLine, Qt::RoundCap)); // Thicker and cyan

    // Условные длины звеньев, мм
    double len1_mm = 100.0;
    double len2_mm = 100.0;
    double len3_mm = 80.0;
    double len4_mm = 60.0;

    double len1 = len1_mm * scale / 1000.0;
    double len2 = len2_mm * scale / 1000.0;
    double len3 = len3_mm * scale / 1000.0;
    double len4 = len4_mm * scale / 1000.0;

    double a1 = joints_[0];
    double a2 = joints_[1];
    double a3 = joints_[2];
    double a4 = joints_[3];

    QPointF j1(base.x() + len1 * std::cos(a1),
               base.y() - len1 * std::sin(a1));
    QPointF j2(j1.x() + len2 * std::cos(a1 + a2),
               j1.y() - len2 * std::sin(a1 + a2));
    QPointF j3(j2.x() + len3 * std::cos(a1 + a2 + a3),
               j2.y() - len3 * std::sin(a1 + a2 + a3));
    QPointF j4(j3.x() + len4 * std::cos(a1 + a2 + a3 + a4),
               j3.y() - len4 * std::sin(a1 + a2 + a3 + a4));

    p.drawLine(base, j1);
    p.drawLine(j1, j2);
    p.drawLine(j2, j3);
    p.drawLine(j3, j4);

    // Захват
    p.setPen(QPen(gripper_closed_ ? Qt::red : Qt::green, 4, Qt::SolidLine, Qt::RoundCap));
    double grip_size = 12.0;
    QPointF g1(j4.x() - grip_size, j4.y());
    QPointF g2(j4.x() + grip_size, j4.y());
    p.drawLine(g1, j4);
    p.drawLine(j4, g2);

    p.restore();
}
