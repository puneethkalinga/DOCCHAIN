(() => {
  const { toast, setHTML } = window.ui;
  const { fetchJSON } = window.api;
  const { me, clear } = window.auth;
  const C = window.DOCCHAIN_CONFIG || { PAGE_SIZE: 20 };

  // ✅ Use your live backend base URL
  const BASE = window.location.origin;

  const spinner = document.getElementById("spinner");
  const showSpinner = () => spinner.classList.remove("hidden");
  const hideSpinner = () => spinner.classList.add("hidden");

  function badge(status) {
    const cls =
      status === "active" ? "badge active" :
      status === "revoked" ? "badge revoked" :
      "badge expired";
    return `<span class="${cls}">${status}</span>`;
  }

  function getExpiryDate() {
    const sel = document.getElementById("expires_at").value;
    if (sel === "custom") {
      const customDate = document.getElementById("custom_expiry").value;
      if (!customDate) {
        alert("Please pick a custom expiry date");
        return null;
      }
      return new Date(customDate).toISOString();
    } else {
      const days = parseInt(sel, 10);
      const now = new Date();
      now.setDate(now.getDate() + days);
      return now.toISOString();
    }
  }

  // -----------------------------
  // Render letters table
  // -----------------------------
  async function renderTable(page = 1, filters = {}) {
    showSpinner();
    try {
      const params = new URLSearchParams({
        page,
        page_size: C.PAGE_SIZE,
      });

      if (filters.q) params.append("q", filters.q);
      if (filters.status) params.append("status", filters.status);
      if (filters.uploaded_after) params.append("uploaded_after", filters.uploaded_after);
      if (filters.uploaded_before) params.append("uploaded_before", filters.uploaded_before);

      const data = await fetchJSON(`/letters?${params.toString()}`, { auth: true });
      const rows = Array.isArray(data.items) ? data.items : [];
      const pages = data.pages ?? 1;

      const tbody = rows.map(
        (r) => `
        <tr data-id="${r.id}">
          <td>${r.id}</td>
          <td>${r.file_name || ""}</td>
          <td>${badge(r.status)}</td>
          <td>${r.hash_prefix || ""}…</td>
          <td>${r.created_at ? new Date(r.created_at).toLocaleString() : ""}</td>
          <td>${r.expires_at ? new Date(r.expires_at).toLocaleString() : "—"}</td>
          <td>${r.status === "active" ? `<button class="revoke">Revoke</button>` : ``}</td>
        </tr>`
      ).join("");

      const html = `
        <table>
          <thead><tr>
            <th>ID</th><th>File</th><th>Status</th><th>Hash</th>
            <th>Created</th><th>Expires</th><th>Actions</th>
          </tr></thead>
          <tbody>${tbody || `<tr><td colspan="7">No letters</td></tr>`}</tbody>
        </table>`;
      setHTML(document.getElementById("lettersTable"), html);
      document.getElementById("pageInfo").textContent = `Page ${page}${pages ? ` / ${pages}` : ""}`;

      // revoke buttons
      document.querySelectorAll("#lettersTable .revoke").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          const id = e.target.closest("tr").dataset.id;
          showSpinner();
          try {
            await fetchJSON(`/letters/${id}/revoke`, { method: "PATCH", auth: true });
            toast("Revoked successfully");
            await renderTable(page, filters);
          } catch (err) {
            toast(err.message);
          } finally {
            hideSpinner();
          }
        });
      });

      // pagination
      document.getElementById("prevPage").onclick = () => {
        if (page > 1) renderTable(page - 1, filters);
      };
      document.getElementById("nextPage").onclick = () => {
        if (page < pages) renderTable(page + 1, filters);
      };
    } catch (e) {
      setHTML(document.getElementById("lettersTable"), `Error loading letters: ${e.message}`);
    } finally {
      hideSpinner();
    }
  }

  // -----------------------------
  // Upload letter (multi-recipient)
  // -----------------------------
  async function upload() {
    const recipientRaw = document.getElementById("recipient").value.trim();
    const note = document.getElementById("note").value.trim();
    const file = document.getElementById("file").files[0];
    if (!file) return toast("Choose a PDF first.");

    const fd = new FormData();
    fd.append("file", file);

    if (recipientRaw) {
      const recipients = recipientRaw.split(/[,;\n]+/).map(r => r.trim()).filter(Boolean);
      if (recipients.length > 1) {
        fd.append("recipient_emails", JSON.stringify(recipients));
      } else if (recipients.length === 1) {
        fd.append("recipient_email", recipients[0]);
      }
    }

    if (note) fd.append("note", note);

    const exp = getExpiryDate();
    if (!exp) return;
    fd.append("expires_at", exp);

    showSpinner();
    try {
      await fetchJSON("/letters", { method: "POST", auth: true, form: true, body: fd });
      toast("Letter uploaded successfully");
      await renderTable(1);
    } catch (e) {
      toast(e.message || "Upload failed");
    } finally {
      hideSpinner();
    }
  }

  // -----------------------------
  // Init
  // -----------------------------
  document.addEventListener("DOMContentLoaded", async () => {
    try {
      const u = await me();
      document.getElementById("whoami").textContent = `${u.email} · role: ${u.role}`;
    } catch {
      toast("Not logged in");
      window.location.href = "login.html";
      return;
    }

    // expiry selector toggle
    const expSel = document.getElementById("expires_at");
    const customField = document.getElementById("custom_expiry");
    expSel.addEventListener("change", (e) => {
      if (e.target.value === "custom") {
        customField.style.display = "inline-block";
        customField.focus();
      } else {
        customField.style.display = "none";
        customField.value = "";
      }
    });

    document.getElementById("btnUpload").addEventListener("click", upload);
    document.getElementById("btnLogout").addEventListener("click", () => {
      clear();
      window.location.href = "login.html";
    });

    // 🔹 search filters
    document.getElementById("btnSearch").addEventListener("click", () => {
      const q = document.getElementById("searchBox").value.trim();
      const status = document.getElementById("statusFilter").value;
      const from = document.getElementById("dateFrom").value;
      const to = document.getElementById("dateTo").value;

      const filters = {};
      if (q) filters.q = q;
      if (status) filters.status = status;
      if (from) filters.uploaded_after = from;
      if (to) filters.uploaded_before = to;

      renderTable(1, filters);
    });

    document.getElementById("btnReset").addEventListener("click", () => {
      document.getElementById("searchBox").value = "";
      document.getElementById("statusFilter").value = "";
      document.getElementById("dateFrom").value = "";
      document.getElementById("dateTo").value = "";
      renderTable(1);
    });

    renderTable(1);
  });
})();
