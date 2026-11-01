(() => {
  console.log("inbox.js loaded");

  document.addEventListener("DOMContentLoaded", async () => {
    if (!window.ui || !window.auth) { 
      console.error("ui/auth missing"); 
      return; 
    }
    const { qs, setHTML, toast } = window.ui;
    const { me, redirectByRole } = window.auth;

    // =============================
    // Auth check
    // =============================
    try {
      const u = await me();
      if (!u || u.role !== "recipient") {
        return redirectByRole(u?.role || "login");
      }
    } catch (e) {
      console.error(e);
      return toast("Not logged in");
    }

    // =============================
    // Load recipient inbox
    // =============================
    try {
      const res = await fetch("/letters/inbox", {
        headers: { Authorization: "Bearer " + localStorage.getItem("access_token") }
      });
      if (!res.ok) throw new Error("Failed to fetch letters");
      const docs = await res.json();

      if (!docs.length) {
        setHTML(qs("#app"), "<p>No documents found.</p>");
        return;
      }

      const list = docs.map(d => `
        <li style="margin:12px 0;padding:12px;border:1px solid #333;border-radius:8px;background:#1b2235">
          <strong>${d.title}</strong><br/>
          Uploaded: ${new Date(d.uploaded_at).toLocaleString()}<br/>
          ${d.expires_at ? `Expires: ${new Date(d.expires_at).toLocaleString()}<br/>` : ""}
          Hash: <code>${d.hash}</code><br/>
          <a href="${d.download_url}" target="_blank">📄 Download</a>
        </li>
      `).join("");

      setHTML(qs("#app"), `<h2>Your Letters</h2><ul style="list-style:none;padding:0">${list}</ul>`);

    } catch (e) {
      console.error(e);
      toast("Could not load letters");
    }
  });
})();
