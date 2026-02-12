import { tank } from './robotState.js';

let canvasRef = null;

// Коэффициент масштаба «метры → пиксели».
// Подобран так, чтобы модель была умеренно маленькой и не ломала дизайн.
const METERS_TO_PIXELS = 80;

// Виртуальный центр сцены (0,0) смещаем в центр холста
// и вокруг него рисуем всё остальное.
export function initChassis(canvas) {
  canvasRef = canvas;
}

export function drawChassis(ctx) {
  if (!canvasRef) return;

  const canvas = canvasRef;
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;

  // Переводим физические координаты tank.x, tank.y в экранные.
  // При разумных значениях x,y (±2–3 м) робот остаётся в центральной области.
  const xPix = cx + tank.x * METERS_TO_PIXELS;
  const yPix = cy - tank.y * METERS_TO_PIXELS;

  // Размеры модели в «метрах» (условные)
  const robotLengthM = 0.7; // ~70 см
  const robotWidthM = 0.45; // ~45 см

  const robotLengthPx = robotLengthM * METERS_TO_PIXELS;
  const robotWidthPx = robotWidthM * METERS_TO_PIXELS;

  // Ограничим размер, чтобы не раздувать модель при больших масштабах
  const maxLen = Math.min(canvas.width, canvas.height) * 0.6;
  const scaleClamp = Math.min(1.0, maxLen / robotLengthPx);

  const L = robotLengthPx * scaleClamp;
  const W = robotWidthPx * scaleClamp;

  ctx.save();

  // Поворот по курсу робота
  const yawRad = tank.yawDeg * Math.PI / 180.0;
  ctx.translate(xPix, yPix);
  ctx.rotate(yawRad);

  // Корпус
  ctx.fillStyle = '#3f3f3f';
  ctx.strokeStyle = '#222';
  ctx.lineWidth = 2;
  ctx.fillRect(-L / 2, -W / 2, L, W);
  ctx.strokeRect(-L / 2, -W / 2, L, W);

  // Передняя часть (для направления)
  ctx.fillStyle = '#8c8c8c';
  const noseLen = L * 0.15;
  ctx.fillRect(L / 2 - noseLen, -W * 0.25, noseLen, W * 0.5);

  // Гусеницы/колёса
  ctx.fillStyle = '#222';
  const trackWidth = W * 0.25;
  ctx.fillRect(-L / 2, -W / 2 - trackWidth, L, trackWidth);
  ctx.fillRect(-L / 2, W / 2, L, trackWidth);

  ctx.restore();
}
