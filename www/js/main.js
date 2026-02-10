import { initNetwork, pollStatus } from './network.js';
import { initChassis, drawChassis, updateBase } from './chassis.js';
import { initManipulator, drawManipulator } from './manipulator.js';
import { initUI, updateControls } from './uiControls.js';

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
    setInterval(pollStatus, 500);
}

function loop(timestamp) {
    const dt = (timestamp - lastTime) / 1000;
    lastTime = timestamp;

    updateControls(dt);
    updateBase(dt);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawChassis(ctx);
    drawManipulator(ctx);

    requestAnimationFrame(loop);
}

window.addEventListener('load', init);
