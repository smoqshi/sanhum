import { tank } from './robotState.js';

let canvasRef = null;

export function initManipulator() {
  // холст нам нужен из chassis.js через canvasRef,
  // здесь дополнительных инициализаций не требуется
}

export function drawManipulator(ctx) {
  if (!canvasRef) {
    // Попробуем взять тот же canvas, что и у шасси
    const c = document.getElementById('tankCanvas');
    if (!c) return;
    canvasRef = c;
  }

  const cx = canvasRef.width / 2;
  const cy = canvasRef.height / 2;

  ctx.save();

  // Совместная система координат с шасси:
  const yawRad = tank.yawDeg * Math.PI / 180.0;
  ctx.translate(cx, cy);
  ctx.rotate(yawRad);

  // Поворотная башня
  const turretRad = tank.turretAngle * Math.PI / 180.0;
  ctx.rotate(turretRad);

  const baseLen = 60;
  const baseWidth = 20;

  ctx.fillStyle = '#555';
  ctx.fillRect(0, -baseWidth / 2, baseLen, baseWidth);

  // Телескопическая часть (extension 0..1)
  const extLen = 80 * tank.armExtension;
  ctx.fillStyle = '#777';
  ctx.fillRect(baseLen, -baseWidth / 4, extLen, baseWidth / 2);

  // Захват (gripper 0..1)
  const gripOpen = 20 * tank.gripper + 5;
  ctx.fillStyle = '#999';
  const tipX = baseLen + extLen;
  ctx.fillRect(tipX, -gripOpen, 15, 4);
  ctx.fillRect(tipX, gripOpen - 4, 15, 4);

  ctx.restore();
}
