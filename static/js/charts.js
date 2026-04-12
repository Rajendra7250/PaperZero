// ─── Bar Chart Renderer ────────────────────────────────────────────────────────
function renderBarChart(containerId, labels, values, color = "var(--primary)") {
  const el = document.getElementById(containerId);
  if (!el) return;

  const max = Math.max(1, ...values);
  el.innerHTML = labels
    .map((label, i) => {
      const heightPx = Math.round((values[i] / max) * 120);
      return `
        <div class="bar-col">
          <span class="bar-val">${values[i].toLocaleString()}</span>
          <div class="bar" style="height:${heightPx}px; background:${color}"></div>
          <span class="bar-label">${label}</span>
        </div>`;
    })
    .join("");
}

// ─── Progress List Renderer ───────────────────────────────────────────────────
function renderProgressList(containerId, items) {
  const el = document.getElementById(containerId);
  if (!el) return;

  el.innerHTML = items
    .map(({ label, pct }) => {
      const colorMap = pct >= 90 ? "var(--success)" : pct >= 60 ? "var(--primary)" : pct >= 40 ? "var(--accent)" : "var(--danger)";
      return `
        <div class="progress-item">
          <div class="progress-header">
            <span>${label}</span>
            <span style="font-weight:600; color:${colorMap}">${pct}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width:${pct}%; background:${colorMap}"></div>
          </div>
        </div>`;
    })
    .join("");
}
