/**
 * reports.js
 * Triggers report downloads by fetching a Blob from the backend and
 * forcing a browser save via a temporary object URL + <a download>.
 */

firebaseAuth.onAuthStateChanged((user) => {
  if (!user) {
    window.location.href = "./login.html";
    return;
  }
  document.getElementById("userEmail").textContent = user.email;
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await firebaseAuth.signOut();
  window.location.href = "./login.html";
});

document.querySelectorAll(".report-card-actions button").forEach((button) => {
  button.addEventListener("click", async () => {
    const reportType = button.dataset.report;
    const format = button.dataset.format;
    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = "Generating...";

    try {
      const { blob, filename } = await window.reportsApi.download(reportType, format);

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      showToast(`${filename} downloaded.`, "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = originalText;
    }
  });
});
