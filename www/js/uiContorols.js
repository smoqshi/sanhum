import { tank } from './robotState.js';
import { sendBaseCommand, sendArmCommand } from './network.js';

let gamepadIndex = null;

export function initUI() {
    // чекбокс симуляции
    const simCheckbox = document.getElementById('chkSimulation');
    if (simCheckbox) {
        tank.simulationMode = simCheckbox.checked;
        simCheckbox.addEventListener('change', () => {
            tank.simulationMode = simCheckbox.checked;
        });
    }

    // базовые кнопки
    const bind = (id, v, w) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('mousedown', () => {
            tank.vLinear  = v;
            tank.vAngular = w;
            sendBaseCommand(v, w);
            updateSpeedLabelsFromState();
        });
        el.addEventListener('mouseup', () => {
            tank.vLinear  = 0;
            tank.vAngular = 0;
            sendBaseCommand(0, 0);
            updateSpeedLabelsFromState();
        });
        el.addEventListener('mouseleave', () => {
            tank.vLinear  = 0;
            tank.vAngular = 0;
            sendBaseCommand(0, 0);
            updateSpeedLabelsFromState();
        });
    };

    bind('btnBaseForward',  0.3,  0.0);
    bind('btnBaseBack',    -0.3,  0.0);
    bind('btnBaseLeft',     0.0,  0.7);
    bind('btnBaseRight',    0.0, -0.7);

    const btnStop = document.getElementById('btnBaseStop');
    if (btnStop) {
        btnStop.addEventListener('click', () => {
            tank.vLinear  = 0;
            tank.vAngular = 0;
            sendBaseCommand(0, 0);
            updateSpeedLabelsFromState();
        });
    }

    // геймпад
    window.addEventListener('gamepadconnected', (e) => {
        gamepadIndex = e.gamepad.index;
        const el = document.getElementById('gamepadStatus');
        if (el) el.textContent = `Gamepad: ${e.gamepad.id}`;
    });

    window.addEventListener('gamepaddisconnected', () => {
        gamepadIndex = null;
        const el = document.getElementById('gamepadStatus');
        if (el) el.textContent = 'Gamepad: not connected';
    });
}

function updateSpeedLabelsFromState() {
    const vLabel = document.getElementById('vLinearLabel');
    const vVal   = document.getElementById('vLinearVal');
    const wLabel = document.getElementById('vAngularLabel');
    const wVal   = document.getElementById('vAngularVal');

    if (vLabel) vLabel.textContent = tank.vLinear.toFixed(2);
    if (vVal)   vVal.textContent   = tank.vLinear.toFixed(2);
    if (wLabel) wLabel.textContent = (tank.vAngular * 180 / Math.PI).toFixed(1);
    if (wVal)   wVal.textContent   = (tank.vAngular * 180 / Math.PI).toFixed(1);
}

