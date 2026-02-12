import { tank } from './robotState.js';

// Уменьшенная модель: корпус компактнее, под окно симуляции 200px
const hullW = 120;
const hullH = 70;

export function initChassis(canvas) {
  tank.canvasWidth = canvas.width;
  tank.canvasHeight = canvas.height;

  tank.x = tank.canvasWidth * 0.5;
  tank.y = tank.canvasHeight * 0.5;

  tank.heading = -Math.PI / 2;

  if (tank.trackPhaseLeft === undefined) tank.trackPhaseLeft = 0;
  if (tank.trackPhaseRight === undefined) tank.trackPhaseRight = 0;
}

export function drawChassis(ctx) {
  const cx = tank.x;
  const cy = tank.y;

  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(tank.heading);

  ctx.fillStyle = "#111827";
  ctx.strokeStyle = "#4b5563";
  ctx.lineWidth = 2;

  ctx.beginPath();
  if (ctx.roundRect) {
    ctx.roundRect(-hullW / 2, -hullH / 2, hullW, hullH, 6);
  } else {
    ctx.rect(-hullW / 2, -hullH / 2, hullW, hullH);
  }
  ctx.fill();
  ctx.stroke();

  const cabW = 22;
  const cabH = 34;

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
    hullW / 2 - cabW + 3,
    -cabH / 2 + 3,
    cabW - 6,
    cabH - 8
  );

  const bedW = hullW * 0.55;
  const bedX = -hullW / 2;
  ctx.fillStyle = "#0b1120";
  ctx.fillRect(bedX, -hullH / 2 + 4, bedW, hullH - 8);

  const trackLen = hullW;
  const seg = 6;
  const phaseL = tank.trackPhaseLeft ?? 0;
  const phaseR = tank.trackPhaseRight ?? 0;

  ctx.strokeStyle = "#374151";
  ctx.lineWidth = 2;

  function drawTrack(y, phase) {
    ctx.beginPath();
    for (let x = -trackLen / 2; x < trackLen / 2; x += seg) {
      const xx = x + (phase % seg);
      ctx.moveTo(xx, y - 2);
      ctx.lineTo(xx, y + 2);
    }
    ctx.stroke();
  }

  const trackOffsetY = hullH / 2 + 3;
  drawTrack(-trackOffsetY, phaseL);
  drawTrack(trackOffsetY, phaseR);

  ctx.fillStyle = "#f97316";
  ctx.beginPath();
  const noseX = hullW / 2;
  ctx.moveTo(noseX + 5, 0);
  ctx.lineTo(noseX - 5, -7);
  ctx.lineTo(noseX - 5, 7);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

export function updateBase(dt) {
  const vCmd = tank.vLinearCmd;
  const wCmd = tank.vAngularCmdDeg * Math.PI / 180.0;

  tank.vLinear = vCmd;
  tank.vAngular = wCmd;

  tank.heading += wCmd * dt;

  // плечо базы меньше, чтобы анимация выглядела адекватно уменьшенному корпусу
  const B = 0.18;
  const vL = vCmd - wCmd * B;
  const vR = vCmd + wCmd * B;

  const k = 60;
  tank.trackPhaseLeft = (tank.trackPhaseLeft ?? 0) + vL * k * dt;
  tank.trackPhaseRight = (tank.trackPhaseRight ?? 0) + vR * k * dt;
}

