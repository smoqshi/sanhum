import { tank } from './robotState.js';
import { sendBaseCommand, sendArmCommand } from './network.js';

let vLinearSlider, vAngularSlider, turretSlider, armSlider, gripperSlider;
let lblVLinear, lblVAngular, lblTurret, lblArm, lblGripper;
let chkSimulation;
let gamepadStatusLabel;

let gamepadIndex = null;

export function initUI() {
    vLinearSlider   = document.getElementById('vLinear');
    vAngularSlider  = document.getElementById('vAngular');
    turretSlider    = document.getElementById('turretAngle');
    armSlider       = document.getElementById('armExtend');
    gripperSlider   = document.getElementById('gripper');

    const vLinearValue  = document.getElementById('vLinearValue');
    const vAngularValue = document.getElementById('vAngularValue');
    const turretValue   = document.getElementById('turretAngleValue');
    const armValue      = document.getElementById('armExtendValue');
    const gripperValue  = document.getElementById('gripperValue');

    lblVLinear  = document.getElementById('lblVLinear');
    lblVAngular = document.getElementById('lblVAngular');
    lblTurret   = document.getElementById('lblTurret');
    lblArm      = document.getElementById('lblArm');
    lblGripper  = document.getElementById('lblGripper');

    chkSimulation = document.getElementById('chkSimulation');
    if (chkSimulation) {
        chkSimulation.checked = tank.simulationMode;
        chkSimulation.addEventListener('change', () => {
            tank.simulationMode = chkSimulation.checked;
        });
    }

    gamepadStatusLabel = document.getElementById('gamepadStatus');

    if (vLinearSlider && vLinearValue) {
        vLinearSlider.addEventListener('input', () => {
            const v = parseFloat(vLinearSlider.value) || 0;
            tank.vLinearCmd = v;
            vLinearValue.textContent = v.toFixed(2);
            sendBaseIfNeeded();
        });
    }
    if (vAngularSlider && vAngularValue) {
        vAngularSlider.addEventListener('input', () => {
            const v = parseFloat(vAngularSlider.value) || 0;
            tank.vAngularCmdDeg = v;
            vAngularValue.textContent = v.toFixed(0);
            sendBaseIfNeeded();
        });
    }
    if (turretSlider && turretValue) {
        turretSlider.addEventListener('input', () => {
            const v = parseFloat(turretSlider.value) || 0;
            tank.turretAngle = v;
            turretValue.textContent = v.toFixed(0);
            sendArmIfNeeded();
        });
    }
    if (armSlider && armValue) {
        armSlider.addEventListener('input', () => {
            const v = parseFloat(armSlider.value) || 0;
            tank.armExtension = v / 100.0;
            armValue.textContent = v.toFixed(0);
            sendArmIfNeeded();
        });
    }
    if (gripperSlider && gripperValue) {
        gripperSlider.addEventListener('input', () => {
            const v = parseFloat(gripperSlider.value) || 0;
            tank.gripper = v / 100.0;
            gripperValue.textContent = v.toFixed(0);
            sendArmIfNeeded();
        });
    }

    wireControlButtons();
    initGamepadEvents();
}

// обновление по dt — здесь читаем геймпад
export function updateControls(dt) {
    pollGamepad(dt);
}

function wireControlButtons() {
    const buttons = Array.from(document.querySelectorAll('.controls-column button'));
    buttons.forEach(btn => {
        const text = btn.textContent || '';
        const label = text.toLowerCase();

        if (label.includes('forward')) {
            btn.addEventListener('click', () => {
                tank.vLinearCmd = +0.5;
                tank.vAngularCmdDeg = 0;
                sendBaseIfNeeded();
            });
        } else if (label.includes('back')) {
            btn.addEventListener('click', () => {
                tank.vLinearCmd = -0.5;
                tank.vAngularCmdDeg = 0;
                sendBaseIfNeeded();
            });
        } else if (label.includes('rotate left')) {
            btn.addEventListener('click', () => {
                tank.vLinearCmd = 0;
                tank.vAngularCmdDeg = +30;
                sendBaseIfNeeded();
            });
        } else if (label.includes('rotate right')) {
            btn.addEventListener('click', () => {
                tank.vLinearCmd = 0;
                tank.vAngularCmdDeg = -30;
                sendBaseIfNeeded();
            });
        } else if (label.includes('stop')) {
            btn.addEventListener('click', () => {
                tank.vLinearCmd = 0;
                tank.vAngularCmdDeg = 0;
                sendBaseIfNeeded(true);
            });
        } else if (label.includes('turret left')) {
            btn.addEventListener('click', () => {
                tank.turretAngle -= 5;
                sendArmIfNeeded();
            });
        } else if (label.includes('turret right')) {
            btn.addEventListener('click', () => {
                tank.turretAngle += 5;
                sendArmIfNeeded();
            });
        } else if (label.includes('arm extend')) {
            btn.addEventListener('click', () => {
                tank.armExtension = clamp01(tank.armExtension + 0.05);
                sendArmIfNeeded();
            });
        } else if (label.includes('arm retract')) {
            btn.addEventListener('click', () => {
                tank.armExtension = clamp01(tank.armExtension - 0.05);
                sendArmIfNeeded();
            });
        } else if (label.includes('gripper close')) {
            btn.addEventListener('click', () => {
                tank.gripper = clamp01(tank.gripper + 0.1);
                sendArmIfNeeded();
            });
        } else if (label.includes('gripper open')) {
            btn.addEventListener('click', () => {
                tank.gripper = clamp01(tank.gripper - 0.1);
                sendArmIfNeeded();
            });
        }
    });

    const resetBtn = document.getElementById('btnResetPose');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            tank.resetPose();
            sendBaseIfNeeded(true);
            sendArmIfNeeded();
        });
    }
}

