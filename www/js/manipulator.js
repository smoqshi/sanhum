import { tank } from './robotState.js';

let canvasRef = null;
const METERS_TO_PIXELS = 80;

export function initManipulator(canvas) {
  canvasRef = canvas;
}

export function drawManipulator(ctx) {
  if (!canvasRef) return;

  const canvas = canvasRef;
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;

  // Позиция базы
  const baseX = cx + tank.x * METERS_TO_PIXELS;
  const baseY = cy - tank.y * METERS_TO_PIXELS;

  ctx.save();

  // Общий поворот по курсу робота
  const yawRad = tank.yawDeg * Math.PI / 180.0;
  ctx.translate(baseX, baseY);
  ctx.rotate(yawRad);

  // Поворот башни относительно корпуса
  const turretRad = tank.turretAngle * Math.PI / 180.0;
  ctx.rotate(turretRad);

  // Геометрия манипулятора относительно корпуса в пикселях
  const baseLenPx = 0.35 * METERS_TO_PIXELS;   // основание
  const baseWidthPx = 0.12 * METERS_TO_PIXELS;

  ctx.fillStyle = '#555';
  ctx.fillRect(0, -baseWidthPx / 2, baseLenPx, baseWidthPx);

  // Телескопическая часть (extension 0..1)
  const maxExtLenPx = 0.5 * METERS_TO_PIXELS;
  const extLenPx = maxExtLenPx * tank.armExtension;

  ctx.fillStyle = '#777';
  ctx.fillRect(baseLenPx, -baseWidthPx / 4, extLenPx, baseWidthPx / 2);

  // Захват
  const gripBaseOpen = 0.04 * METERS_TO_PIXELS;
  const gripExtraOpen = 0.06 * METERS_TO_PIXELS * tank.gripper;
  const gripOpen = gripBaseOpen + gripExtraOpen;

  ctx.fillStyle = '#999';
  const tipX = baseLenPx + extLenPx;
  const fingerLen = 0.12 * METERS_TO_PIXELS;
  const fingerThick = 0.02 * METERS_TO_PIXELS;

  ctx.fillRect(tipX, -gripOpen, fingerLen, fingerThick);
  ctx.fillRect(tipX, gripOpen - fingerThick, fingerLen, fingerThick);

  ctx.restore();
}

