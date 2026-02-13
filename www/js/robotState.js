// Нормализованное состояние робота/манипулятора для симуляции и реального робота
export const tank = {
    // команды оператора
    vLinearCmd: 0.0,        // м/с
    vAngularCmdDeg: 0.0,    // град/с

    // фактическое состояние (после интеграции)
    vLinear: 0.0,
    vAngularDeg: 0.0,
    x: 0.0,
    y: 0.0,
    yawDeg: 0.0,

    // манипулятор
    turretAngle: 0.0,       // градусы
    armExtension: 0.5,      // 0..1
    gripper: 0.3,           // 0..1

    // режимы
    simulationMode: true,
    gamepadConnected: false,

    resetPose() {
        this.x = 0.0;
        this.y = 0.0;
        this.yawDeg = 0.0;
        this.vLinear = 0.0;
        this.vAngularDeg = 0.0;
        this.vLinearCmd = 0.0;
        this.vAngularCmdDeg = 0.0;
        this.turretAngle = 0.0;
        this.armExtension = 0.5;
        this.gripper = 0.3;
    }
};
