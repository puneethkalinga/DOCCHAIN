(() => {
  document.addEventListener("DOMContentLoaded", () => {
    const { qs, setHTML, on, toast } = window.ui;
    const { fetchJSON } = window.api;

    // Render signup form dynamically
    setHTML(qs("#app"), `
      <div class="signup-wrapper">
        <section class="signup-box">
          <h2>Create an Account</h2>

          <label>Email</label>
          <input id="email" type="email" placeholder="you@example.com">

          <label>Password</label>
          <input id="password" type="password" placeholder="••••••••">

          <label>Role</label>
          <select id="role">
            <option value="recipient">Recipient</option>
            <option value="staff">Staff</option>
          </select>

          <button id="btnSignup">Sign Up</button>
          <div class="note">
            Already have an account? <a href="login.html">Log in</a>
          </div>
        </section>
      </div>
    `);

    const email = qs("#email");
    const password = qs("#password");
    const role = qs("#role");
    const btn = qs("#btnSignup");

    on(btn, "click", async () => {
      btn.disabled = true;
      try {
        const body = {
          email: email.value.trim(),
          password: password.value,
          role: role.value,
          mfa_enabled: false   // Always false — disables OTP/MFA
        };
        if (!body.email || !body.password)
          throw new Error("Email and password are required.");

        await fetchJSON("/auth/signup", { method: "POST", body }); 
        toast("Account created. Redirecting to login…");
        setTimeout(() => { window.location.href = "login.html"; }, 800);
      } catch (e) {
        toast(e.message || "Sign up failed");
      } finally {
        btn.disabled = false;
      }
    });
  });
})();
