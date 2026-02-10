import { tank } from './robotState.js';

// корпус шире, кабина спереди, платформа сзади
const hullW = 160;
const hullH = 100;

export function initChassis(canvas) {
    tank.canvasWidth  = canvas.width;
    tank.canvasHeight = canvas.height;

    tank.x = tank.canvasWidth * 0.5;
    tank.y = tank.canvasHeight * 0.5;

    if (tank.trackPhaseLeft === undefined)  tank.trackPhaseLeft  = 0;
    if (tank.trackPhaseRight === undefined) tank.trackPhaseRight = 0;
}

export function drawChassis(ctx) {
    const cx = tank.x;
    const cy = tank.y;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(tank.heading);

    // корпус
    ctx.fillStyle = "#111827";
    ctx.strokeStyle = "#4b5563";
    ctx.lineWidth = 2;
    ctx.beginPath();
    if (ctx.roundRect) {
        ctx.roundRect(-hullW / 2, -hullH / 2, hullW, hullH, 8);
    } else {
        ctx.rect(-hullW / 2, -hullH / 2, hullW, hullH);
    }
    ctx.fill();
    ctx.stroke();

    // кабина спереди
    const cabW = 40;
    const cabH = 80;
    ctx.fillStyle = "#1f2937";
    ctx.beginPath();
    if (ctx.roundRect) {
        ctx.roundRect(hullW / 2 - cabW, -cabH / 2, cabW, cabH, 4);
    } else {
        ctx.rect(hullW / 2 - cabW, -cabH / 2, cabW, cabH);
    }
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#60a5fa";
    ctx.fillRect(
        hullW / 2 - cabW + 4,
        -cabH / 2 + 4,
        cabW - 8,
        cabH - 10
    );

    // задняя платформа под манипулятор
    const bedW = hullW * 0.55;
    const bedX = -hullW / 2;
    ctx.fillStyle = "#0b1120";
    ctx.fillRect(bedX, -hullH / 2 + 4, bedW, hullH - 8);

    // гусеницы вдоль кузова (без "выступания")
    const trackLen = hullW;
    const seg = 12;

    const phaseL = tank.trackPhaseLeft  ?? 0;
    const phaseR = tank.trackPhaseRight ?? 0;

    ctx.strokeStyle = "#374151";
    ctx.lineWidth = 3;

    function drawTrack(y, phase) {
        ctx.beginPath();
        for (let x = -trackLen / 2; x < trackLen / 2; x += seg) {
            const xx = x + (phase % seg);
            ctx.moveTo(xx, y - 3);
            ctx.lineTo(xx, y + 3);
        }
        ctx.stroke();
    }

    // размещаем ровно по нижней и верхней кромке корпуса
    const trackOffsetY = hullH / 2 + 4;
    drawTrack(-trackOffsetY, phaseL); // левая
    drawTrack( trackOffsetY, phaseR); // правая

    // стрелка носа
    ctx.fillStyle = "#f97316";
    ctx.beginPath();
    const noseX = hullW / 2;
    ctx.moveTo(noseX + 8, 0);
    ctx.lineTo(noseX - 8, -10);
    ctx.lineTo(noseX - 8,  10);
    ctx.closePath();
    ctx.fill();

    ctx.restore();
}

export function updateBase(dt) {
    const v = tank.vLinear;
    const w = tank.vAngular;

    tank.heading += w * dt;
    tank.x       += Math.cos(tank.heading) * v * dt;
    tank.y       += Math.sin(tank.heading) * v * dt;

    const cw = tank.canvasWidth;
    const ch = tank.canvasHeight;
    if (tank.x < 0) tank.x += cw;
    if (tank.x > cw) tank.x -= cw;
    if (tank.y < 0) tank.y += ch;
    if (tank.y > ch) tank.y -= ch;

    // фазовая скорость для левой/правой гусеницы
    const B = 0.25; // "плечо" базы
    const vL = v - w * B;
    const vR = v + w * B;

    const k = 40;
    tank.trackPhaseLeft  = (tank.trackPhaseLeft  ?? 0) + vL * k * dt;
    tank.trackPhaseRight = (tank.trackPhaseRight ?? 0) + vR * k * dt;
}
