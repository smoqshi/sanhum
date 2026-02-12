import { initNetwork, pollStatus, pollJointState } from './network.js';
import { initChassis, drawChassis, updateBase } from './chassis.js';
import { initManipulator, drawManipulator } from './manipulator.js';
import { initUI, updateControls, updateDashboardFromState } from './uiControls.js';

let canvas, ctx;
let lastTime = 0;

function init() {
    canvas = document.getElementById('tankCanvas');
    if (!canvas) {
        console.error('Canvas with id "tankCanvas" not found');
        return;
    }
    ctx = canvas.getContext('2d');

    initChassis(canvas);
    initManipulator();
    initNetwork();
    initUI();

    requestAnimationFrame(loop);

    // периодический опрос статуса и суставов
    setInterval(pollStatus, 500);
    setInterval(pollJointState, 200);
}

function loop(timestamp) {
    const dt = (timestamp - lastTime) / 1000;
    lastTime = timestamp;

    updateControls(dt);        // обновление команд оператора
    updateBase(dt);            // интеграция движения базы

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawChassis(ctx);          // отрисовка корпуса
    drawManipulator(ctx);      // отрисовка манипулятора

    updateDashboardFromState(); // обновление правого блока

    requestAnimationFrame(loop);
}

window.addEventListener('load', init);
