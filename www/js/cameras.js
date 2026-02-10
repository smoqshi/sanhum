// js/cameras.js

// настроить URL под свои топики/хост
const STEREO_URL = "/stream?topic=/stereo/left/image_raw";
const CSI_URL    = "/stream?topic=/csi/image_raw";

function initCameras() {
    const stereoImg = document.getElementById("stereoCameraImg");
    const csiImg    = document.getElementById("csiCameraImg");

    const stereoStatus = document.getElementById("stereoCameraStatus");
    const csiStatus    = document.getElementById("csiCameraStatus");

    if (stereoImg) {
        stereoImg.src = STEREO_URL;
        stereoImg.onload = () => {
            if (stereoStatus) stereoStatus.textContent = "Stereo: streaming";
        };
        stereoImg.onerror = () => {
            if (stereoStatus) stereoStatus.textContent = "Stereo: error";
        };
    }

    if (csiImg) {
        csiImg.src = CSI_URL;
        csiImg.onload = () => {
            if (csiStatus) csiStatus.textContent = "CSI: streaming";
        };
        csiImg.onerror = () => {
            if (csiStatus) csiStatus.textContent = "CSI: error";
        };
    }
}

window.addEventListener("load", initCameras);
