/**
 * signup.js
 *
 * Creates a Firebase Auth account, then calls the Flask backend to
 * create the matching Firestore profile document (shop name, role).
 * Two steps because Firebase Auth (credentials) and Firestore (profile
 * data) are separate systems -- the backend is what links them by uid.
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("signupForm");
  const shopName = document.getElementById("shopName");
  const email = document.getElementById("email");
  const password = document.getElementById("password");
  const confirmPassword = document.getElementById("confirmPassword");

  const shopNameError = document.getElementById("shopNameError");
  const emailError = document.getElementById("emailError");
  const passwordError = document.getElementById("passwordError");
  const confirmPasswordError = document.getElementById("confirmPasswordError");
  const signupError = document.getElementById("signupError");
  const submitBtn = document.getElementById("signupSubmit");

  function clearErrors() {
    [shopNameError, emailError, passwordError, confirmPasswordError].forEach((el) => (el.textContent = ""));
    signupError.classList.remove("is-visible");
    signupError.textContent = "";
  }

  function validate() {
    let valid = true;
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (shopName.value.trim().length < 2) {
      shopNameError.textContent = "Enter your shop or vendor name.";
      valid = false;
    }
    if (!emailPattern.test(email.value.trim())) {
      emailError.textContent = "Enter a valid email address.";
      valid = false;
    }
    if (password.value.length < 6) {
      passwordError.textContent = "Password must be at least 6 characters.";
      valid = false;
    }
    if (confirmPassword.value !== password.value) {
      confirmPasswordError.textContent = "Passwords do not match.";
      valid = false;
    }
    return valid;
  }

  function friendlyAuthError(error) {
    const map = {
      "auth/email-already-in-use": "An account with this email already exists.",
      "auth/invalid-email": "That email address doesn't look right.",
      "auth/weak-password": "Please choose a stronger password (at least 6 characters).",
      "auth/network-request-failed": "Network error. Check your connection.",
    };
    return map[error.code] || "Something went wrong. Please try again.";
  }

  async function handleSignup(event) {
    event.preventDefault();
    clearErrors();
    if (!validate()) return;

    submitBtn.disabled = true;
    submitBtn.textContent = "Creating account...";

    let createdUser = null;

    try {
      // Step 1: create the Firebase Auth account (handles the password securely).
      const credential = await window.firebaseAuth.createUserWithEmailAndPassword(
        email.value.trim(),
        password.value
      );
      createdUser = credential.user;

      await createdUser.updateProfile({ displayName: shopName.value.trim() });

      // Step 2: create the Firestore profile via the backend, authenticated
      // with the fresh ID token so the backend can trust the uid.
      const idToken = await createdUser.getIdToken();
      await window.api.request("/api/auth/register-profile", {
        method: "POST",
        authToken: idToken,
        body: {
          shop_name: shopName.value.trim(),
          email: email.value.trim(),
        },
      });

      window.location.href = "./dashboard.html";
    } catch (err) {
      // If Firestore profile creation failed after Auth succeeded, the
      // account still exists -- surface a clear message rather than
      // silently leaving an orphaned auth account.
      if (err.code) {
        signupError.textContent = friendlyAuthError(err);
      } else {
        signupError.textContent =
          "Your account was created, but we couldn't finish setup: " + err.message;
      }
      signupError.classList.add("is-visible");
      submitBtn.disabled = false;
      submitBtn.textContent = "Create account";
    }
  }

  form.addEventListener("submit", handleSignup);
});
