/**
 * File: site-nav.js
 * Path: docs/templates/local-workspace/site-nav.js
 * Role: Injects a sticky top navigator across local HTML pages (copy to `.local/.../dashboards/`).
 * Used By:
 *  - index.html, implementation-control-center.html (same folder)
 *  - audits/module-audit.html via ../dashboards/site-nav.js
 * Depends On:
 *  - <html data-local-site="dashboards|audits" data-local-active="home|control|audit">
 * Notes:
 *  - Add new pages here + update data-local-active values on each HTML shell.
 */
(function () {
  "use strict";

  const site = document.documentElement.getAttribute("data-local-site") || "dashboards";
  const active = document.documentElement.getAttribute("data-local-active") || "home";

  const links =
    site === "audits"
      ? {
          home: "../dashboards/index.html",
          control: "../dashboards/implementation-control-center.html",
          audit: "module-audit.html",
        }
      : {
          home: "index.html",
          control: "implementation-control-center.html",
          audit: "../audits/module-audit.html",
        };

  const css = `
    .local-site-nav {
      position: sticky;
      top: 0;
      z-index: 9999;
      font-family: "Segoe UI", Arial, sans-serif;
      background: linear-gradient(135deg, var(--panel, #111a33), var(--panel-2, #142041));
      border-bottom: 1px solid var(--line, #2b3f73);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
      margin: 0 0 0 0;
    }
    .local-site-nav-inner {
      max-width: 1320px;
      margin: 0 auto;
      padding: 12px 18px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px 14px;
    }
    .local-site-nav-title {
      font-weight: 700;
      font-size: 0.82rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--muted, #9eb3e6);
      opacity: 0.85;
      margin-right: 6px;
    }
    .local-site-nav-count {
      font-size: 0.78rem;
      color: var(--muted, #9eb3e6);
      opacity: 0.65;
      margin-right: 8px;
    }
    .local-site-nav-pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 0 18px;
      border-radius: 12px;
      font-weight: 600;
      font-size: 0.95rem;
      text-decoration: none;
      border: 1px solid var(--line, #2b3f73);
      background: linear-gradient(180deg, #0f1a36, #0c152c);
      color: var(--muted, #9eb3e6);
      transition: border-color 0.15s, color 0.15s, background 0.15s;
    }
    .local-site-nav-pill:hover {
      border-color: var(--accent, #61b2ff);
      color: var(--text, #eaf0ff);
      background: #173064;
    }
    .local-site-nav-pill.is-active {
      border-color: var(--accent, #61b2ff);
      color: var(--text, #eaf0ff);
      background: #1a3a78;
      box-shadow: 0 0 0 1px rgba(97, 178, 255, 0.35);
      cursor: default;
    }
  `;

  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  const items = [
    { id: "home", label: "Home", href: links.home },
    { id: "control", label: "Control Center", href: links.control },
    { id: "audit", label: "Module audit", href: links.audit },
  ];

  const nav = document.createElement("nav");
  nav.className = "local-site-nav";
  nav.setAttribute("aria-label", "Local HTML navigator");

  const inner = document.createElement("div");
  inner.className = "local-site-nav-inner";

  const title = document.createElement("span");
  title.className = "local-site-nav-title";
  title.textContent = "Navigator";

  const count = document.createElement("span");
  count.className = "local-site-nav-count";
  count.textContent = "3 HTML pages";

  inner.appendChild(title);
  inner.appendChild(count);

  for (const item of items) {
    if (active === item.id) {
      const span = document.createElement("span");
      span.className = "local-site-nav-pill is-active";
      span.setAttribute("aria-current", "page");
      span.textContent = item.label;
      inner.appendChild(span);
    } else {
      const a = document.createElement("a");
      a.className = "local-site-nav-pill";
      a.href = item.href;
      a.textContent = item.label;
      inner.appendChild(a);
    }
  }

  nav.appendChild(inner);
  document.body.insertBefore(nav, document.body.firstChild);
})();
