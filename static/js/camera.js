const video = document.getElementById('video');
const result = document.getElementById('result');

// Kamerayı başlat
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        console.error("Kamera açılmadı:", err);
    });

function captureAndSend() {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL('image/jpeg');

    fetch('/verify_face', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: dataUrl })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            result.innerText = `Giriş başarılı! Hoş geldin, ${data.name}`;
            window.location.href = "/dashboard";
        } else {
            result.innerText = `Hata: ${data.message}`;
        }
    })
    .catch(error => {
        console.error("Sunucu hatası:", error);
        result.innerText = "Sunucuya bağlanılamadı.";
    });
}
