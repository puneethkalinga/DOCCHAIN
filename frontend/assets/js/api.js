(() => {
  const C = window.DOCCHAIN_CONFIG || {};

  function getToken() {
    try { return localStorage.getItem("docchain_token"); } catch {}
  }

  function clearToken() {
    try { localStorage.removeItem("docchain_token"); } catch {}
  }

  async function fetchJSON(path, { method="GET", body=null, headers={}, form=false } = {}) {
    const url = `${C.BASE_URL}/api${path.startsWith('/') ? path : '/' + path}`; 
    const hdrs = new Headers(headers);

    //  Attach token automatically unless it's an auth/verify endpoint
    const t = getToken();
    if (t && !path.startsWith("/auth") && !path.startsWith("/verify")) {
      hdrs.set("Authorization", `Bearer ${t}`);
    }

    if (!form && body) hdrs.set("Content-Type", "application/json");

    const res = await fetch(url, { 
      method, 
      headers: hdrs, 
      body: form ? body : (body ? JSON.stringify(body) : null) 
    });

    if (res.status === 401) {
      clearToken();
      window.location.href = "login.html";
      throw new Error("Unauthorized");
    }

    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("application/json")) return res; // for downloads

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.message || res.statusText);
    return data;
  }

  async function fetchBlob(url, opts={}) {
    const r = await fetch(url, opts);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.blob();
  }

  window.api = { fetchJSON, fetchBlob, getToken, clearToken };
  console.log("✅ api.js loaded (auto token attach, /auth & /verify skipped)");
})();
