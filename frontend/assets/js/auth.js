(() => {
  const { fetchJSON, clearToken } = window.api;

  // =========================
  // Token helpers
  // =========================
  function saveToken(t) {
    try {
      localStorage.setItem("docchain_token", t);
    } catch {}
  }

  function clear() {
    try {
      clearToken();
      localStorage.clear();
      sessionStorage.clear();
      console.clear();
      console.log("DocChain session cleared");
    } catch (e) {
      console.error("Failed to clear session", e);
    }
  }

  // =========================
  // Current user
  // =========================
  async function me() {
    return await fetchJSON("/me");
  }

  // =========================
  // Role-based redirect
  // =========================
  function redirectByRole(role) {
    if (role === "staff") {
      window.location.href = "staff.html";
    } else if (role === "admin") {
      window.location.href = "admin-users.html";
    } else if (role === "recipient") {
      window.location.href = "recipient.html";
    } else {
      window.location.href = "login.html";
    }
  }

  // =========================
  // Auth API calls
  // =========================
  async function login(email, password) {
    const data = await fetchJSON("/auth/login", {
      method: "POST",
      body: { email, password },
    });
    if (data.access_token) saveToken(data.access_token);
    return data;
  }

  async function verifyOtp(email, otp) {
    const data = await fetchJSON("/auth/verify-otp", {
      method: "POST",
      body: { email, otp },
    });
    if (data.access_token) saveToken(data.access_token);
    return data;
  }

  // =========================
  // Export to window
  // =========================
  window.auth = { saveToken, clear, me, redirectByRole, login, verifyOtp };
})();
