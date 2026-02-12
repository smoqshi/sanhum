import { tank } from './robotState.js';

// Простейшая 2D‑модель: башня + телескопическое звено + захват
export function initManipulator() {
    // Нормализуем начальные значения, если не заданы
    if (typeof tank.turretAngle !== 'number') {
        tank.turretAngle = 0.0;
    }
    if (typeof tank.armExtension !== 'number') {
        tank.armExtension = 0.5; // 50 %
    }
    if (typeof tank.gripper !== 'number') {
        tank.gripper = 0.3;      // 30 % закрытия
    }
}

export function drawManipulator(ctx) {
    // Геометрия должна совпадать с chassis.js
    const hullW = 160;
    const hullH = 100;
    const bedW = hullW * 0.55;
    const bedX = -hullW / 2;
    const turretBaseX = bedX + bedW * 0.5;  // центр задней платформы
    const turretBaseY = 0;

    const cx = tank.x;
    const cy = tank.y;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(tank.heading);

    // Переходим в систему координат башни
    ctx.save();
    ctx.translate(turretBaseX, turretBaseY);
    ctx.rotate(tank.turretAngle * Math.PI / 180.0);

    // Башня
    const turretW = 22;
    const turretH = 16;
    ctx.fillStyle = "#111827";
    ctx.strokeStyle = "#4b5563";
    ctx.lineWidth = 2;
    ctx.beginPath();
    if (ctx.roundRect) {
        ctx.roundRect(-turretW / 2, -turretH / 2, turretW, turretH, 4);
    } else {
        ctx.rect(-turretW / 2, -turretH / 2, turretW, turretH);
    }
    ctx.fill();
    ctx.stroke();

    // База стрелы — всегда вдоль локальной -X оси башни
    const baseY = -turretH / 2;
    const baseDirX = -1;
    const baseDirY = 0;

    // Первое звено фиксированной длины
    const L0 = 40;
    const baseEndX = baseDirX * L0;
    const baseEndY = baseY + baseDirY * L0;

    // Телескопический вылет вдоль того же направления
    const LextMax = 60;
    const extNorm = clamp01(tank.armExtension); // ожидаем 0..1
    const Lext = LextMax * extNorm;

    const tipX = baseEndX + baseDirX * Lext;
    const tipY = baseEndY + baseDirY * Lext;

    // Базовое звено
    ctx.strokeStyle = "#facc15";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, baseY);
    ctx.lineTo(baseEndX, baseEndY);
    ctx.stroke();

    // Телескопическая часть
    ctx.beginPath();
    ctx.moveTo(baseEndX, baseEndY);
    ctx.lineTo(tipX, tipY);
    ctx.stroke();

    // Маркер середины телескопа
    const midX = baseEndX + baseDirX * (Lext * 0.5);
    const midY = baseEndY + baseDirY * (Lext * 0.5);
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(midX, midY - 3);
    ctx.lineTo(midX, midY + 3);
    ctx.stroke();

    // Захват на конце
    const baseAngle = Math.atan2(baseDirY, baseDirX); // направление стрелы (вдоль -X)
    const endAngle = baseAngle;                       // можно развернуть при желании
    const gripLen = 14;
    const gripOpen = (1 - clamp01(tank.gripper)) * 0.6; // 0..0.6 рад

    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(tipX, tipY);
    ctx.lineTo(
        tipX + gripLen * Math.cos(endAngle - gripOpen),
        tipY + gripLen * Math.sin(endAngle - gripOpen)
    );
    ctx.moveTo(tipX, tipY);
    ctx.lineTo(
        tipX + gripLen * Math.cos(endAngle + gripOpen),
        tipY + gripLen * Math.sin(endAngle + gripOpen)
    );
    ctx.stroke();

    ctx.restore(); // из локальной системы башни
    ctx.restore(); // из мировой системы
}

function clamp01(x) {
    if (x < 0) return 0;
    if (x > 1) return 1;
    return x;
}
