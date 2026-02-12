import { tank } from './robotState.js';
import { initChassis, drawChassis, updateBase } from './chassis.js';
import { initManipulator, drawManipulator } from './manipulator.js';
import { initUI, updateControls, updateDashboardFromState } from './uiControls.js';
import { initNetwork, pollStatus } from './network.js';

const canvas = document.getElementById('tankCanvas');
const ctx = canvas.getContext('2d');

initChassis(canvas);
initManipulator();
initUI();
initNetwork();        // ВАЖНО: привязать кнопку и т.п.
pollStatus();         // один раз запросить статус при старте

let lastTime = performance.now();

function loop(time) {
  const dt = (time - lastTime) / 1000.0;
  lastTime = time;

  updateBase(dt);
  updateControls(dt);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawChassis(ctx);
  drawManipulator(ctx);

  updateDashboardFromState();

  requestAnimationFrame(loop);
}

requestAnimationFrame(loop);
