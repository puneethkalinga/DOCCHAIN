(() => {
  console.log("verify.js loaded");

  document.addEventListener("DOMContentLoaded", () => {
    const qs = (sel) => document.querySelector(sel);

    const API_BASE = window.location.origin;

    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get("token") || "";

    const loadingEl = qs("#loading");
    const resultBox = qs("#result");
    const qrUpload = qs("#qrUpload");

    const startCameraBtn = qs("#startCamera");
    const videoEl = qs("#video");

    async function doVerify(token) {
      if (!token) {
        loadingEl.innerText = "No verification token provided.";
        return;
      }

      loadingEl.innerText = "⏳ Verifying...";
      resultBox.classList.add("hidden");
      resultBox.innerHTML = "";

      try {
        const res = await fetch(`${API_BASE}/api/letters/verify/${encodeURIComponent(token)}`);
        if (!res.ok) throw new Error("Verify request failed");
        const data = await res.json();

        loadingEl.classList.add("hidden");
        resultBox.classList.remove("hidden");

        // Default metadata (always shown for active/expired/revoked)
        let details = `
          <p><strong>Letter ID:</strong> ${data.letter_id || "-"}</p>
          <p><strong>Sender:</strong> ${data.sender || "-"}</p>
          <p><strong>Created At:</strong> ${data.created_at ? new Date(data.created_at).toLocaleString() : "-"}</p>
          <p><strong>Expires At:</strong> ${data.expires_at ? new Date(data.expires_at).toLocaleString() : "-"}</p>
          <p><strong>Hash Prefix:</strong> ${data.hash_prefix || "-"}</p>
        `;

        // Status handling
        if (!data.valid) {
          if (data.status === "revoked") {
            resultBox.innerHTML = `<p class="status revoked">Letter has been revoked</p>` + details;
          } else if (data.status === "expired") {
            resultBox.innerHTML = `<p class="status expired">Letter has expired</p>` + details;
          } else {
            resultBox.innerHTML = `<p class="status invalid">Incorrect or wrong QR code</p>`;
          }
          return;
        }

        // Active letter (but no download link!)
        resultBox.innerHTML = `
          <p class="status active">ACTIVE</p>
          ${details}
        `;
      } catch (err) {
        console.error(err);
        loadingEl.classList.add("hidden");
        resultBox.classList.remove("hidden");
        resultBox.innerHTML = `<p class="status invalid">Verification failed. Try again later.</p>`;
      }
    }

    // Auto-verify if ?token=... is in URL
    if (tokenFromUrl) {
      doVerify(tokenFromUrl);
    }

    // QR upload handler
    qrUpload.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const img = new Image();
      img.src = URL.createObjectURL(file);
      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, canvas.width, canvas.height);
        if (code) {
          console.log("QR decoded:", code.data);
          const tokenMatch = code.data.match(/token=([^&]+)/);
          const extractedToken = tokenMatch ? tokenMatch[1] : code.data;
          doVerify(extractedToken);
        } else {
          resultBox.classList.remove("hidden");
          resultBox.innerHTML = `<p class="status invalid">Could not read QR from image.</p>`;
        }
      };
    });

    // Camera scan handler
    startCameraBtn.addEventListener("click", async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        videoEl.srcObject = stream;
        videoEl.classList.remove("hidden");

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        const scan = () => {
          if (videoEl.readyState === videoEl.HAVE_ENOUGH_DATA) {
            canvas.width = videoEl.videoWidth;
            canvas.height = videoEl.videoHeight;
            ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const code = jsQR(imageData.data, canvas.width, canvas.height);
            if (code) {
              console.log("QR decoded from camera:", code.data);
              const tokenMatch = code.data.match(/token=([^&]+)/);
              const extractedToken = tokenMatch ? tokenMatch[1] : code.data;
              doVerify(extractedToken);

              // stop camera after success
              stream.getTracks().forEach(track => track.stop());
              videoEl.classList.add("hidden");
              return;
            }
          }
          requestAnimationFrame(scan);
        };

        requestAnimationFrame(scan);
      } catch (err) {
        console.error("Camera error:", err);
        resultBox.classList.remove("hidden");
        resultBox.innerHTML = `<p class="status invalid">Camera not available or permission denied.</p>`;
      }
    });
  });
})();
