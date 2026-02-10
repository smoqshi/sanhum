#include "armkinematics.h"

#include <cmath>

namespace ArmKinematics {

void fromExtension(double ext, double &q2, double &q3, double &q4)
{
    if (ext < 0.0) ext = 0.0;
    if (ext > 1.0) ext = 1.0;

    const double L1 = 0.35;
    const double L2 = 0.30;

    const double minReach = 0.05;
    const double maxReach = L1 + L2 - 0.05;

    const double minHeight = 0.25;
    const double maxDrop   = -0.10;

    double x = minReach + (maxReach - minReach) * ext;
    double z = minHeight + (maxDrop   - minHeight) * ext;

    double dist = std::sqrt(x * x + z * z);

    const double rMin = std::fabs(L1 - L2) + 1e-3;
    const double rMax = L1 + L2 - 1e-3;

    double r = dist;
    if (r < rMin) r = rMin;
    if (r > rMax) r = rMax;

    if (dist > 1e-3) {
        double k = r / dist;
        x *= k;
        z *= k;
    }

    double cos2 = (x * x + z * z - L1 * L1 - L2 * L2) / (2.0 * L1 * L2);
    if (cos2 < -1.0) cos2 = -1.0;
    if (cos2 > 1.0)  cos2 = 1.0;

    q3 = std::acos(cos2);

    double k1 = L1 + L2 * std::cos(q3);
    double k2 = L2 * std::sin(q3);

    q2 = std::atan2(z, x) - std::atan2(k2, k1);

    // простой вариант для ориентации захвата
    q4 = -(q2 + q3) * 0.5;
}

} // namespace ArmKinematics
