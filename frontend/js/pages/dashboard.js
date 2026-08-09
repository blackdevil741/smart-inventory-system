/**
 * dashboard.js
 * Loads and renders the summary cards, low-stock list, and recent
 * activity feed from the real backend/Firestore data.
 */

firebaseAuth.onAuthStateChanged((user) => {
  if (!user) {
    window.location.href = "./login.html";
    return;
  }
  document.getElementById("userEmail").textContent = user.email;
  loadDashboard();
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await firebaseAuth.signOut();
  window.location.href = "./login.html";
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function formatCurrency(amount) {
  return `₹${Number(amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const ACTION_LABELS = {
  created: "added",
  updated: "updated",
  deleted: "removed",
  stock_increased: "increased stock for",
  stock_decreased: "decreased stock for",
};

function timeAgo(isoString) {
  const then = new Date(isoString).getTime();
  const now = Date.now();
  const diffSec = Math.max(0, Math.floor((now - then) / 1000));

  if (diffSec < 60) return "just now";
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

function renderLowStockList(items) {
  const list = document.getElementById("lowStockList");
  if (items.length === 0) {
    list.innerHTML = `<li class="dashboard-empty">Nothing needs attention — all stock levels look healthy.</li>`;
    return;
  }
  list.innerHTML = items.map((item) => `
    <li>
      <span>${escapeHtml(item.name)}</span>
      <strong style="color: ${item.quantity <= 0 ? 'var(--terracotta-700)' : '#8a6417'};">
        ${item.quantity} ${item.quantity <= 0 ? "(out of stock)" : "left"}
      </strong>
    </li>
  `).join("");
}

function renderActivityList(entries) {
  const list = document.getElementById("activityList");
  if (entries.length === 0) {
    list.innerHTML = `<li class="dashboard-empty">No activity yet — changes to your inventory will show up here.</li>`;
    return;
  }
  list.innerHTML = entries.map((entry) => `
    <li>
      <div class="activity-icon ${entry.action_type}">${(entry.action_type || "?")[0].toUpperCase()}</div>
      <div>
        <div>You ${ACTION_LABELS[entry.action_type] || "updated"} <strong>${escapeHtml(entry.product_name)}</strong></div>
        <div class="activity-meta">${timeAgo(entry.timestamp)}${entry.note ? " · " + escapeHtml(entry.note) : ""}</div>
      </div>
    </li>
  `).join("");
}

async function loadDashboard() {
  try {
    const summary = await window.dashboardApi.getSummary();
    document.getElementById("cardTotalProducts").textContent = summary.total_products;
    document.getElementById("cardLowStock").textContent = summary.low_stock_count;
    document.getElementById("cardOutOfStock").textContent = summary.out_of_stock_count;
    document.getElementById("cardCategories").textContent = summary.category_count;
    document.getElementById("cardStockValue").textContent = formatCurrency(summary.total_stock_value);
    renderLowStockList(summary.low_stock_items);
  } catch (err) {
    showToast(err.message, "error");
  }

  try {
    const activity = await window.dashboardApi.getActivity(15);
    renderActivityList(activity);
  } catch (err) {
    document.getElementById("activityList").innerHTML =
      `<li class="dashboard-empty">Couldn't load activity: ${escapeHtml(err.message)}</li>`;
  }
}
