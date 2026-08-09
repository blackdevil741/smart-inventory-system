/**
 * forgot-password.js
 * Uses real Firebase Auth password reset emails.
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("resetForm");
  const email = document.getElementById("email");
  const emailError = document.getElementById("emailError");
  const resetSuccess = document.getElementById("resetSuccess");
  const resetError = document.getElementById("resetError");
  const submitBtn = document.getElementById("resetSubmit");

  function friendlyAuthError(error) {
    const map = {
      "auth/invalid-email": "That email address doesn't look right.",
      "auth/user-not-found": "No account found with that email.",
      "auth/network-request-failed": "Network error. Check your connection.",
    };
    return map[error.code] || "Something went wrong. Please try again.";
  }

  async function handleReset(event) {
    event.preventDefault();
    emailError.textContent = "";
    resetSuccess.classList.remove("is-visible");
    resetError.classList.remove("is-visible");

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email.value.trim())) {
      emailError.textContent = "Enter a valid email address.";
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Sending...";

    try {
      await window.firebaseAuth.sendPasswordResetEmail(email.value.trim());
      resetSuccess.textContent = "Check your inbox for a password reset link.";
      resetSuccess.classList.add("is-visible");
      form.reset();
    } catch (err) {
      // Firebase intentionally does NOT reveal whether an email exists
      // for password reset (to prevent account enumeration), so most
      // real deployments show a generic success message regardless.
      // We surface the real error here only for genuinely invalid input.
      resetError.textContent = friendlyAuthError(err);
      resetError.classList.add("is-visible");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Send reset link";
    }
  }

  form.addEventListener("submit", handleReset);
});
