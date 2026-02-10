     import { tank } from './robotState.js';

// инициализация сети (если нужно что‑то сделать при старте)
export function initNetwork() {
    // пока ничего
}

// периодический опрос статуса
export async function pollStatus() {
    try {
        const r = await fetch('/api/status');
        if (!r.ok) return;
        const d = await r.json();

        const s = document.getElementById('status');
        if (s) {
            const cpu  = (d.cpu  ?? '').toString();
            const temp = (d.temp ?? '').toString();
            const up   = (d.uptime ?? '').toString();
            s.textContent = `CPU: ${cpu} | Temp: ${temp} | Uptime: ${up}`;
        }
    } catch (e) {
        console.error('pollStatus error', e);
    }
}

// команды на базу
export async function sendBaseCommand(vLinear, vAngular, emergency = false) {
    try {
        if (tank.simulationMode) return; // в симуляции — только на канве

        const payload = emergency
            ? { emergency: true }
            : { vLinear, vAngular };

        await fetch('/api/base', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } catch (e) {
        console.error('sendBaseCommand error', e);
    }
}

// команды на манипулятор
export async function sendArmCommand(extend, gripper, turretAngle) {
    try {
        if (tank.simulationMode) return;
        await fetch('/api/arm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ extend, gripper, turretAngle })
        });
    } catch (e) {
        console.error('sendArmCommand error', e);
    }
}

// если у тебя есть API с реальным joint_state — можешь потом сюда вернуть парсинг
export async function pollJointState() {
    try {
        const r = await fetch('/api/joint_state');
        if (!r.ok) return;
        const d = await r.json();

        // пример: если придёт arm: { q2,q3,q4,gripper,turret }
        if (d.arm) {
            tank.q2          = d.arm.q2 ?? tank.q2;
            tank.q3          = d.arm.q3 ?? tank.q3;
            tank.q4          = d.arm.q4 ?? tank.q4;
            tank.gripper     = d.arm.gripper ?? tank.gripper;
            tank.turretAngle = d.arm.turret ?? tank.turretAngle;
        }
    } catch (e) {
        console.error('pollJointState error', e);
    }
}
