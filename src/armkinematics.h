#ifndef ARMKINEMATICS_H
#define ARMKINEMATICS_H

namespace ArmKinematics {

// По заданному относительному выдвижению ext [0..1]
// вычисляет углы шарниров q2, q3, q4 [рад]
void fromExtension(double ext, double &q2, double &q3, double &q4);

} // namespace ArmKinematics

#endif // ARMKINEMATICS_H
