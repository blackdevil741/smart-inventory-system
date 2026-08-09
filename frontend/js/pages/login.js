/**
 * login.js
 *
 * Handles the login form using real Firebase Authentication.
 * On success, stores nothing manually -- firebase.auth() persists the
 * session itself -- and redirects to the dashboard (built in Phase 6;
 * until then it redirects to a temporary placeholder route).
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const emailError = document.getElementById("emailError");
  const passwordError = document.getElementById("passwordError");
  const loginError = document.getElementById("loginError");
  const submitBtn = document.getElementById("loginSubmit");

  function clearErrors() {
    emailError.textContent = "";
    passwordError.textContent = "";
    loginError.classList.remove("is-visible");
    loginError.textContent = "";
  }

  function validate() {
    let valid = true;
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(emailInput.value.trim())) {
      emailError.textContent = "Enter a valid email address.";
      valid = false;
    }

    if (passwordInput.value.length < 6) {
      passwordError.textContent = "Password must be at least 6 characters.";
      valid = false;
    }

    return valid;
  }

  // Maps Firebase's internal error codes to messages a shopkeeper
  // (not a developer) will actually understand.
  function friendlyAuthError(error) {
    const map = {
      "auth/invalid-email": "That email address doesn't look right.",
      "auth/user-disabled": "This account has been disabled. Contact support.",
      "auth/user-not-found": "No account found with that email.",
      "auth/wrong-password": "Incorrect password. Try again or reset it.",
      "auth/invalid-credential": "Incorrect email or password.",
      "auth/too-many-requests": "Too many attempts. Please wait a moment and try again.",
      "auth/network-request-failed": "Network error. Check your connection.",
    };
    return map[error.code] || "Something went wrong. Please try again.";
  }

  async function handleLogin(event) {
    event.preventDefault();
    clearErrors();

    if (!validate()) return;

    submitBtn.disabled = true;
    submitBtn.textContent = "Logging in...";

    try {
      await window.firebaseAuth.signInWithEmailAndPassword(
        emailInput.value.trim(),
        passwordInput.value
      );

      // Redirect to the dashboard. dashboard.html doesn't exist until
      // Phase 6 -- this points there already so the login flow is
      // "done" from this page's perspective.
      window.location.href = "./dashboard.html";
    } catch (err) {
      loginError.textContent = friendlyAuthError(err);
      loginError.classList.add("is-visible");
      submitBtn.disabled = false;
      submitBtn.textContent = "Log in";
    }
  }

  form.addEventListener("submit", handleLogin);

  // If already logged in (e.g. came back to this page by mistake),
  // skip straight to the dashboard.
  window.firebaseAuth.onAuthStateChanged((user) => {
    if (user) {
      window.location.href = "./dashboard.html";
    }
  });
});
