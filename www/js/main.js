import { tank } from './robotState.js';
import { initChassis, drawChassis, updateBase } from './chassis.js';
import { drawManipulator } from './manipulator.js';
import {
  initUIControls,
  updateControls,
  updateDashboardFromState
} from './uiControls.js';

const canvas = document.getElementById('tankCanvas');
const ctx = canvas.getContext('2d');

initChassis(canvas);
initUIControls();

let lastTime = performance.now();

function loop(time) {
  const dt = (time - lastTime) / 1000.0;
  lastTime = time;

  // Локальная симуляция (если включена)
  updateBase(dt);
  updateControls(dt);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawChassis(ctx);
  drawManipulator(ctx, tank);

  updateDashboardFromState();

  requestAnimationFrame(loop);
}

requestAnimationFrame(loop);

