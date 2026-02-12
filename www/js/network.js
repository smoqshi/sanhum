import { tank } from './robotState.js';

export function initNetwork() {
    const btn = document.getElementById('btnRefreshStatus');
    if (btn) {
        btn.addEventListener('click', () => {
            pollStatus();
        });
    }

    const stereoImg = document.getElementById('stereoVideo');
    const stereoNoSig = document.getElementById('stereoNoSignal');
    if (stereoImg && stereoNoSig) {
        stereoImg.addEventListener('error', () => {
            stereoNoSig.style.display = 'block';
        });
        stereoImg.addEventListener('load', () => {
            stereoNoSig.style.display = 'none';
        });
    }

    const csiImg = document.getElementById('csiVideo');
    const csiNoSig = document.getElementById('csiNoSignal');
    if (csiImg && csiNoSig) {
        csiImg.addEventListener('error', () => {
            csiNoSig.style.display = 'block';
        });
        csiImg.addEventListener('load', () => {
            csiNoSig.style.display = 'none';
        });
    }
}

export async function pollStatus() {
    try {
        const r = await fetch('/api/status');
        if (!r.ok) return;
        const d = await r.json();

        const wifiSsid = document.getElementById('statusWifiSsid');
        const wifiRssi = document.getElementById('statusWifiRssi');
        if (wifiSsid) {
            wifiSsid.textContent = (d.wifi_ssid ?? '--').toString();
        }
        if (wifiRssi) {
            const rssi = d.wifi_rssi_dbm;
            wifiRssi.textContent = (rssi !== undefined && rssi !== null) ? `${rssi} dBm` : '-- dBm';
        }

        const cpuTemp = document.getElementById('statusCpuTemp');
        const cpuLoad = document.getElementById('statusCpuLoad');
        const boardTemp = document.getElementById('statusBoardTemp');
        if (cpuTemp) {
            const v = d.cpu_temp_c;
            cpuTemp.textContent = (v !== undefined && v !== null) ? `${v} °C` : '-- °C';
        }
        if (cpuLoad) {
            const v = d.cpu_load_percent;
            cpuLoad.textContent = (v !== undefined && v !== null) ? `${v} %` : '-- %';
        }
        if (boardTemp) {
            const v = d.board_temp_c;
            boardTemp.textContent = (v !== undefined && v !== null) ? `${v} °C` : '-- °C';
        }

        const battery = document.getElementById('statusBattery');
        const currentTotal = document.getElementById('statusCurrentTotal');
        const current5V = document.getElementById('statusCurrent5V');
        const current12V = document.getElementById('statusCurrent12V');
        const currentMotors = document.getElementById('statusCurrentMotors');
        const currentGpio = document.getElementById('statusCurrentGpio');

        if (battery) {
            const v = d.battery_v;
            battery.textContent = (v !== undefined && v !== null) ? `${v} V` : '-- V';
        }
        if (currentTotal) {
            const v = d.current_total_a;
            currentTotal.textContent = (v !== undefined && v !== null) ? `${v} A` : '-- A';
        }
        if (current5V) {
            const v = d.current_5v_a;
            current5V.textContent = (v !== undefined && v !== null) ? `${v} A` : '-- A';
        }
        if (current12V) {
            const v = d.current_12v_a;
            current12V.textContent = (v !== undefined && v !== null) ? `${v} A` : '-- A';
        }
        if (currentMotors) {
            const v = d.current_motors_a;
            currentMotors.textContent = (v !== undefined && v !== null) ? `${v} A` : '-- A';
        }
        if (currentGpio) {
            const v = d.current_gpio_ma;
            currentGpio.textContent = (v !== undefined && v !== null) ? `${v} mA` : '-- mA';
        }
    } catch (e) {
        console.error('pollStatus error', e);
    }
}

export async function sendBaseCommand(vLinear, vAngular, emergency = false) {
    try {
        const payload = emergency ? { emergency: true } : { vLinear, vAngular };
        await fetch('/api/base', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } catch (e) {
        console.error('sendBaseCommand error', e);
    }
}

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

export async function pollJointState() {
    try {
        const r = await fetch('/api/joint_state');
        if (!r.ok) return;
        const d = await r.json();

        if (d.arm) {
            tank.q2 = d.arm.q2 ?? tank.q2;
            tank.q3 = d.arm.q3 ?? tank.q3;
            tank.q4 = d.arm.q4 ?? tank.q4;
            tank.gripper = d.arm.gripper ?? tank.gripper;
            tank.turretAngle = d.arm.turret ?? tank.turretAngle;
        }
    } catch (e) {
        console.error('pollJointState error', e);
    }
}


