import { tank } from './robotState.js';
import { initChassis, drawChassis, updateBase } from './chassis.js';
import { initManipulator, drawManipulator } from './manipulator.js';
import { initUI, updateControls, updateDashboardFromState } from './uiControls.js';

const canvas = document.getElementById('tankCanvas');
const ctx = canvas.getContext('2d');

// инициализация состояния и UI
initChassis(canvas);
initManipulator();
initUI();

let lastTime = performance.now();

function loop(time) {
  const dt = (time - lastTime) / 1000.0;
  lastTime = time;

  // локальная симуляция базы и опрос геймпада
  updateBase(dt);
  updateControls(dt);

  // отрисовка
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawChassis(ctx);
  drawManipulator(ctx);

  // обновление числовых индикаторов
  updateDashboardFromState();

  requestAnimationFrame(loop);
}

requestAnimationFrame(loop);

