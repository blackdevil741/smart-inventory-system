/**
 * qr-scanner.js
 *
 * Real webcam QR scanning via the html5-qrcode library. Our QR codes
 * encode "product:<firestore-doc-id>" (see backend/services/qr_service.py),
 * so on a successful scan we parse out the id, call the backend to
 * confirm the product still exists, and show it with quick stock
 * adjustment buttons -- the whole "scan at the till" workflow.
 */

let html5QrCode = null;
let isScanning = false;
let currentScannedProduct = null;

const toggleScannerBtn = document.getElementById("toggleScannerBtn");
const scanResultEmpty = document.getElementById("scanResultEmpty");
const scanResultError = document.getElementById("scanResultError");
const scanResultProduct = document.getElementById("scanResultProduct");

// ---- Route guard ----
firebaseAuth.onAuthStateChanged((user) => {
  if (!user) {
    window.location.href = "./login.html";
    return;
  }
  document.getElementById("userEmail").textContent = user.email;
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  if (isScanning) await stopScanner();
  await firebaseAuth.signOut();
  window.location.href = "./login.html";
});

function showEmpty() {
  scanResultEmpty.style.display = "block";
  scanResultError.classList.remove("is-visible");
  scanResultProduct.classList.remove("is-visible");
}

function showError(message) {
  scanResultEmpty.style.display = "none";
  scanResultProduct.classList.remove("is-visible");
  scanResultError.textContent = message;
  scanResultError.classList.add("is-visible");
}

function showProduct(product) {
  currentScannedProduct = product;
  scanResultEmpty.style.display = "none";
  scanResultError.classList.remove("is-visible");

  document.getElementById("resultName").textContent = product.name;
  document.getElementById("resultSku").textContent = product.sku;
  document.getElementById("resultCategory").textContent = product.category;
  updateQtyDisplay(product);

  scanResultProduct.classList.add("is-visible");
}

function updateQtyDisplay(product) {
  const qty = product.quantity ?? 0;
  const threshold = product.min_quantity_threshold ?? 5;
  const qtyEl = document.getElementById("resultQty");
  qtyEl.textContent = `${qty} in stock`;
  qtyEl.style.color = qty <= 0
    ? "var(--terracotta-700)"
    : qty <= threshold
      ? "#8a6417"
      : "var(--stock-green-700)";
}

// ---- Parse "product:<id>" payloads from our own QR codes ----
function extractProductId(decodedText) {
  const match = /^product:(.+)$/.exec(decodedText.trim());
  return match ? match[1] : null;
}

async function handleScanSuccess(decodedText) {
  const productId = extractProductId(decodedText);
  if (!productId) {
    showError("That doesn't look like a Smart Inventory product QR code.");
    return;
  }

  try {
    const product = await window.qrApi.resolveScannedProduct(productId);
    showProduct(product);
    showToast(`Scanned: ${product.name}`, "success");
  } catch (err) {
    showError(err.message);
  }
}

// ---- Camera lifecycle ----
async function startScanner() {
  html5QrCode = new Html5Qrcode("qrReaderViewport");

  try {
    await html5QrCode.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 240, height: 240 } },
      (decodedText) => {
        // Briefly pause scanning after a hit so the same code isn't
        // re-processed dozens of times a second while still in frame.
        handleScanSuccess(decodedText);
        html5QrCode.pause(true);
        setTimeout(() => {
          if (html5QrCode && isScanning) html5QrCode.resume();
        }, 2000);
      },
      () => { /* per-frame decode failures are normal/expected, ignore */ }
    );
    isScanning = true;
    toggleScannerBtn.textContent = "Stop camera";
  } catch (err) {
    showToast(
      "Couldn't access the camera. Make sure you've allowed camera permission for this site.",
      "error"
    );
  }
}

async function stopScanner() {
  if (html5QrCode && isScanning) {
    try {
      await html5QrCode.stop();
      html5QrCode.clear();
    } catch (err) {
      // Camera may already be stopped; safe to ignore.
    }
  }
  isScanning = false;
  toggleScannerBtn.textContent = "Start camera";
}

toggleScannerBtn.addEventListener("click", () => {
  if (isScanning) {
    stopScanner();
  } else {
    startScanner();
  }
});

// ---- Quick stock actions on the scanned product ----
document.querySelectorAll(".scan-quick-actions button").forEach((button) => {
  button.addEventListener("click", async () => {
    if (!currentScannedProduct) return;
    const delta = Number(button.dataset.delta);

    button.disabled = true;
    try {
      const updated = await window.productsApi.adjustStock(currentScannedProduct.id, delta);
      currentScannedProduct = updated;
      updateQtyDisplay(updated);
      showToast(`Stock ${delta > 0 ? "increased" : "decreased"} to ${updated.quantity}.`, "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      button.disabled = false;
    }
  });
});

showEmpty();
