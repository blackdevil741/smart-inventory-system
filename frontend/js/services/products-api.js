/**
 * products-api.js
 *
 * Wraps all /api/products calls, automatically attaching the current
 * user's Firebase ID token (via window.api.request's authToken option).
 * Every call here first waits for a fresh token so an expired one
 * never silently causes a 401.
 */

async function getAuthToken() {
  const user = window.firebaseAuth.currentUser;
  if (!user) throw new Error("You must be logged in.");
  return user.getIdToken();
}

const productsApi = {
  async list({ search, category, stockFilter, sortBy, page, pageSize } = {}) {
    const token = await getAuthToken();
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (category) params.set("category", category);
    if (stockFilter) params.set("stock_filter", stockFilter);
    if (sortBy) params.set("sort_by", sortBy);
    if (page) params.set("page", page);
    if (pageSize) params.set("page_size", pageSize);

    const query = params.toString() ? `?${params.toString()}` : "";
    return window.api.request(`/api/products${query}`, { authToken: token });
  },

  async create(productData) {
    const token = await getAuthToken();
    return window.api.request("/api/products", {
      method: "POST",
      authToken: token,
      body: productData,
    });
  },

  async update(productId, productData) {
    const token = await getAuthToken();
    return window.api.request(`/api/products/${productId}`, {
      method: "PATCH",
      authToken: token,
      body: productData,
    });
  },

  async remove(productId) {
    const token = await getAuthToken();
    return window.api.request(`/api/products/${productId}`, {
      method: "DELETE",
      authToken: token,
    });
  },

  async adjustStock(productId, delta) {
    const token = await getAuthToken();
    return window.api.request(`/api/products/${productId}/adjust-stock`, {
      method: "POST",
      authToken: token,
      body: { delta },
    });
  },
};

window.productsApi = productsApi;

// ---- QR code endpoints ----
window.qrApi = {
  async getQrCode(productId) {
    const token = await getAuthToken();
    return window.api.request(`/api/qr/${productId}`, { authToken: token });
  },

  async resolveScannedProduct(productId) {
    const token = await getAuthToken();
    return window.api.request(`/api/qr/resolve/${productId}`, { authToken: token });
  },
};

// ---- Dashboard endpoints ----
window.dashboardApi = {
  async getSummary() {
    const token = await getAuthToken();
    return window.api.request("/api/dashboard/summary", { authToken: token });
  },
  async getActivity(limit = 15) {
    const token = await getAuthToken();
    return window.api.request(`/api/dashboard/activity?limit=${limit}`, { authToken: token });
  },
};

// ---- Analytics endpoints ----
window.analyticsApi = {
  async categoryDistribution() {
    const token = await getAuthToken();
    return window.api.request("/api/analytics/category-distribution", { authToken: token });
  },
  async monthlyGrowth() {
    const token = await getAuthToken();
    return window.api.request("/api/analytics/monthly-growth", { authToken: token });
  },
  async stockValue() {
    const token = await getAuthToken();
    return window.api.request("/api/analytics/stock-value", { authToken: token });
  },
  async mostActiveProducts(limit = 5) {
    const token = await getAuthToken();
    return window.api.request(`/api/analytics/most-active-products?limit=${limit}`, { authToken: token });
  },
};

// ---- Reports (returns a Blob for download, needs the token attached manually) ----
window.reportsApi = {
  async download(reportType, format = "pdf") {
    const token = await getAuthToken();
    const response = await fetch(`${window.api.baseUrl}/api/reports/${reportType}?format=${format}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      let message = `Failed to generate report (status ${response.status}).`;
      try {
        const errJson = await response.json();
        message = errJson.error || message;
      } catch { /* response wasn't JSON, keep default message */ }
      throw new Error(message);
    }
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = /filename=([^;]+)/.exec(disposition);
    const filename = match ? match[1].trim() : `${reportType}_report.${format}`;
    return { blob, filename };
  },
};

// ---- AI Assistant endpoint ----
window.aiAssistantApi = {
  async ask(question) {
    const token = await getAuthToken();
    return window.api.request("/api/ai-assistant/ask", {
      method: "POST",
      authToken: token,
      body: { question },
    });
  },
};

// ---- Bulk CSV import/export ----
productsApi.exportCsv = async function () {
  const token = await getAuthToken();
  const response = await fetch(`${window.api.baseUrl}/api/products/export`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(`Export failed (status ${response.status}).`);
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = /filename=([^;]+)/.exec(disposition);
  const filename = match ? match[1].trim() : "products_export.csv";
  return { blob, filename };
};

productsApi.importCsv = async function (file) {
  const token = await getAuthToken();
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${window.api.baseUrl}/api/products/import`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  const payload = await response.json();
  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || "Import failed.");
  }
  return payload.data;
};
