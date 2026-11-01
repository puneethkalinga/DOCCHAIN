(() => {
  const { me, redirectByRole } = window.auth;

  document.addEventListener("DOMContentLoaded", async () => {
    try {
      const u = await me(); // 401 -> api.js will redirect to login
      const path = location.pathname.toLowerCase();

      const needsStaff = path.endsWith("/staff.html");
      const needsAdmin = path.endsWith("/admin-users.html") || path.endsWith("/admin-logs.html");

      if (needsStaff && !(u.role === "staff" || u.role === "admin")) {
        return redirectByRole(u.role);
      }
      if (needsAdmin && u.role !== "admin") {
        return redirectByRole(u.role);
      }

      // small header helper if a #whoami element exists
      const tag = document.getElementById("whoami");
      if (tag) tag.textContent = `${u.email} · role: ${u.role}`;
    } catch (e) {
      // no-op; api.js handles unauthorized
    }
  });
})();
