import { tank } from './robotState.js';

export function initNetwork() {
  const btn = document.getElementById('btnRefreshStatus');
  if (btn) {
    btn.addEventListener('click', () => {
      pollStatus();
    });
  }

  // Периодический опрос статуса и суставов для симуляции
  setInterval(() => {
    pollStatus();
    pollJointState();
  }, 500);
}

// ===== /api/status =====

export async function pollStatus() {
  try {
    const r = await fetch('/api/status');
    if (!r.ok) return;
    const d = await r.json();

    // ... существующие обновления Wi‑Fi, батареи и т.п. ...

    // позиция / ориентация
    if (typeof d.x === 'number') {
      tank.x = d.x;
    }
    if (typeof d.y === 'number') {
      tank.y = d.y;
    }
    if (typeof d.theta_deg === 'number') {
      tank.yawDeg = d.theta_deg;
    }

    // скорости для панели
    if (typeof d.v_linear === 'number') {
      tank.vLinear = d.v_linear;
    }
    if (typeof d.v_angular_deg === 'number') {
      tank.vAngularDeg = d.v_angular_deg;
    }

    if (typeof d.emergency === 'boolean') {
      tank.emergency = d.emergency;
    }
  } catch (e) {
    console.error('pollStatus error', e);
  }
}


// ===== /api/base =====

export async function sendBaseCommand(vLinear, vAngular, emergency = false) {
  try {
    const payload = emergency
      ? { emergency: true }
      : { vLinear, vAngular };

    await fetch('/api/base', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  } catch (e) {
    console.error('sendBaseCommand error', e);
  }
}

// ===== /api/arm =====

export async function sendArmCommand(extend, gripper, turretAngle) {
  try {
    await fetch('/api/arm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ extend, gripper, turretAngle })
    });
  } catch (e) {
    console.error('sendArmCommand error', e);
  }
}

// ===== /api/joint_state =====

export async function pollJointState() {
  try {
    const r = await fetch('/api/joint_state');
    if (!r.ok) {
      console.warn('pollJointState: HTTP', r.status);
      return;
    }
    const d = await r.json();

    if (typeof d.turret_deg === 'number') {
      tank.turretAngle = d.turret_deg;
    }
    if (typeof d.arm_ext === 'number') {
      tank.armExtension = d.arm_ext;
    }
    if (typeof d.gripper === 'number') {
      tank.gripper = d.gripper;
    }
  } catch (e) {
    console.error('pollJointState error', e);
  }
}

