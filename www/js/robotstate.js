export const tank = {
    // состояние для визуализации
    x: 0,
    y: 0,
    heading: 0,      // рад
    vLinear: 0,      // м/с
    vAngular: 0,     // рад/с

    // манипулятор в локальных углах
    turretAngle: 0,  // q1, рад
    q2: 0,           // плечо
    q3: 0,           // локоть
    q4: 0,           // кисть
    gripper: 0.3,    // 0..1

    uiArmExtend: 50, // 0..100, для нашей упрощённой IK
    uiGripper: 30,   // 0..100

    trackPhase: 0,

    simulationMode: false,

    canvasWidth: 440,
    canvasHeight: 260
};
