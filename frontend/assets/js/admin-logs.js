(() => {
  const { qs, setHTML, on } = window.ui;
  const { fetchJSON } = window.api;
  const { me } = window.auth;

  function table(rows) {
    const body = rows.map(r => `
      <tr>
        <td>${r.ts || ""}</td>
        <td>${r.user_email || ""}</td>
        <td>${r.action || ""}</td>
        <td>${r.letter_id || ""}</td>
        <td>${r.ip || ""}</td>
        <td>${r.ua || ""}</td>
      </tr>`).join("");
    return `
      <table style="width:100%;border-collapse:collapse">
        <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Letter</th><th>IP</th><th>User-Agent</th></tr></thead>
        <tbody>${body || `<tr><td colspan="6">No logs</td></tr>`}</tbody>
      </table>`;
  }

  async function loadLogs() {
    try {
      // This assumes you’ll add GET /logs?user=&letter_id=&action= later.
      const p = new URLSearchParams();
      const u = qs("#f_user").value.trim(); if (u) p.set("user", u);
      const l = qs("#f_letter").value.trim(); if (l) p.set("letter_id", l);
      const a = qs("#f_action").value; if (a) p.set("action", a);
      const data = await fetchJSON(`/logs?${p.toString()}`, { auth:true });
      setHTML(qs("#logsTable"), table(Array.isArray(data) ? data : (data.items || [])));
    } catch (e) {
      setHTML(qs("#logsTable"),
        `<div style="background:#0f142a;padding:16px;border-radius:12px">
           <p><b>Heads up:</b> /logs endpoint not found or not implemented yet.</p>
           <p>Core demo works without it. Add this endpoint later for full marks.</p>
         </div>`);
    }
  }

  document.addEventListener("DOMContentLoaded", async () => {
    try { const u = await me(); const who = qs("#whoami"); if (who) who.textContent = `${u.email} · role: ${u.role}`; } catch {}
    on(qs("#btnFilter"), "click", loadLogs);
    loadLogs();
  });
})();
