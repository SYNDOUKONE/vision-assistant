let webcamStream: MediaStream | null = null;

export async function enableWebcam(): Promise<boolean> {
  if (webcamStream) return true;
  try {
    webcamStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720 },
      audio: false,
    });
    console.log("[VISION] Webcam activée");
    return true;
  } catch (e) {
    console.error("[VISION] Webcam refusée:", e);
    return false;
  }
}

export async function captureWebcamFrame(): Promise<string | null> {
  if (!webcamStream) {
    const ok = await enableWebcam();
    if (!ok) return null;
  }

  const video = document.createElement("video");
  video.srcObject = webcamStream;
  await video.play();

  // Create bitmap
  const bitmap = await createImageBitmap(video);
  video.pause();

  const maxW = 1280;
  const ratio = bitmap.width > maxW ? maxW / bitmap.width : 1;
  const w = Math.round(bitmap.width * ratio);
  const h = Math.round(bitmap.height * ratio);

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(bitmap, 0, 0, w, h);
  
  return canvas.toDataURL("image/jpeg", 0.8).split(",")[1];
}

export function injectWebcamButton() {
  const btn = document.createElement("button");
  btn.id = "webcam-button";
  btn.textContent = "📷 Activer Caméra";
  btn.style.cssText =
    "position:fixed;bottom:18px;left:180px;z-index:9999;padding:8px 14px;" +
    "background:rgba(76, 168, 232, 0.12);color:rgba(255,255,255,0.4);border:1px solid rgba(76, 168, 232, 0.2);border-radius:20px;" +
    "font-family:sans-serif;cursor:pointer;font-size:11px;letter-spacing:1px;text-transform:lowercase;backdrop-filter:blur(10px);transition:all 0.3s ease;";
  
  btn.onmouseover = () => { btn.style.background = "rgba(76, 168, 232, 0.3)"; btn.style.color = "#fff"; };
  btn.onmouseout  = () => { btn.style.background = "rgba(76, 168, 232, 0.12)"; btn.style.color = "rgba(255,255,255,0.4)"; };
  
  btn.onclick = async () => {
    const ok = await enableWebcam();
    btn.textContent = ok ? "📷 Caméra Active" : "❌ Caméra Refusée";
    btn.style.background = ok ? "rgba(46, 204, 113, 0.2)" : "rgba(231, 76, 60, 0.2)";
  };
  document.body.appendChild(btn);
}