export function updateControls(dt) {
    const vLinSlider   = document.getElementById('vLinear');
    const vAngSlider   = document.getElementById('vAngular');
    const turretSlider = document.getElementById('turretAngle');
    const armExtSlider = document.getElementById('armExtend');
    const gripSlider   = document.getElementById('gripper');

    // база — слайдеры
    if (vLinSlider) {
        const val = parseFloat(vLinSlider.value);
        tank.vLinear = val;
        document.getElementById('vLinearVal').textContent   = val.toFixed(2);
        document.getElementById('vLinearLabel').textContent = val.toFixed(2);
    }

    if (vAngSlider) {
        const deg = parseFloat(vAngSlider.value);
        const rad = deg * Math.PI / 180;
        tank.vAngular = rad;
        document.getElementById('vAngularVal').textContent   = deg.toString();
        document.getElementById('vAngularLabel').textContent = deg.toString();
    }

    // башня манипулятора
    if (turretSlider) {
        const deg = parseFloat(turretSlider.value);
        const rad = deg * Math.PI / 180;
        tank.turretAngle = rad;
        document.getElementById('turretAngleVal').textContent   = deg.toString();
        document.getElementById('turretAngleLabel').textContent = deg.toString();
    }

    // удлинение стрелы манипулятора
    if (armExtSlider) {
        const val = parseFloat(armExtSlider.value);
        tank.uiArmExtend = val; // 0..100
        document.getElementById('armExtendVal').textContent   = val.toString();
        document.getElementById('armExtendLabel').textContent = val.toFixed(1);

        const t = val / 100.0;
        const q2min = -30 * Math.PI / 180;
        const q2max =  60 * Math.PI / 180;
        tank.q2 = q2min + (q2max - q2min) * t;
    }

    // захват
    if (gripSlider) {
        const val = parseFloat(gripSlider.value);
        tank.uiGripper = val;
        tank.gripper   = val / 100.0;
        document.getElementById('gripperVal').textContent   = val.toString();
        document.getElementById('gripperLabel').textContent = val.toFixed(1);
    }

    // --- ГЕЙМПАД ---
    if (gamepadIndex === null) return;

    const gp = navigator.getGamepads()[gamepadIndex];
    if (!gp) return;

    // база — левый стик
    const lx = gp.axes[0] || 0;
    const ly = gp.axes[1] || 0;

    const dead = 0.15;
    const ax = (Math.abs(lx) < dead) ? 0 : lx;
    const ay = (Math.abs(ly) < dead) ? 0 : ly;

    const vMax = 0.3;
    const wMax = 1.0;

    const v = -ay * vMax;
    const w =  ax * wMax;

    tank.vLinear  = v;
    tank.vAngular = w;

    // Кнопка B (обычно index 1) — экстренный стоп
    const emergency = gp.buttons[1] && gp.buttons[1].pressed;

    if (emergency) {
        sendBaseCommand(0, 0, true);
        tank.vLinear  = 0;
        tank.vAngular = 0;
    } else {
        sendBaseCommand(v, w);
    }

    updateSpeedLabelsFromState();

    // манипулятор — правый стик
    const rx = gp.axes[2] || 0;
    const ry = gp.axes[3] || 0;

    const deadR = 0.15;
    const rax = (Math.abs(rx) < deadR) ? 0 : rx;
    const ray = (Math.abs(ry) < deadR) ? 0 : ry;

    const turretSpeed = 1.2;
    tank.turretAngle += rax * turretSpeed * dt;

    if (turretSlider) {
        const deg = tank.turretAngle * 180 / Math.PI;
        turretSlider.value = deg.toFixed(0);
        document.getElementById('turretAngleVal').textContent   = deg.toFixed(0);
        document.getElementById('turretAngleLabel').textContent = deg.toFixed(0);
    }

    const extendSpeed = 40;
    tank.uiArmExtend = Math.min(100, Math.max(0, tank.uiArmExtend - ray * extendSpeed * dt));
    if (armExtSlider) {
        armExtSlider.value = tank.uiArmExtend.toFixed(0);
        document.getElementById('armExtendVal').textContent   = tank.uiArmExtend.toFixed(0);
        document.getElementById('armExtendLabel').textContent = tank.uiArmExtend.toFixed(1);
    }

    const tExt = tank.uiArmExtend / 100.0;
    const q2min = -30 * Math.PI / 180;
    const q2max =  60 * Math.PI / 180;
    tank.q2 = q2min + (q2max - q2min) * tExt;

    const lt = gp.buttons[6]?.value || 0;
    const rt = gp.buttons[7]?.value || 0;
    const gripSpeed = 40;
    tank.uiGripper += (lt - rt) * gripSpeed * dt;
    tank.uiGripper = Math.min(100, Math.max(0, tank.uiGripper));
    tank.gripper   = tank.uiGripper / 100.0;

    if (gripSlider) {
        gripSlider.value = tank.uiGripper.toFixed(0);
        document.getElementById('gripperVal').textContent   = tank.uiGripper.toFixed(0);
        document.getElementById('gripperLabel').textContent = tank.uiGripper.toFixed(1);
    }

    if (!tank.simulationMode) {
        const extendNorm = tank.uiArmExtend / 100.0;
        sendArmCommand(extendNorm, tank.gripper, tank.turretAngle);
    }
}
