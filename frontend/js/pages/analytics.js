/**
 * analytics.js
 * Loads real aggregated data from the backend and renders it with
 * Chart.js: category pie, stock-value bar, monthly growth bar, and
 * a most-active-products list.
 */

firebaseAuth.onAuthStateChanged((user) => {
  if (!user) {
    window.location.href = "./login.html";
    return;
  }
  document.getElementById("userEmail").textContent = user.email;
  loadAnalytics();
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

// A small, consistent palette drawn from the app's design tokens,
// used across all charts so colors feel intentional rather than
// Chart.js defaults.
const CHART_PALETTE = [
  "#2E7D5B", "#D9A441", "#C25B4A", "#8A8578", "#24614A",
  "#B58A2E", "#9C4436", "#5E5A4E", "#6FA98A", "#E0BC73",
];

// Chart.js doesn't read CSS variables on its own -- it needs explicit
// color options, and those need to flip when dark mode toggles (its
// default text color is a dark grey that's unreadable on a dark
// card background). We track live chart instances so we can destroy
// and redraw them with the right colors whenever the theme changes,
// rather than only getting it right on initial page load.
let chartInstances = [];
let lastAnalyticsData = null;

function isDarkMode() {
  return document.documentElement.getAttribute("data-theme") === "dark";
}

function chartTextColor() {
  return isDarkMode() ? "#F7F3EA" : "#0F1E17";
}

function chartGridColor() {
  return isDarkMode() ? "rgba(247, 243, 234, 0.12)" : "rgba(15, 30, 23, 0.08)";
}

function destroyExistingCharts() {
  chartInstances.forEach((chart) => chart.destroy());
  chartInstances = [];
}

// Re-render all charts with current-theme colors. Called on initial
// load and again whenever the theme toggle button is clicked.
function rerenderChartsForCurrentTheme() {
  if (!lastAnalyticsData) return;
  destroyExistingCharts();
  renderCategoryPieChart(lastAnalyticsData.categoryData);
  renderStockValueBarChart(lastAnalyticsData.stockValueData.by_category);
  renderGrowthBarChart(lastAnalyticsData.growthData);
}

const themeToggleBtn = document.getElementById("themeToggleBtn");
if (themeToggleBtn) {
  themeToggleBtn.addEventListener("click", () => {
    // theme-toggle.js flips data-theme synchronously on click, so a
    // microtask delay lets that happen first before we read it back.
    setTimeout(rerenderChartsForCurrentTheme, 0);
  });
}

async function loadAnalytics() {
  try {
    const [categoryData, stockValueData, growthData, mostActiveData] = await Promise.all([
      window.analyticsApi.categoryDistribution(),
      window.analyticsApi.stockValue(),
      window.analyticsApi.monthlyGrowth(),
      window.analyticsApi.mostActiveProducts(5),
    ]);

    lastAnalyticsData = { categoryData, stockValueData, growthData };

    renderStatHighlights(stockValueData);
    renderCategoryPieChart(categoryData);
    renderStockValueBarChart(stockValueData.by_category);
    renderGrowthBarChart(growthData);
    renderMostActiveList(mostActiveData);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderStatHighlights(stockValueData) {
  document.getElementById("statCostValue").textContent = formatCurrency(stockValueData.total_cost_value);
  document.getElementById("statRevenue").textContent = formatCurrency(stockValueData.total_potential_revenue);
  document.getElementById("statProfit").textContent = formatCurrency(stockValueData.potential_profit);
}

function renderCategoryPieChart(categoryData) {
  const ctx = document.getElementById("categoryPieChart");
  if (categoryData.length === 0) {
    ctx.parentElement.innerHTML += `<p style="color: var(--stone-500); font-size: var(--fs-sm);">No products yet.</p>`;
    return;
  }
  const chart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: categoryData.map((c) => c.category),
      datasets: [{
        data: categoryData.map((c) => c.total_quantity),
        backgroundColor: CHART_PALETTE,
        borderColor: isDarkMode() ? "#1B2B23" : "#FFFDF8",
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
          labels: { font: { family: "Inter" }, color: chartTextColor() },
        },
      },
    },
  });
  chartInstances.push(chart);
}

function renderStockValueBarChart(byCategory) {
  const ctx = document.getElementById("stockValueBarChart");
  if (byCategory.length === 0) {
    ctx.parentElement.innerHTML += `<p style="color: var(--stone-500); font-size: var(--fs-sm);">No products yet.</p>`;
    return;
  }
  const chart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: byCategory.map((c) => c.category),
      datasets: [{
        label: "Cost value (₹)",
        data: byCategory.map((c) => c.cost_value),
        backgroundColor: "#2E7D5B",
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { color: chartTextColor() }, grid: { color: chartGridColor() } },
        x: { ticks: { color: chartTextColor() }, grid: { color: chartGridColor() } },
      },
    },
  });
  chartInstances.push(chart);
}

function renderGrowthBarChart(growthData) {
  const ctx = document.getElementById("growthBarChart");
  const chart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: growthData.map((g) => g.month),
      datasets: [{
        label: "Products added",
        data: growthData.map((g) => g.products_added),
        backgroundColor: "#D9A441",
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1, color: chartTextColor() }, grid: { color: chartGridColor() } },
        x: { ticks: { color: chartTextColor() }, grid: { color: chartGridColor() } },
      },
    },
  });
  chartInstances.push(chart);
}

function renderMostActiveList(items) {
  const list = document.getElementById("mostActiveList");
  if (items.length === 0) {
    list.innerHTML = `<li style="color: var(--stone-500);">No stock decreases recorded yet — this list fills in as you use the +/- stock buttons or QR scanner.</li>`;
    return;
  }
  list.innerHTML = items.map((item) => `
    <li>
      <span>${escapeHtml(item.product_name)}</span>
      <strong class="mono">${item.total_decreased} units moved</strong>
    </li>
  `).join("");
}
