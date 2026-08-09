/**
 * inventory.js
 *
 * Drives the Inventory page: route guard, loading/rendering products
 * from Firestore (via the Flask API), the Add/Edit modal, delete
 * confirmation, quick stock adjustment buttons, and search/filter/sort.
 */

let currentProducts = [];
let editingProductId = null;
let pendingDeleteId = null;
let currentPage = 1;
const PAGE_SIZE = 10;

const tableBody = document.getElementById("productTableBody");
const searchInput = document.getElementById("searchInput");
const categoryFilter = document.getElementById("categoryFilter");
const stockFilter = document.getElementById("stockFilter");
const sortBySelect = document.getElementById("sortBy");

// ---- Route guard ----
firebaseAuth.onAuthStateChanged((user) => {
  if (!user) {
    window.location.href = "./login.html";
    return;
  }
  document.getElementById("userEmail").textContent = user.email;
  loadProducts();
  loadCategoryOptions();
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await firebaseAuth.signOut();
  window.location.href = "./login.html";
});

// ---- Rendering ----
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function stockBadge(product) {
  const qty = product.quantity ?? 0;
  const threshold = product.min_quantity_threshold ?? 5;

  if (qty <= 0) {
    return `<span class="qty-badge qty-badge--out ink-stamp">${qty} · out</span>`;
  }
  if (qty <= threshold) {
    return `<span class="qty-badge qty-badge--low ink-stamp">${qty} · low</span>`;
  }
  return `<span class="qty-badge qty-badge--ok ink-stamp">${qty} · in stock</span>`;
}

function rowClass(product) {
  const qty = product.quantity ?? 0;
  const threshold = product.min_quantity_threshold ?? 5;
  if (qty <= 0) return "is-out-of-stock";
  if (qty <= threshold) return "is-low-stock";
  return "";
}

function renderProducts(products) {
  if (products.length === 0) {
    tableBody.innerHTML = `
      <tr><td colspan="8">
        <div class="table-empty-state">
          <h3>No products found</h3>
          <p>Try adjusting your search or filters, or add your first product.</p>
        </div>
      </td></tr>`;
    return;
  }

  tableBody.innerHTML = products.map((p) => `
    <tr class="${rowClass(p)}" data-id="${p.id}">
      <td class="product-name-cell">${escapeHtml(p.name)}</td>
      <td class="product-sku-cell">${escapeHtml(p.sku)}</td>
      <td>${escapeHtml(p.category)}</td>
      <td>${stockBadge(p)}</td>
      <td class="mono ledger-numeral">₹${Number(p.cost_price || 0).toFixed(2)} / ₹${Number(p.selling_price || 0).toFixed(2)}</td>
      <td>${escapeHtml(p.vendor_name || "—")}</td>
      <td>
        <div class="stock-quick-actions">
          <button class="decrease" data-action="adjust" data-delta="-10" title="-10">-10</button>
          <button class="decrease" data-action="adjust" data-delta="-5" title="-5">-5</button>
          <button class="decrease" data-action="adjust" data-delta="-1" title="-1">-1</button>
          <button class="increase" data-action="adjust" data-delta="1" title="+1">+1</button>
          <button class="increase" data-action="adjust" data-delta="5" title="+5">+5</button>
          <button class="increase" data-action="adjust" data-delta="10" title="+10">+10</button>
        </div>
      </td>
      <td>
        <div class="row-actions">
          <button class="edit" data-action="edit" title="Edit">Edit</button>
          <button class="edit" data-action="qr" title="View QR">QR</button>
          <button class="delete" data-action="delete" title="Delete">Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

function renderLoading() {
  tableBody.innerHTML = Array.from({ length: 4 }).map(() => `
    <tr class="skeleton-row"><td colspan="8"><div class="skeleton-bar"></div></td></tr>
  `).join("");
}

function updateCategoryFilterOptions(products) {
  const categories = [...new Set(products.map((p) => p.category).filter(Boolean))].sort();
  const current = categoryFilter.value;
  categoryFilter.innerHTML = `<option value="">All categories</option>` +
    categories.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
  categoryFilter.value = categories.includes(current) ? current : "";
}

// ---- Data loading ----
async function loadCategoryOptions() {
  try {
    const result = await window.productsApi.list({ page: 1, pageSize: 500 });
    updateCategoryFilterOptions(result.items);
  } catch (err) {
    // Non-critical: the category dropdown just won't populate fully. The
    // table itself still loads via loadProducts(), so silently skip.
  }
}

async function loadProducts() {
  renderLoading();
  try {
    const result = await window.productsApi.list({
      search: searchInput.value.trim(),
      category: categoryFilter.value,
      stockFilter: stockFilter.value,
      sortBy: sortBySelect.value,
      page: currentPage,
      pageSize: PAGE_SIZE,
    });
    currentProducts = result.items;
    renderProducts(result.items);
    renderPaginationControls(result.pagination);
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="8"><div class="table-empty-state">Couldn't load products: ${escapeHtml(err.message)}</div></td></tr>`;
    showToast(err.message, "error");
  }
}

