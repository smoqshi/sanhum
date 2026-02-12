import { tank } from './robotState.js';

let canvasRef = null;

export function initChassis(canvas) {
  canvasRef = canvas;
}

// Рисуем шасси всегда в геометрическом центре холста
export function drawChassis(ctx) {
  if (!canvasRef) return;

  const cx = canvasRef.width / 2;
  const cy = canvasRef.height / 2;

  const robotWidth = 120;
  const robotLength = 180;

  ctx.save();

  // Ориентация робота по yaw, но центр всегда один и тот же
  const yawRad = tank.yawDeg * Math.PI / 180.0;
  ctx.translate(cx, cy);
  ctx.rotate(yawRad);

  // Корпус
  ctx.fillStyle = '#444';
  ctx.fillRect(-robotLength / 2, -robotWidth / 2, robotLength, robotWidth);

  // «Лицо» робота (перед)
  ctx.fillStyle = '#888';
  ctx.fillRect(robotLength / 2 - 10, -robotWidth / 4, 10, robotWidth / 2);

  // Гусеницы/колёса
  ctx.fillStyle = '#222';
  const trackWidth = 20;
  ctx.fillRect(-robotLength / 2, -robotWidth / 2 - trackWidth, robotLength, trackWidth);
  ctx.fillRect(-robotLength / 2, robotWidth / 2, robotLength, trackWidth);

  ctx.restore();
}
