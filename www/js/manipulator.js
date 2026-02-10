import { tank } from './robotState.js';

export function initManipulator() {}

export function drawManipulator(ctx) {
    const hullW = 160;
    const hullH = 46;

    const bedW = hullW * 0.55;
    const bedX = -hullW / 2;
    const turretBaseX = bedX + bedW * 0.5; // центр задней платформы
    const turretBaseY = 0;

    const cx = tank.x;
    const cy = tank.y;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(tank.heading);

    ctx.save();
    ctx.translate(turretBaseX, turretBaseY);
    ctx.rotate(tank.turretAngle);

    // башня
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

    // база стрелы (исходная точка)
    const baseY = -turretH / 2;

    // ПЕРВОЕ ЗВЕНО НЕ ВРАЩАЕТСЯ — оно всегда вдоль локальной -X оси башни
    const baseDirX = -1;  // направление "назад" от башни
    const baseDirY =  0;

    // длина первого звена фиксированная
    const L0 = 40;

    const baseEndX = baseDirX * L0;
    const baseEndY = baseY   + baseDirY * L0;

    // телескопический ВЫЛЕТ вдоль того же направления
    const LextMax = 60;
    const extNorm = tank.uiArmExtend / 100.0; // 0..1
    const Lext = LextMax * extNorm;

    const tipX = baseEndX + baseDirX * Lext;
    const tipY = baseEndY + baseDirY * Lext;

    // рисуем базовое звено
    ctx.strokeStyle = "#facc15";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, baseY);
    ctx.lineTo(baseEndX, baseEndY);
    ctx.stroke();

    // рисуем телескопический участок
    ctx.beginPath();
    ctx.moveTo(baseEndX, baseEndY);
    ctx.lineTo(tipX, tipY);
    ctx.stroke();

    // небольшой маркер середины телескопа
    const midX = baseEndX + baseDirX * (Lext * 0.5);
    const midY = baseEndY + baseDirY * (Lext * 0.5);
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(midX, midY - 3);
    ctx.lineTo(midX, midY + 3);
    ctx.stroke();

    // захват на конце
    const baseAngle = Math.atan2(baseDirY, baseDirX);  // направление стрелы (сейчас вдоль -X)
    const endAngle = baseAngle; //+ Math.PI;              // +180° — смотрим "вперёд" от манипулятора

    const gripLen = 14;
    const gripOpen = (1 - tank.gripper) * 0.6;

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

    ctx.stroke();


    ctx.restore();
    ctx.restore();
}