function renderPaginationControls(pagination) {
  let container = document.getElementById("paginationControls");
  if (!container) {
    container = document.createElement("div");
    container.id = "paginationControls";
    container.style.cssText = "display:flex; align-items:center; justify-content:center; gap:12px; margin-top:16px; font-size: var(--fs-sm); color: var(--stone-500);";
    document.querySelector(".product-table-wrap").insertAdjacentElement("afterend", container);
  }

  const { page, total_pages, total_items } = pagination;

  container.innerHTML = `
    <button id="prevPageBtn" ${page <= 1 ? "disabled" : ""} style="padding:6px 12px; border-radius:6px; border:1px solid var(--stone-200); background:var(--white); cursor:${page <= 1 ? "not-allowed" : "pointer"};">← Prev</button>
    <span>Page ${page} of ${total_pages} &middot; ${total_items} product${total_items === 1 ? "" : "s"}</span>
    <button id="nextPageBtn" ${page >= total_pages ? "disabled" : ""} style="padding:6px 12px; border-radius:6px; border:1px solid var(--stone-200); background:var(--white); cursor:${page >= total_pages ? "not-allowed" : "pointer"};">Next →</button>
  `;

  document.getElementById("prevPageBtn").addEventListener("click", () => {
    if (currentPage > 1) {
      currentPage -= 1;
      loadProducts();
    }
  });
  document.getElementById("nextPageBtn").addEventListener("click", () => {
    if (currentPage < total_pages) {
      currentPage += 1;
      loadProducts();
    }
  });
}

function resetToFirstPage() {
  currentPage = 1;
  loadProducts();
}

let searchDebounceTimer = null;
searchInput.addEventListener("input", () => {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(resetToFirstPage, 350);
});
categoryFilter.addEventListener("change", resetToFirstPage);
stockFilter.addEventListener("change", resetToFirstPage);
sortBySelect.addEventListener("change", resetToFirstPage);

// ---- Add / Edit modal ----
const productModalOverlay = document.getElementById("productModalOverlay");
const productForm = document.getElementById("productForm");
const modalTitle = document.getElementById("modalTitle");
const saveProductBtn = document.getElementById("saveProductBtn");

function openAddModal() {
  editingProductId = null;
  modalTitle.textContent = "Add Product";
  productForm.reset();
  document.getElementById("productId").value = "";
  document.getElementById("productQuantity").value = 0;
  document.getElementById("productThreshold").value = 5;
  document.getElementById("productCostPrice").value = 0;
  document.getElementById("productSellingPrice").value = 0;
  clearFormErrors();
  productModalOverlay.classList.add("is-open");
}

function openEditModal(product) {
  editingProductId = product.id;
  modalTitle.textContent = "Edit Product";
  document.getElementById("productId").value = product.id;
  document.getElementById("productName").value = product.name || "";
  document.getElementById("productSku").value = product.sku || "";
  document.getElementById("productCategory").value = product.category || "";
  document.getElementById("productQuantity").value = product.quantity ?? 0;
  document.getElementById("productThreshold").value = product.min_quantity_threshold ?? 5;
  document.getElementById("productCostPrice").value = product.cost_price ?? 0;
  document.getElementById("productSellingPrice").value = product.selling_price ?? 0;
  document.getElementById("productVendor").value = product.vendor_name || "";
  clearFormErrors();
  productModalOverlay.classList.add("is-open");
}

function closeProductModal() {
  productModalOverlay.classList.remove("is-open");
}

function clearFormErrors() {
  document.getElementById("productNameError").textContent = "";
  document.getElementById("productSkuError").textContent = "";
  document.getElementById("productCategoryError").textContent = "";
}

document.getElementById("openAddModalBtn").addEventListener("click", openAddModal);
document.getElementById("closeModalBtn").addEventListener("click", closeProductModal);
document.getElementById("cancelModalBtn").addEventListener("click", closeProductModal);
productModalOverlay.addEventListener("click", (e) => {
  if (e.target === productModalOverlay) closeProductModal();
});

function validateForm() {
  let valid = true;
  clearFormErrors();

  if (!document.getElementById("productName").value.trim()) {
    document.getElementById("productNameError").textContent = "Product name is required.";
    valid = false;
  }
  if (!document.getElementById("productSku").value.trim()) {
    document.getElementById("productSkuError").textContent = "SKU is required.";
    valid = false;
  }
  if (!document.getElementById("productCategory").value.trim()) {
    document.getElementById("productCategoryError").textContent = "Category is required.";
    valid = false;
  }
  return valid;
}

productForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!validateForm()) return;

  const payload = {
    name: document.getElementById("productName").value.trim(),
    sku: document.getElementById("productSku").value.trim(),
    category: document.getElementById("productCategory").value.trim(),
    quantity: Number(document.getElementById("productQuantity").value || 0),
    min_quantity_threshold: Number(document.getElementById("productThreshold").value || 5),
    cost_price: Number(document.getElementById("productCostPrice").value || 0),
    selling_price: Number(document.getElementById("productSellingPrice").value || 0),
    vendor_name: document.getElementById("productVendor").value.trim(),
  };

  saveProductBtn.disabled = true;
  saveProductBtn.textContent = "Saving...";

  try {
    if (editingProductId) {
      await window.productsApi.update(editingProductId, payload);
      showToast("Product updated.", "success");
    } else {
      await window.productsApi.create(payload);
      showToast("Product added.", "success");
    }
    closeProductModal();
    loadProducts();
    loadCategoryOptions();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    saveProductBtn.disabled = false;
    saveProductBtn.textContent = "Save product";
  }
});

// ---- Delete confirmation ----
const deleteModalOverlay = document.getElementById("deleteModalOverlay");
const deleteProductNameEl = document.getElementById("deleteProductName");

function openDeleteModal(product) {
  pendingDeleteId = product.id;
  deleteProductNameEl.textContent = product.name;
  deleteModalOverlay.classList.add("is-open");
}

function closeDeleteModal() {
  deleteModalOverlay.classList.remove("is-open");
  pendingDeleteId = null;
}

document.getElementById("closeDeleteModalBtn").addEventListener("click", closeDeleteModal);
document.getElementById("cancelDeleteBtn").addEventListener("click", closeDeleteModal);
deleteModalOverlay.addEventListener("click", (e) => {
  if (e.target === deleteModalOverlay) closeDeleteModal();
});

document.getElementById("confirmDeleteBtn").addEventListener("click", async () => {
  if (!pendingDeleteId) return;
  try {
    await window.productsApi.remove(pendingDeleteId);
    showToast("Product deleted.", "success");
    closeDeleteModal();
    loadProducts();
  } catch (err) {
    showToast(err.message, "error");
  }
});

// ---- QR modal ----
const qrModalOverlay = document.getElementById("qrModalOverlay");
const qrModalImage = document.getElementById("qrModalImage");
const qrModalProductName = document.getElementById("qrModalProductName");
const qrModalDownloadBtn = document.getElementById("qrModalDownloadBtn");

async function openQrModal(product) {
  qrModalProductName.textContent = product.name;
  qrModalImage.src = "";
  qrModalImage.alt = "Loading QR code...";
  qrModalOverlay.classList.add("is-open");

  try {
    const result = await window.qrApi.getQrCode(product.id);
    qrModalImage.src = result.qr_image;
    qrModalImage.alt = `QR code for ${product.name}`;
    qrModalDownloadBtn.href = result.qr_image;
    qrModalDownloadBtn.download = `qr-${product.sku || product.id}.png`;
  } catch (err) {
    showToast(err.message, "error");
    qrModalOverlay.classList.remove("is-open");
  }
}

document.getElementById("closeQrModalBtn").addEventListener("click", () => {
  qrModalOverlay.classList.remove("is-open");
});
qrModalOverlay.addEventListener("click", (e) => {
  if (e.target === qrModalOverlay) qrModalOverlay.classList.remove("is-open");
});

// ---- Table click delegation (edit / delete / stock quick actions) ----
tableBody.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;

  const row = button.closest("tr[data-id]");
  if (!row) return;
  const productId = row.dataset.id;
  const product = currentProducts.find((p) => p.id === productId);
  if (!product) return;

  const action = button.dataset.action;

  if (action === "edit") {
    openEditModal(product);
  } else if (action === "qr") {
    openQrModal(product);
  } else if (action === "delete") {
    openDeleteModal(product);
  } else if (action === "adjust") {
    const delta = Number(button.dataset.delta);
    button.disabled = true;
    try {
      await window.productsApi.adjustStock(productId, delta);
      loadProducts();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      button.disabled = false;
    }
  }
});

// ---- Bulk CSV import/export ----
document.getElementById("exportCsvBtn").addEventListener("click", async () => {
  try {
    const { blob, filename } = await window.productsApi.exportCsv();
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
  }
});

const csvFileInput = document.getElementById("csvFileInput");
document.getElementById("importCsvBtn").addEventListener("click", () => {
  csvFileInput.click();
});

csvFileInput.addEventListener("change", async () => {
  const file = csvFileInput.files[0];
  if (!file) return;

  try {
    const result = await window.productsApi.importCsv(file);
    if (result.errors && result.errors.length > 0) {
      showToast(`Imported ${result.created} product(s), ${result.errors.length} row(s) had errors (see console).`, "error");
      console.warn("CSV import errors:", result.errors);
    } else {
      showToast(`Imported ${result.created} product(s).`, "success");
    }
    currentPage = 1;
    loadProducts();
    loadCategoryOptions();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    csvFileInput.value = "";
  }
});
