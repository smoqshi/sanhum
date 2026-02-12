import { tank } from './robotState.js';

export function initManipulator() {
    if (typeof tank.turretAngle !== 'number') {
        tank.turretAngle = 0.0;
    }
    if (typeof tank.armExtension !== 'number') {
        tank.armExtension = 0.5;
    }
    if (typeof tank.gripper !== 'number') {
        tank.gripper = 0.3;
    }
}

export function drawManipulator(ctx) {
    // новые размеры под уменьшенный корпус
    const hullW = 120;
    const hullH = 70;
    const bedW = hullW * 0.55;
    const bedX = -hullW / 2;
    const turretBaseX = bedX + bedW * 0.5;
    const turretBaseY = 0;

    const cx = tank.x;
    const cy = tank.y;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(tank.heading);

    ctx.save();
    ctx.translate(turretBaseX, turretBaseY);
    ctx.rotate(tank.turretAngle * Math.PI / 180.0);

    const turretW = 18;
    const turretH = 14;
    ctx.fillStyle = "#111827";
    ctx.strokeStyle = "#4b5563";
    ctx.lineWidth = 2;
    ctx.beginPath();
    if (ctx.roundRect) {
        ctx.roundRect(-turretW / 2, -turretH / 2, turretW, turretH, 3);
    } else {
        ctx.rect(-turretW / 2, -turretH / 2, turretW, turretH);
    }
    ctx.fill();
    ctx.stroke();

    const baseY = -turretH / 2;
    const baseDirX = -1;
    const baseDirY = 0;

    const L0 = 30;
    const baseEndX = baseDirX * L0;
    const baseEndY = baseY + baseDirY * L0;

    const LextMax = 45;
    const extNorm = clamp01(tank.armExtension);
    const Lext = LextMax * extNorm;

    const tipX = baseEndX + baseDirX * Lext;
    const tipY = baseEndY + baseDirY * Lext;

    ctx.strokeStyle = "#facc15";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, baseY);
    ctx.lineTo(baseEndX, baseEndY);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(baseEndX, baseEndY);
    ctx.lineTo(tipX, tipY);
    ctx.stroke();

    const midX = baseEndX + baseDirX * (Lext * 0.5);
    const midY = baseEndY + baseDirY * (Lext * 0.5);
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(midX, midY - 2);
    ctx.lineTo(midX, midY + 2);
    ctx.stroke();

    const baseAngle = Math.atan2(baseDirY, baseDirX);
    const endAngle = baseAngle;
    const gripLen = 10;
    const gripOpen = (1 - clamp01(tank.gripper)) * 0.6;

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

    ctx.restore();
    ctx.restore();
}

function clamp01(x) {
    if (x < 0) return 0;
    if (x > 1) return 1;
    return x;
}