function sendBaseIfNeeded(emergency = false) {
    if (tank.simulationMode) return;
    const vLin = tank.vLinearCmd;
    const vAng = tank.vAngularCmdDeg * Math.PI / 180.0;
    sendBaseCommand(vLin, vAng, emergency);
}

function sendArmIfNeeded() {
    if (tank.simulationMode) return;
    const extend = tank.armExtension;
    const grip = tank.gripper;
    const turret = tank.turretAngle;
    sendArmCommand(extend, grip, turret);
}

export function updateDashboardFromState() {
    if (lblVLinear) {
        lblVLinear.textContent = `${tank.vLinear.toFixed(2)} m/s`;
    }
    if (lblVAngular) {
        lblVAngular.textContent = `${tank.vAngular.toFixed(1)} °/s`;
    }
    if (lblTurret) {
        lblTurret.textContent = `${tank.turretAngle.toFixed(1)} °`;
    }
    if (lblArm) {
        lblArm.textContent = `${(tank.armExtension * 100).toFixed(1)} %`;
    }
    if (lblGripper) {
        lblGripper.textContent = `${(tank.gripper * 100).toFixed(1)} %`;
    }

    if (turretSlider) {
        turretSlider.value = tank.turretAngle.toFixed(0);
    }
    if (armSlider) {
        armSlider.value = (tank.armExtension * 100).toFixed(0);
    }
    if (gripperSlider) {
        gripperSlider.value = (tank.gripper * 100).toFixed(0);
    }

    if (gamepadStatusLabel) {
        gamepadStatusLabel.textContent = tank.gamepadConnected
            ? 'Gamepad: connected'
            : 'Gamepad: not connected';
    }
}

/* ---------- Gamepad API ---------- */

function initGamepadEvents() {
    window.addEventListener('gamepadconnected', (e) => {
        const gp = e.gamepad;
        gamepadIndex = gp.index;
        tank.gamepadConnected = true;
        if (gamepadStatusLabel) {
            gamepadStatusLabel.textContent = 'Gamepad: connected';
        }
    });

    window.addEventListener('gamepaddisconnected', (e) => {
        if (gamepadIndex === e.gamepad.index) {
            gamepadIndex = null;
            tank.gamepadConnected = false;
            if (gamepadStatusLabel) {
                gamepadStatusLabel.textContent = 'Gamepad: not connected';
            }
        }
    });
}

function pollGamepad(dt) {
    const gps = navigator.getGamepads ? navigator.getGamepads() : [];
    const gp = (gps && gamepadIndex !== null) ? gps[gamepadIndex] : null;

    if (!gp) {
        tank.gamepadConnected = false;
        return;
    }

    tank.gamepadConnected = true;

    const lx = gp.axes[0] || 0;
    const ly = gp.axes[1] || 0;
    const rx = gp.axes[2] || 0;
    const ry = gp.axes[3] || 0;
    const lt = gp.buttons[6] ? gp.buttons[6].value : 0;
    const rt = gp.buttons[7] ? gp.buttons[7].value : 0;

    const dead = 0.3;
    const ax = (Math.abs(lx) > dead) ? lx : 0;
    const ay = (Math.abs(ly) > dead) ? ly : 0;
    const axR = (Math.abs(rx) > dead) ? rx : 0;
    const ayR = (Math.abs(ry) > dead) ? ry : 0;

    // база: LS
    tank.vLinearCmd = -ay;
    tank.vAngularCmdDeg = ax * 40.0;

    // манипулятор: плавные изменения
    const turretSpeedDeg = 25.0;
    const armSpeed = 0.25;
    const gripSpeed = 0.4;

    tank.turretAngle += axR * turretSpeedDeg * dt;
    tank.armExtension = clamp01(
        tank.armExtension - ayR * armSpeed * dt
    );
    const gripDelta = (rt - lt) * gripSpeed * dt;
    tank.gripper = clamp01(tank.gripper + gripDelta);

    // если работаем с реальным роботом — отправляем команды на борт
    if (!tank.simulationMode) {
        sendBaseIfNeeded();
        sendArmIfNeeded();
    }
}

function clamp01(x) {
    if (x < 0) return 0;
    if (x > 1) return 1;
    return x;
}
