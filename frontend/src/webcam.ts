let webcamStream: MediaStream | null = null;
let webcamVideo: HTMLVideoElement | null = null;

export async function enableWebcam(): Promise<boolean> {
  if (webcamStream) return true;
  try {
    webcamStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720 },
      audio: false,
    });

    // Init persistent video element to keep the stream warm
    webcamVideo = document.createElement("video");
    webcamVideo.srcObject = webcamStream;
    webcamVideo.autoplay = true;
    webcamVideo.muted = true;
    webcamVideo.play().catch(e => console.warn("[VISION] Auto-play warning:", e));

    console.log("[VISION] Webcam activée");
    return true;
  } catch (e) {
    console.error("[VISION] Webcam refusée:", e);
    return false;
  }
}

export async function captureWebcamFrame(): Promise<string | null> {
  if (!webcamStream || !webcamVideo) {
    const ok = await enableWebcam();
    if (!ok) return null;
  }

  try {
    // Ensure video is playing and ready
    if (webcamVideo!.paused) {
      await webcamVideo!.play();
    }

    // Wait a tiny bit for the stream to be ready if it's the first time
    if (webcamVideo!.readyState < 2) {
      await new Promise(resolve => {
        webcamVideo!.onloadeddata = resolve;
        setTimeout(resolve, 500); // Timeout fallback
      });
    }

    const bitmap = await createImageBitmap(webcamVideo!);

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
  } catch (e) {
    console.error("[VISION] Capture error:", e);
    return null;
  }
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
