import { tank } from './robotState.js';

// корпус, кабина спереди, платформа сзади
// размеры согласованы с манипулятором (см. manipulator.js)
const hullW = 160;
const hullH = 100;

export function initChassis(canvas) {
  tank.canvasWidth = canvas.width;
  tank.canvasHeight = canvas.height;

  // Центр симуляции — центр холста
  tank.x = tank.canvasWidth * 0.5;
  tank.y = tank.canvasHeight * 0.5;

  // Повернём робота носом вверх (нос вдоль +X, heading = -90°)
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

  // корпус
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

  // кабина спереди (по +X)
  const cabW = 28;
  const cabH = 44;

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

  // задняя платформа под манипулятор
  const bedW = hullW * 0.55;
  const bedX = -hullW / 2;
  ctx.fillStyle = "#0b1120";
  ctx.fillRect(bedX, -hullH / 2 + 4, bedW, hullH - 8);

  // гусеницы вдоль корпуса
  const trackLen = hullW;
  const seg = 8;
  const phaseL = tank.trackPhaseLeft ?? 0;
  const phaseR = tank.trackPhaseRight ?? 0;

  ctx.strokeStyle = "#374151";
  ctx.lineWidth = 2;

  function drawTrack(y, phase) {
    ctx.beginPath();
    for (let x = -trackLen / 2; x < trackLen / 2; x += seg) {
      const xx = x + (phase % seg);
      ctx.moveTo(xx, y - 3);
      ctx.lineTo(xx, y + 3);
    }
    ctx.stroke();
  }

  const trackOffsetY = hullH / 2 + 3;
  drawTrack(-trackOffsetY, phaseL); // левая
  drawTrack(trackOffsetY, phaseR);  // правая

  // стрелка носа
  ctx.fillStyle = "#f97316";
  ctx.beginPath();
  const noseX = hullW / 2;
  ctx.moveTo(noseX + 6, 0);
  ctx.lineTo(noseX - 6, -8);
  ctx.lineTo(noseX - 6, 8);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

export function updateBase(dt) {
  // используем команды, а не прошлое состояние,
  // чтобы анимация гусениц соответствовала input'у
  const vCmd = tank.vLinearCmd;                 // м/с
  const wCmd = tank.vAngularCmdDeg * Math.PI / 180.0; // рад/с

  tank.vLinear = vCmd;
  tank.vAngular = wCmd;

  // вращение вокруг центра (без смещения x/y)
  tank.heading += wCmd * dt;

  // фазовая скорость для гусениц:
  // vL = v - w*B, vR = v + w*B
  const B = 0.25; // "плечо" базы
  const vL = vCmd - wCmd * B;
  const vR = vCmd + wCmd * B;

  // увеличим коэффициент, чтобы при развороте на месте
  // траки визуально быстро крутились
  const k = 80;
  tank.trackPhaseLeft = (tank.trackPhaseLeft ?? 0) + vL * k * dt;
  tank.trackPhaseRight = (tank.trackPhaseRight ?? 0) + vR * k * dt;
}

