/**
 * SGA — Academic Management System
 * custom.js — Interactions JavaScript natives
 * Chargé automatiquement par Dash depuis /assets/
 */

(function () {
  "use strict";

  /* ─── Constantes ──────────────────────────────────────────────────────────── */
  const TRANSITION_MS = 200;
  let navGlobalsBound = false;

  /* ═══════════════════════════════════════════════════════════════════════════
     NAVIGATION DROPDOWN
     Gère l'ouverture/fermeture des dropdowns du header
     ═══════════════════════════════════════════════════════════════════════════ */
  function initNavDropdowns() {
    document.querySelectorAll(".nav-item").forEach(function (item) {
      if (item.dataset.navBound === "1") return;

      const trigger = item.querySelector(".nav-link");
      const dropdown = item.querySelector(".nav-dropdown");
      if (!trigger || !dropdown) return;

      item.dataset.navBound = "1";

      // Ouvrir au clic
      trigger.addEventListener("click", function (e) {
        e.stopPropagation();
        const isOpen = item.classList.contains("open");
        // Fermer tous les autres
        closeAllDropdowns();
        if (!isOpen) item.classList.add("open");
      });
    });

    if (!navGlobalsBound) {
      // Fermer en cliquant ailleurs
      document.addEventListener("click", closeAllDropdowns);

      // Fermer avec Escape
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeAllDropdowns();
      });

      navGlobalsBound = true;
    }
  }

  function closeAllDropdowns() {
    document.querySelectorAll(".nav-item.open").forEach(function (el) {
      el.classList.remove("open");
    });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     ACTIVE NAV LINK
     Met à jour le lien actif selon l'URL courante
     ═══════════════════════════════════════════════════════════════════════════ */
  function updateActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll(".nav-link, .nav-dropdown-item").forEach(function (el) {
      el.classList.remove("active");
      const href = el.getAttribute("href") || el.dataset.href || "";
      if (href && path.startsWith(href) && href !== "/") {
        el.classList.add("active");
        // Si c'est un dropdown item, activer aussi le parent
        const parentLink = el.closest(".nav-item")?.querySelector(".nav-link");
        if (parentLink) parentLink.classList.add("active");
      } else if (href === "/" && path === "/") {
        el.classList.add("active");
      }
    });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     TOOLTIPS LÉGERS
     Affiche un tooltip au survol des boutons avec [data-tooltip]
     ═══════════════════════════════════════════════════════════════════════════ */
  let tooltipEl = null;

  function initTooltips() {
    tooltipEl = document.createElement("div");
    tooltipEl.id = "sga-tooltip";
    tooltipEl.style.cssText = `
      position: fixed;
      background: #1c1c2e;
      color: #fff;
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 0.76rem;
      font-family: 'DM Sans', sans-serif;
      pointer-events: none;
      z-index: 9999;
      opacity: 0;
      transition: opacity 0.15s;
      white-space: nowrap;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    `;
    document.body.appendChild(tooltipEl);

    document.addEventListener("mouseover", function (e) {
      const el = e.target.closest("[data-tooltip]");
      if (!el) { hideTooltip(); return; }
      showTooltip(el.dataset.tooltip, e);
    });

    document.addEventListener("mousemove", function (e) {
      if (tooltipEl.style.opacity === "1") {
        positionTooltip(e);
      }
    });

    document.addEventListener("mouseout", function (e) {
      if (!e.target.closest("[data-tooltip]")) hideTooltip();
    });
  }

  function showTooltip(text, e) {
    tooltipEl.textContent = text;
    tooltipEl.style.opacity = "1";
    positionTooltip(e);
  }

  function positionTooltip(e) {
    const x = e.clientX + 12;
    const y = e.clientY - 32;
    tooltipEl.style.left = x + "px";
    tooltipEl.style.top  = y + "px";
  }

  function hideTooltip() {
    if (tooltipEl) tooltipEl.style.opacity = "0";
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     FEEDBACK NOTIFICATIONS (Toast)
     Usage depuis Dash : window.showToast('Message', 'success')
     Types : success | warning | danger | info
     ═══════════════════════════════════════════════════════════════════════════ */
  const TOAST_ICONS = {
    success: "fa-circle-check",
    warning: "fa-triangle-exclamation",
    danger:  "fa-circle-xmark",
    info:    "fa-circle-info",
  };

  window.showToast = function (message, type) {
    type = type || "info";
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9998;
        display: flex;
        flex-direction: column;
        gap: 8px;
        pointer-events: none;
      `;
      document.body.appendChild(container);
    }

    const iconClass = TOAST_ICONS[type] || "fa-circle-info";
    const colorMap = {
      success: "#2e7d32",
      warning: "#f57f17",
      danger:  "#c62828",
      info:    "#0277bd",
    };
    const bgMap = {
      success: "#e8f5e9",
      warning: "#fff8e1",
      danger:  "#ffebee",
      info:    "#e1f5fe",
    };

    const toast = document.createElement("div");
    toast.style.cssText = `
      display: flex;
      align-items: center;
      gap: 10px;
      background: ${bgMap[type] || "#fff"};
      color: ${colorMap[type] || "#333"};
      border: 1px solid ${colorMap[type] || "#ccc"}40;
      border-left: 3px solid ${colorMap[type] || "#333"};
      padding: 11px 16px;
      border-radius: 8px;
      font-family: 'DM Sans', sans-serif;
      font-size: 0.85rem;
      box-shadow: 0 4px 16px rgba(0,0,0,0.1);
      pointer-events: all;
      opacity: 0;
      transform: translateX(20px);
      transition: opacity 0.2s, transform 0.2s;
      min-width: 260px;
      max-width: 380px;
    `;
    toast.innerHTML = `<i class="fa-solid ${iconClass}" style="flex-shrink:0"></i><span>${message}</span>`;
    container.appendChild(toast);

    // Entrée
    requestAnimationFrame(function () {
      toast.style.opacity = "1";
      toast.style.transform = "translateX(0)";
    });

    // Sortie
    setTimeout(function () {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(20px)";
      setTimeout(function () { toast.remove(); }, TRANSITION_MS + 50);
    }, 3500);
  };

  /* ═══════════════════════════════════════════════════════════════════════════
     CONFIRMATION DIALOG
     Usage : window.confirmAction('Message ?', callbackFn)
     ═══════════════════════════════════════════════════════════════════════════ */
  window.confirmAction = function (message, onConfirm, onCancel) {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal-box" style="max-width:400px; animation: slideUp 0.2s ease;">
        <div class="modal-header">
          <span class="modal-title" style="display:flex;align-items:center;gap:9px;">
            <i class="fa-solid fa-triangle-exclamation" style="color:#f57f17"></i>
            Confirmation
          </span>
        </div>
        <p style="font-size:0.9rem;color:#555;line-height:1.6;">${message}</p>
        <div class="modal-footer">
          <button class="btn btn-ghost btn-cancel" style="cursor:pointer;">
            <i class="fa-solid fa-xmark"></i> Annuler
          </button>
          <button class="btn btn-danger btn-confirm" style="cursor:pointer;">
            <i class="fa-solid fa-trash"></i> Confirmer
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    overlay.querySelector(".btn-confirm").addEventListener("click", function () {
      overlay.remove();
      if (typeof onConfirm === "function") onConfirm();
    });
    overlay.querySelector(".btn-cancel").addEventListener("click", function () {
      overlay.remove();
      if (typeof onCancel === "function") onCancel();
    });
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) {
        overlay.remove();
        if (typeof onCancel === "function") onCancel();
      }
    });
  };

  /* ═══════════════════════════════════════════════════════════════════════════
     SEARCH BAR — Raccourci clavier
     Ctrl+K ou Cmd+K pour focus sur la recherche
     ═══════════════════════════════════════════════════════════════════════════ */
  function initSearchShortcut() {
    document.addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        const input = document.querySelector(".search-input");
        if (input) input.focus();
      }
    });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     DASH REACT OBSERVER
     Ré-initialise les scripts après chaque mise à jour du DOM par Dash
     (nécessaire car Dash rerender dynamiquement)
     ═══════════════════════════════════════════════════════════════════════════ */
  function observeDashUpdates() {
    const target = document.getElementById("page-content") || document.body;
    const observer = new MutationObserver(function () {
      updateActiveNav();
      initNavDropdowns();
    });
    observer.observe(target, { childList: true, subtree: true });
  }

  /* ═══════════════════════════════════════════════════════════════════════════
     INIT
     ═══════════════════════════════════════════════════════════════════════════ */
  function init() {
    initNavDropdowns();
    updateActiveNav();
    initTooltips();
    initSearchShortcut();
    observeDashUpdates();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Ré-init après navigation Dash (SPA)
  window.addEventListener("popstate", function () {
    updateActiveNav();
  });

})();
