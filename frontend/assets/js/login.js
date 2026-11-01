(() => {
  console.clear();
  console.log("login.js loaded");

  function clearTokens() {
    try {
      localStorage.removeItem("docchain_token");
      sessionStorage.clear();
    } catch (e) {
      console.error("Failed to clear tokens", e);
    }
  }

  document.addEventListener("DOMContentLoaded", async () => {
    if (!window.ui || !window.auth) {
      console.error("ui/auth missing");
      return;
    }
    const { qs, on, toast } = window.ui;
    const { login, verifyOtp, me, redirectByRole } = window.auth;

    const spinner = qs("#spinner");

    function showSpinner() { spinner.classList.remove("hidden"); }
    function hideSpinner() { spinner.classList.add("hidden"); }

    // =============================
    // If already logged in
    // =============================
    try {
      const u = await me();
      if (u?.role) {
        if (!location.pathname.endsWith("login.html")) {
          return redirectByRole(u.role);
        }
      }
    } catch { /* ignore */ }

    // references from static HTML
    const form = qs("#login-form"),
      email = qs("#email"),
      password = qs("#password"),
      otpInput = qs("#otp"),
      btnOtp = qs("#btnOtp"),
      step1 = qs("#step1"),
      step2 = qs("#step2");

    function showOtpStep() {
      step1.style.display = "none";
      step2.style.display = "block";
      toast("OTP sent");
      otpInput?.focus();
    }

    // =============================
    // Override redirectByRole to fix admin redirect
    // =============================
    function fixedRedirectByRole(role) {
      if (role === "admin") {
        location.href = "/admin.html";   
      } else if (role === "staff") {
        location.href = "/staff.html";
      } else if (role === "recipient") {
        location.href = "/recipient.html";
      } else {
        location.href = "/login.html";
      }
    }

    // =============================
    // Login form submit
    // =============================
    on(form, "submit", async (e) => {
      e.preventDefault();
      clearTokens(); // clear only on explicit login attempt
      const btn = form.querySelector("button[type=submit]");
      btn.disabled = true;
      showSpinner();
      try {
        const res = await login(email.value.trim(), password.value);

        if (res.mfa_required) {
          showOtpStep();
          return;
        }

        if (res.access_token) {
          localStorage.setItem("docchain_token", res.access_token);
        }

        if (res.user && res.user.role) {
          return fixedRedirectByRole(res.user.role);
        }

        const u = await me();
        return fixedRedirectByRole(u.role);
      } catch (e) {
        console.error(e);
        toast(e.message || "Login failed");
      } finally {
        btn.disabled = false;
        hideSpinner();
      }
    });

    // =============================
    // OTP verify button
    // =============================
    on(btnOtp, "click", async () => {
      btnOtp.disabled = true;
      showSpinner();
      try {
        const res = await verifyOtp(email.value.trim(), otpInput.value.trim());

        if (res.access_token) {
          localStorage.setItem("docchain_token", res.access_token);
        }

        if (res.user && res.user.role) {
          return fixedRedirectByRole(res.user.role);
        }

        const u = await me();
        return fixedRedirectByRole(u.role);
      } catch (e) {
        console.error(e);
        toast(e.message || "OTP verify failed");
      } finally {
        btnOtp.disabled = false;
        hideSpinner();
      }
    });
  });
})();
