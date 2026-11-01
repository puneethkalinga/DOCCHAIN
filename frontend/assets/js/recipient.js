(() => {
  const { qs, setHTML, toast, on } = window.ui;
  const { me, clear } = window.auth;

  // ✅ Use your deployed backend URL
  const BASE = window.location.origin;

  // ============================
  // Helper: Badge Colors
  // ============================
  function badge(status) {
    if (status === "active") return `<span class="badge active">Active</span>`;
    if (status === "revoked") return `<span class="badge revoked">Revoked</span>`;
    if (status === "expired") return `<span class="badge expired">Expired</span>`;
    return `<span class="badge">${status}</span>`;
  }

  // ============================
  // Load letters with filters
  // ============================
  async function loadLetters(params = {}) {
    try {
      const token = localStorage.getItem("docchain_token");
      if (!token) throw new Error("Not logged in");

      const qsParams = new URLSearchParams(params);
      const url = `${BASE}/api/recipients/me/letters?${qsParams.toString()}`;

      const res = await fetch(url, { headers: { Authorization: "Bearer " + token } });
      if (!res.ok) throw new Error("Failed to fetch letters");

      const data = await res.json();
      const items = data.items || [];

      if (!items.length) {
        setHTML(qs("#lettersTable"), `<p>No letters found.</p>`);
        return;
      }

      // Inline expiry enforcement
      const now = new Date();
      for (const r of items) {
        if (r.expires_at && new Date(r.expires_at) < now && r.status === "active") {
          r.status = "expired";
        }
      }

      const rows = items.map((r) => `
        <tr>
          <td style="word-break:break-all">${r.id}</td>
          <td>${r.file_name}</td>
          <td>${badge(r.status)}</td>
          <td>${r.hash_prefix || ""}…</td>
          <td>${r.uploaded_at ? new Date(r.uploaded_at).toLocaleString() : ""}</td>
          <td>${r.expires_at ? new Date(r.expires_at).toLocaleString() : ""}</td>
          <td>
            ${
              r.status === "active"
                ? `
                <button onclick="downloadLetter('${r.id}','${r.file_name}')">Download</button>
                <button onclick="previewLetter('${r.id}')">Preview</button>
              `
                : `<span style="color:#888">Unavailable</span>`
            }
          </td>
        </tr>
      `).join("");

      setHTML(qs("#lettersTable"), `
        <div style="overflow:auto">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>File</th>
                <th>Status</th>
                <th>Hash</th>
                <th>Uploaded</th>
                <th>Expires</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `);
    } catch (e) {
      console.error(e);
      setHTML(qs("#lettersTable"), `<p style="color:#f43f5e">Error: ${e.message}</p>`);
    }
  }

  // ============================
  // Download a single letter
  // ============================
  window.downloadLetter = async function (letterId, fileName = "document.pdf") {
    const token = localStorage.getItem("docchain_token");
    if (!token) return alert("Not logged in.");

    const res = await fetch(`${BASE}/api/letters/${letterId}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return alert("Download failed: " + res.status);

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  // ============================
  // Preview a single letter
  // ============================
  window.previewLetter = async function (letterId) {
    const token = localStorage.getItem("docchain_token");
    if (!token) return alert("Not logged in.");

    const modal = document.getElementById("previewModal");
    const spinner = document.getElementById("spinner");
    const previewText = document.getElementById("previewText");

    previewText.textContent = "";
    spinner.classList.remove("hidden");
    modal.classList.remove("hidden");

    try {
      const res = await fetch(`${BASE}/api/letters/${letterId}/preview`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        spinner.classList.add("hidden");
        alert("Preview failed: " + res.status);
        return;
      }
      const data = await res.json();
      previewText.textContent = data.preview;
    } catch (e) {
      console.error(e);
      alert("Preview failed: " + e.message);
    } finally {
      spinner.classList.add("hidden");
    }
  };

  // ============================
  // Download all letters (active only)
  // ============================
  async function downloadAllLetters() {
    const token = localStorage.getItem("docchain_token");
    if (!token) return alert("Not logged in.");

    try {
      const res = await fetch(`${BASE}/api/recipients/me/letters`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch letters");
      const data = await res.json();
      const items = data.items || [];
      if (!items.length) return alert("No letters to download.");

      const now = new Date();
      for (const r of items) {
        if (r.expires_at && new Date(r.expires_at) < now && r.status === "active") r.status = "expired";
        if (r.status !== "active") continue;

        const dl = await fetch(`${BASE}/api/letters/${r.id}/download`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!dl.ok) continue;

        const blob = await dl.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = r.file_name || `${r.id}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      }

      toast("All active letters downloaded.");
    } catch (e) {
      console.error(e);
      alert("Download all failed: " + e.message);
    }
  }

  // ============================
  // Init
  // ============================
  document.addEventListener("DOMContentLoaded", async () => {
    try {
      const u = await me();
      if (!u || u.role !== "recipient") {
        toast("Please log in as a recipient");
        window.location.href = "login.html";
        return;
      }
      qs("#whoami").textContent = `${u.email} · role: ${u.role}`;
    } catch (e) {
      toast("Not logged in");
      window.location.href = "login.html";
      return;
    }

    // Logout
    on(qs("#btnLogout"), "click", () => {
      clear();
      window.location.href = "login.html";
    });

    // Search + reset
    on(qs("#btnSearch"), "click", () => {
      const q = qs("#searchBox").value.trim();
      const status = qs("#statusFilter").value;
      let params = {};
      if (q) params.q = q;
      if (status) params.status = status;
      loadLetters(params);
    });

    on(qs("#btnReset"), "click", () => {
      qs("#searchBox").value = "";
      qs("#statusFilter").value = "";
      loadLetters();
    });

    // Download all
    const dlAll = qs("#btnDownloadAll");
    if (dlAll) on(dlAll, "click", downloadAllLetters);

    // Modal close
    const modal = document.getElementById("previewModal");
    const closeBtn = document.getElementById("closePreview");
    if (closeBtn) closeBtn.addEventListener("click", () => modal.classList.add("hidden"));
    if (modal) modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.add("hidden");
    });

    await loadLetters();
  });
})();
