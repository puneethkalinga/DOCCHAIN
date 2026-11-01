(() => {
  const { fetchJSON } = window.api;
  const { toast, setHTML } = window.ui;
  const { me, clear } = window.auth;
  const C = window.DOCCHAIN_CONFIG || { PAGE_SIZE: 20 };

  const spinner = document.getElementById("spinner");
  function showSpinner() { spinner?.classList.remove("hidden"); }
  function hideSpinner() { spinner?.classList.add("hidden"); }

  // State
  let usersPage = 1, logsPage = 1;
  let userSearch = "";

  // =============================
  // Load Users
  // =============================
  async function loadUsers() {
    showSpinner();
    try {
      const res = await fetchJSON(
        `/admin/users?page=${usersPage}&q=${encodeURIComponent(userSearch)}&page_size=${C.PAGE_SIZE}`
      );

      const rows = res.items.map(u => {
        const revoked = !u.is_active;
        return `
          <tr class="${revoked ? "revoked-row" : ""}">
            <td>${u.email} ${revoked ? `<span class="badge revoked">Revoked</span>` : ""}</td>
            <td>
              <select data-id="${u.id}" class="roleSelect" ${revoked ? "disabled" : ""}>
                <option value="admin" ${u.role === "admin" ? "selected" : ""}>Admin</option>
                <option value="staff" ${u.role === "staff" ? "selected" : ""}>Staff</option>
                <option value="recipient" ${u.role === "recipient" ? "selected" : ""}>Recipient</option>
              </select>
            </td>
            <td>
              <input type="checkbox" data-id="${u.id}" class="uploadToggle"
                ${u.upload_enabled ? "checked" : ""} ${revoked ? "disabled" : ""}/>
            </td>
            <td>
              ${revoked
                ? `<button class="unrevokeBtn" data-id="${u.id}">Restore</button>`
                : `<button class="revokeBtn" data-id="${u.id}">Revoke</button>`}
            </td>
          </tr>
        `;
      }).join("");

      setHTML("#usersTable", `
        <table>
          <thead>
            <tr><th>Email</th><th>Role</th><th>Upload Enabled</th><th>Action</th></tr>
          </thead>
          <tbody>${rows || "<tr><td colspan='4'>No users found</td></tr>"}</tbody>
        </table>
      `);

      document.querySelector("#usersPageInfo").textContent = `Page ${usersPage} of ${res.total_pages}`;

      // Event bindings
      document.querySelectorAll(".roleSelect").forEach(sel =>
        sel.addEventListener("change", () => updateRole(sel.dataset.id, sel.value))
      );

      document.querySelectorAll(".uploadToggle").forEach(chk =>
        chk.addEventListener("change", () => updateUpload(chk.dataset.id, chk.checked))
      );

      document.querySelectorAll(".revokeBtn").forEach(btn =>
        btn.addEventListener("click", () => {
          if (confirm("Revoke this user's access?")) revokeUser(btn.dataset.id);
        })
      );

      document.querySelectorAll(".unrevokeBtn").forEach(btn =>
        btn.addEventListener("click", () => {
          if (confirm("Restore this user's access?")) unrevokeUser(btn.dataset.id);
        })
      );

    } catch (err) {
      console.error(err);
      toast("Failed to load users", "error");
    } finally {
      hideSpinner();
    }
  }

  // =============================
  // API Actions
  // =============================

  async function updateRole(id, role) {
    try {
      await fetchJSON(`/admin/users/${id}/role`, { method: "PATCH", body: { role } });
      toast("Role updated");
      await loadUsers();
    } catch {
      toast("Failed to update role", "error");
    }
  }

  async function updateUpload(id, enabled) {
    try {
      await fetchJSON(`/admin/users/${id}/upload`, { method: "PATCH", body: { enabled } });
      toast("Upload setting updated");
      await loadUsers();
    } catch {
      toast("Failed to update upload", "error");
    }
  }

  async function revokeUser(id) {
    try {
      await fetchJSON(`/admin/users/${id}/revoke`, { method: "PATCH" });
      toast("User revoked");
      await loadUsers();
    } catch {
      toast("Failed to revoke user", "error");
    }
  }

  async function unrevokeUser(id) {
    try {
      await fetchJSON(`/admin/users/${id}/unrevoke`, { method: "PATCH" });
      toast("User restored");
      await loadUsers();
    } catch {
      toast("Failed to restore user", "error");
    }
  }

  // =============================
  // Logs
  // =============================
  async function loadLogs() {
    showSpinner();
    try {
      const res = await fetchJSON(`/admin/logs?page=${logsPage}&page_size=${C.PAGE_SIZE}`);
      const rows = res.items.map(l => `
        <tr>
          <td>${l.timestamp}</td>
          <td>${l.user_email || "-"}</td>
          <td>${l.action}</td>
          <td>${l.details || ""}</td>
        </tr>
      `).join("");

      setHTML("#logsTable", `
        <table>
          <thead>
            <tr><th>Time</th><th>User</th><th>Action</th><th>Details</th></tr>
          </thead>
          <tbody>${rows || "<tr><td colspan='4'>No logs found</td></tr>"}</tbody>
        </table>
      `);

      document.querySelector("#logsPageInfo").textContent = `Page ${logsPage} of ${res.total_pages}`;
    } catch {
      toast("Failed to load logs", "error");
    } finally {
      hideSpinner();
    }
  }

  async function exportLogs() {
    try {
      const resp = await fetch(`/admin/logs/export`, {
        headers: { "Authorization": `Bearer ${localStorage.getItem("docchain_token")}` }
      });
      if (!resp.ok) throw new Error("Export failed");
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "access_logs.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch {
      toast("Failed to export logs", "error");
    }
  }

  // =============================
  // Init
  // =============================
  document.addEventListener("DOMContentLoaded", async () => {
    try {
      const u = await me();
      if (!u || u.role !== "admin") {
        clear();
        location.href = "/login.html";
        return;
      }
      document.getElementById("whoami").textContent = `${u.email} (admin)`;
    } catch {
      clear();
      location.href = "/login.html";
      return;
    }

    document.getElementById("btnLogout").addEventListener("click", () => {
      clear();
      location.href = "/login.html";
    });

    document.getElementById("btnSearchUsers").addEventListener("click", () => {
      userSearch = document.getElementById("userSearch").value;
      usersPage = 1;
      loadUsers();
    });

    document.getElementById("usersPrev").addEventListener("click", () => {
      if (usersPage > 1) {
        usersPage--;
        loadUsers();
      }
    });
    document.getElementById("usersNext").addEventListener("click", () => {
      usersPage++;
      loadUsers();
    });

    document.getElementById("logsPrev").addEventListener("click", () => {
      if (logsPage > 1) {
        logsPage--;
        loadLogs();
      }
    });
    document.getElementById("logsNext").addEventListener("click", () => {
      logsPage++;
      loadLogs();
    });

    document.getElementById("btnExportLogs").addEventListener("click", exportLogs);

    await loadUsers();
    await loadLogs();
  });
})();
