// www/js/webrtc.js

(function () {
  const startBtn = document.getElementById('btnStartCam');
  const stopBtn = document.getElementById('btnStopCam');
  const localVideo = document.getElementById('localVideo');

  let localStream = null;

  async function startCamera() {
    if (localStream) {
      return;
    }

    try {
      // Базовая конфигурация видеопотока, как в типичных учебных примерах WebRTC:
      // 720p, 30 fps, без аудио.
      localStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 }
        },
        audio: false
      });

      localVideo.srcObject = localStream;

      startBtn.disabled = true;
      stopBtn.disabled = false;
    } catch (err) {
      console.error('Ошибка доступа к камере:', err);
      alert('Не удалось получить доступ к камере. Убедитесь, что страница открыта по HTTPS или на localhost и что в браузере выдано разрешение на камеру.');
    }
  }

  function stopCamera() {
    if (!localStream) {
      return;
    }

    localStream.getTracks().forEach(track => track.stop());
    localStream = null;
    localVideo.srcObject = null;

    startBtn.disabled = false;
    stopBtn.disabled = true;
  }

  if (startBtn && stopBtn && localVideo) {
    startBtn.addEventListener('click', startCamera);
    stopBtn.addEventListener('click', stopCamera);
  }
})();
