// =====================================
// assets/js/verifyWidget.js — Azure Live Version (Camera Auto-Stop)
// =====================================
(() => {
  const { qs, setHTML, toast } = window.ui || {};

  window.initVerifyWidget = function (container) {
    if (!container) return;

    // --- Inject widget HTML ---
    setHTML(
      container,
      `
      <div class="verify-box">
        <h3>Verify Letter</h3>
        <p id="verifyMsg">Scan a QR code using camera or upload an image.</p>

        <div class="verify-actions">
          <button id="btnStartCamera">Start Camera</button>
          <button id="btnStopCamera" style="display:none;background:#e74c3c;">Stop</button>
          <input type="file" id="qrUpload" accept="image/*" style="margin-left:10px;">
        </div>

        <video id="verifyVideo" autoplay muted playsinline style="display:none;width:100%;max-height:300px;border-radius:8px;margin-top:8px;"></video>
        <div id="verifyResult" style="margin-top:12px;"></div>
      </div>
      `
    );

    // --- Refs ---
    const btnStart = qs("#btnStartCamera", container);
    const btnStop = qs("#btnStopCamera", container);
    const upload = qs("#qrUpload", container);
    const video = qs("#verifyVideo", container);
    const resultBox = qs("#verifyResult", container);
    const msg = qs("#verifyMsg", container);

    // ✅ Use your deployed backend
    const API_BASE = window.location.origin;

    let stream = null;
    let stopRequested = false;

    // =====================================
    // ✅ Verify letter token
    // =====================================
    async function doVerify(token) {
      if (!token) return toast("No token found", "error");

      msg.textContent = "⏳ Verifying...";
      setHTML(resultBox, "");

      try {
        const res = await fetch(`${API_BASE}/api/letters/verify/${encodeURIComponent(token)}`);
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || "Invalid response");

        if (!data.valid) {
          const statusMap = {
            revoked: { color: "red", text: "Letter Revoked" },
            expired: { color: "orange", text: "Letter Expired" },
            invalid: { color: "gray", text: "Invalid Token" },
          };
          const info = statusMap[data.status] || statusMap.invalid;
          setHTML(resultBox, `<p style="color:${info.color};">${info.text}</p>`);
          toast(info.text, "error");
        } else {
          setHTML(
            resultBox,
            `
              <p style="color:green;font-weight:bold;">Active Letter</p>
              <p><b>ID:</b> ${data.letter_id}</p>
              <p><b>Sender:</b> ${data.sender}</p>
              <p><b>Expires:</b> ${new Date(data.expires_at).toLocaleString()}</p>
              <p><b>Hash:</b> ${data.hash_prefix}</p>
            `
          );
          toast("Verified successfully");
          stopCamera();
          // Auto-hide after 4 seconds
          setTimeout(() => (container.style.display = "none"), 4000);
        }
      } catch (err) {
        console.error("Verification error:", err);
        toast("Verification failed", "error");
        setHTML(resultBox, `<p style="color:red;">Verification failed. Try again.</p>`);
      }
    }

    // =====================================
    // 🖼️ Decode QR from uploaded image
    // =====================================
    upload.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return toast("No file selected", "error");

      const img = new Image();
      img.src = URL.createObjectURL(file);
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, canvas.width, canvas.height);
        if (code) {
          const tokenMatch = code.data.match(/token=([^&]+)/);
          const token = tokenMatch ? tokenMatch[1] : code.data;
          doVerify(token);
        } else {
          toast("Could not read QR image", "error");
          setHTML(resultBox, `<p style="color:red;">Could not read QR from image</p>`);
        }
      };
    });

    // =====================================
    // 🎥 Live Camera Scan (with 30s auto-stop)
    // =====================================
    btnStart.addEventListener("click", async () => {
      stopRequested = false;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        video.srcObject = stream;
        video.style.display = "block";
        btnStart.style.display = "none";
        btnStop.style.display = "inline-block";
        msg.textContent = "Scanning… Move QR code into view.";

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const startTime = Date.now();

        const scan = () => {
          if (stopRequested) return;
          if (Date.now() - startTime > 30000) {
            toast("No QR detected, stopping camera", "error");
            stopCamera();
            return;
          }
          if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const code = jsQR(imageData.data, canvas.width, canvas.height);
            if (code) {
              const tokenMatch = code.data.match(/token=([^&]+)/);
              const token = tokenMatch ? tokenMatch[1] : code.data;
              doVerify(token);
              stopCamera();
              return;
            }
          }
          requestAnimationFrame(scan);
        };
        requestAnimationFrame(scan);
      } catch (err) {
        console.error("Camera error:", err);
        toast("Camera not available", "error");
        setHTML(resultBox, `<p style="color:red;">Camera access denied or unavailable.</p>`);
      }
    });

    // =====================================
    // 🛑 Stop camera manually or auto
    // =====================================
    function stopCamera() {
      stopRequested = true;
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
        stream = null;
      }
      video.style.display = "none";
      btnStart.style.display = "inline-block";
      btnStop.style.display = "none";
      msg.textContent = "Scan a QR code using camera or upload an image.";
    }

    btnStop.addEventListener("click", stopCamera);
  };

  console.log("verifyWidget.js (Azure Live) loaded");
})();
