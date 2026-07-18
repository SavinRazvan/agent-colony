/**
 * File: local-board-snapshot.js
 * Path: .ai_infra/templates/local-workspace/local-board-snapshot.js
 * Role: Read-only renderer for project-board-snapshot JSON in Implementation Control Center.
 * Used By:
 *  - implementation-control-center.html
 * Depends On:
 *  - local-markdown.js (escapeHtml)
 * Notes:
 *  - Reads `.local/generated-data/project-board-snapshot.json` only; never writes board Status.
 *  - Copy to `.local/agents-control-center/dashboards/` with other dashboard assets.
 */
(function (global) {
  "use strict";

  function escapeHtml(value) {
    if (global.LocalMarkdown && typeof global.LocalMarkdown.escapeHtml === "function") {
      return global.LocalMarkdown.escapeHtml(value);
    }
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function displayCell(value) {
    if (value === null || value === undefined || value === "") {
      return '<span class="local-board-empty">—</span>';
    }
    return escapeHtml(String(value));
  }

  function statusClass(status) {
    const normalized = String(status || "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, "-");
    return normalized ? " local-board-status-" + normalized : "";
  }

  function renderHeader(project, totalCount) {
    const name = project && project.name ? escapeHtml(project.name) : "Project";
    const count = typeof totalCount === "number" ? totalCount : 0;
    const url = project && project.url ? String(project.url) : "";
    let titleHtml = name;
    if (url) {
      const safeUrl = escapeHtml(url);
      titleHtml =
        '<a href="' +
        safeUrl +
        '" target="_blank" rel="noopener noreferrer">' +
        name +
        "</a>";
    }
    return (
      '<header class="local-board-head">' +
      "<h2>" +
      titleHtml +
      "</h2>" +
      '<p class="local-board-meta">' +
      "<span>Total items: <strong>" +
      escapeHtml(String(count)) +
      "</strong></span>" +
      '<span class="local-pill local-board-readonly">read-only snapshot</span>' +
      "</p>" +
      "</header>"
    );
  }

  function renderEmptyItems() {
    return (
      '<div class="local-board-empty-state">' +
      "<p>No board items in this snapshot.</p>" +
      "<p>Run <code>python3 -m cursor_workflow project export</code> after updating cards on GitHub.</p>" +
      "</div>"
    );
  }

  function renderRow(item, index) {
    const excerpt = item && item.body_excerpt ? String(item.body_excerpt) : "";
    let excerptHtml = "";
    if (excerpt.trim()) {
      excerptHtml =
        '<details class="local-board-excerpt">' +
        "<summary>Body excerpt</summary>" +
        "<pre>" +
        escapeHtml(excerpt) +
        "</pre>" +
        "</details>";
    }
    return (
      "<tr>" +
      "<td>" +
      displayCell(item && item.title) +
      "</td>" +
      '<td><span class="local-board-status' +
      statusClass(item && item.status_normalized) +
      '">' +
      displayCell(item && item.status_normalized) +
      "</span></td>" +
      "<td>" +
      displayCell(item && item.priority) +
      "</td>" +
      "<td>" +
      displayCell(item && item.size) +
      "</td>" +
      "<td>" +
      displayCell(item && item.estimate) +
      "</td>" +
      "<td>" +
      displayCell(item && item.updated_at) +
      "</td>" +
      "<td>" +
      excerptHtml +
      "</td>" +
      "</tr>"
    );
  }

  function renderTable(items) {
    if (!items.length) {
      return renderEmptyItems();
    }
    let html =
      '<div class="local-board-table-wrap">' +
      "<table>" +
      "<thead><tr>" +
      "<th>Title</th>" +
      "<th>Status</th>" +
      "<th>Priority</th>" +
      "<th>Size</th>" +
      "<th>Estimate</th>" +
      "<th>Updated</th>" +
      "<th>Excerpt</th>" +
      "</tr></thead><tbody>";
    for (let i = 0; i < items.length; i += 1) {
      html += renderRow(items[i], i);
    }
    html += "</tbody></table></div>";
    return html;
  }

  function renderSnapshot(snapshot) {
    const data = snapshot && typeof snapshot === "object" ? snapshot : {};
    const project = data.project || {};
    const items = Array.isArray(data.items) ? data.items : [];
    const totalCount =
      typeof data.totalCount === "number" ? data.totalCount : items.length;
    return (
      '<div class="local-board-panel">' +
      renderHeader(project, totalCount) +
      renderTable(items) +
      "</div>"
    );
  }

  function renderMissingExport() {
    return (
      '<div class="local-board-missing">' +
      '<p class="status-bad">Project board snapshot not found.</p>' +
      "<p>Export a read-only snapshot from the CLI:</p>" +
      "<pre><code>python3 -m cursor_workflow project export</code></pre>" +
      "<p>Output path: <code>.local/generated-data/project-board-snapshot.json</code></p>" +
      "</div>"
    );
  }

  global.LocalBoardSnapshot = {
    render: renderSnapshot,
    renderMissingExport: renderMissingExport,
    escapeHtml: escapeHtml,
  };
})(typeof window !== "undefined" ? window : globalThis);
