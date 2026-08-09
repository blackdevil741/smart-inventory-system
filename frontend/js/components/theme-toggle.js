/**
 * theme-toggle.js
 *
 * Shared dark mode toggle for all authenticated pages. Persists the
 * choice in localStorage (a normal browser feature -- this runs in
 * the actual deployed/local site, not a sandboxed artifact preview,
 * so localStorage is fully supported here) and applies it immediately
 * on load to avoid a flash of the wrong theme.
 */

(function () {
  const STORAGE_KEY = "smart-inventory-theme";

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }

  function getStoredTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY) || "light";
    } catch {
      return "light";
    }
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* localStorage unavailable (e.g. private browsing edge cases) -- ignore, theme just won't persist */
    }
  }

  // Apply immediately (before DOMContentLoaded) to avoid a flash of
  // the wrong theme on page load.
  applyTheme(getStoredTheme());

  document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("themeToggleBtn");
    if (!toggleBtn) return;

    function updateButtonLabel() {
      const current = document.documentElement.getAttribute("data-theme");
      toggleBtn.textContent = current === "dark" ? "☀️ Light" : "🌙 Dark";
    }

    updateButtonLabel();

    toggleBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      setStoredTheme(next);
      updateButtonLabel();
    });
  });
})();
