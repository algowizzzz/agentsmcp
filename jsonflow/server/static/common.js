/* Shared helpers for every page. No framework; DOM is built with h(). */
(function () {
  "use strict";

  // Let null/undefined/false children mean "nothing" everywhere, as h() already does.
  for (const name of ["replaceChildren", "append", "prepend"]) {
    const orig = Element.prototype[name];
    Element.prototype[name] = function (...kids) {
      return orig.apply(this, kids.flat(Infinity).filter((k) => k !== null && k !== undefined && k !== false));
    };
  }

  const ICONS = {
    llm: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    web: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18z"/>',
    structured: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
    unstructured: '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h6"/>',
    transform: '<path d="M4 6h16M7 12h10M10 18h4"/>',
    loop: '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a3 3 0 0 1 3-3h15"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v2a3 3 0 0 1-3 3H3"/>',
    router: '<path d="M6 3v12"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
    agents: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>',
    other: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    check: '<path d="M5 12l5 5L20 7"/>',
    play: '<path d="M6 4l14 8-14 8z"/>',
  };

  function svg(kind, extra) {
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("viewBox", "0 0 24 24");
    s.setAttribute("fill", kind === "play" ? "currentColor" : "none");
    s.setAttribute("stroke", "currentColor");
    s.setAttribute("stroke-width", "2");
    s.setAttribute("stroke-linecap", "round");
    s.setAttribute("stroke-linejoin", "round");
    s.setAttribute("aria-hidden", "true");
    s.innerHTML = ICONS[kind] || ICONS.other; // static, trusted markup only
    if (extra) Object.entries(extra).forEach(([k, v]) => s.setAttribute(k, v));
    return s;
  }

  function icon(kind) {
    const cls = { loop: "transform" }[kind] || kind;
    return h("span", { class: "ico " + cls }, svg(kind));
  }

  function h(tag, attrs, ...children) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === undefined || v === null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k === "style" && typeof v === "object") Object.assign(el.style, v);
      else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
      else if (k === "value") el.value = v;
      else if (k === "checked") el.checked = !!v;
      else if (v === true) el.setAttribute(k, "");
      else el.setAttribute(k, v);
    }
    for (const c of children.flat(Infinity)) {
      if (c === null || c === undefined || c === false) continue;
      el.append(c instanceof Node ? c : document.createTextNode(String(c)));
    }
    return el;
  }

  async function api(path, opts) {
    opts = opts || {};
    const init = { method: opts.method || "GET", headers: { "X-Requested-With": "jsonflow" }, credentials: "same-origin" };
    if (opts.body !== undefined) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(opts.body);
    }
    const r = await fetch(path, init);
    let data = null;
    try { data = await r.json(); } catch (e) { data = null; }
    if (r.status === 401 && !opts.allow401 && location.pathname.startsWith("/app")) {
      location.href = "/login?next=" + encodeURIComponent(location.pathname + location.search);
      throw new Error("Sign in required.");
    }
    if (!r.ok) {
      const err = new Error((data && data.error) || ("Request failed (" + r.status + ")"));
      err.status = r.status;
      throw err;
    }
    return data;
  }

  function toast(message, bad) {
    let box = document.querySelector(".toasts");
    if (!box) { box = h("div", { class: "toasts", role: "status", "aria-live": "polite" }); document.body.append(box); }
    const t = h("div", { class: "toast" + (bad ? " bad" : ""), text: message });
    box.append(t);
    setTimeout(() => t.remove(), bad ? 7000 : 3500);
  }

  function modal(opts) {
    const prev = document.activeElement;
    const back = h("div", { class: "modal-back" });
    const close = () => { back.remove(); document.removeEventListener("keydown", onKey); if (prev && prev.focus) prev.focus(); };
    const onKey = (e) => { if (e.key === "Escape") close(); };
    const actions = (opts.actions || [{ label: "Close" }]).map((a) =>
      h("button", { type: "button", class: "btn" + (a.primary ? " primary" : "") + (a.danger ? " danger" : ""),
        onclick: async () => { if (a.onClick) { const keep = await a.onClick(close); if (keep === true) return; } close(); } }, a.label));
    const box = h("div", { class: "modal" + (opts.wide ? " wide" : ""), role: "dialog", "aria-modal": "true", "aria-label": opts.title },
      h("h2", { text: opts.title }), opts.body, h("div", { class: "modal-actions" }, actions));
    back.append(box);
    back.addEventListener("mousedown", (e) => { if (e.target === back) close(); });
    document.addEventListener("keydown", onKey);
    document.body.append(back);
    const first = box.querySelector("input, select, textarea, button");
    if (first) first.focus();
    return close;
  }

  function field(label, control, hint) {
    return h("label", { class: "field" }, h("span", { class: "lbl", text: label }), control, hint ? h("span", { text: hint }) : null);
  }

  function ago(iso) {
    if (!iso) return "never";
    const s = (Date.now() - new Date(iso).getTime()) / 1000;
    if (s < 60) return "just now";
    if (s < 3600) return Math.round(s / 60) + " min ago";
    if (s < 86400) return Math.round(s / 3600) + " h ago";
    return new Date(iso).toLocaleDateString();
  }

  function statusChip(status) {
    const cls = { succeeded: "ok", failed: "bad", running: "info", queued: "info" }[status] || "";
    return h("span", { class: "chip " + cls, text: status || "no runs" });
  }

  function pretty(v) { return JSON.stringify(v, null, 2); }

  function jsonBlock(v) { return h("pre", { class: "json", text: v === undefined ? "" : pretty(v) }); }

  async function topbar(active, opts) {
    opts = opts || {};
    const bar = document.getElementById("topbar");
    let user = null;
    try { user = (await api("/api/session")).user; } catch (e) { user = null; }
    if (!user && opts.requireUser) {
      location.href = "/login?next=" + encodeURIComponent(location.pathname + location.search);
      return null;
    }
    const link = (href, label, key) => h("a", { href, class: active === key ? "active" : "", text: label });
    const nav = user
      ? [link("/app", "Agents", "agents"), user.role === "super_admin" ? link("/app/admin", "Admin", "admin") : null,
         link("/guide", "Guide", "guide"), link("/", "About", "home")]
      : [link("/", "Product", "home"), link("/guide", "Guide", "guide")];
    const right = user
      ? h("div", { class: "who" },
          h("span", { text: user.display_name || user.username }),
          h("span", { class: "role " + user.role, text: user.role === "super_admin" ? "Super admin" : "Admin" }),
          h("button", { type: "button", class: "btn small", onclick: changePassword }, "Password"),
          h("button", { type: "button", class: "btn small", onclick: async () => { await api("/api/auth/logout", { method: "POST" }); location.href = "/"; } }, "Sign out"))
      : h("div", { class: "who" }, h("a", { class: "btn primary small", href: "/login", text: "Sign in" }));
    bar.replaceChildren(
      h("a", { class: "brand", href: user ? "/app" : "/" }, h("span", { class: "brand-mark", text: "{ }" }), h("span", { text: "jsonflow" })),
      h("nav", { class: "nav", "aria-label": "Main" }, nav), h("div", { class: "grow" }), right);
    return user;
  }

  function changePassword() {
    const cur = h("input", { class: "input", type: "password", autocomplete: "current-password" });
    const nw = h("input", { class: "input", type: "password", autocomplete: "new-password" });
    modal({
      title: "Change password",
      body: h("div", { class: "stack" }, field("Current password", cur),
        field("New password", nw, "At least 10 characters with upper and lower case and a digit.")),
      actions: [{ label: "Cancel" }, { label: "Change", primary: true, onClick: async () => {
        try { await api("/api/me/password", { method: "POST", body: { current: cur.value, new: nw.value } });
          toast("Password changed. Sign in again."); setTimeout(() => (location.href = "/login"), 900);
        } catch (e) { toast(e.message, true); return true; }
      } }],
    });
  }

  window.JF = { h, api, toast, modal, field, ago, statusChip, pretty, jsonBlock, topbar, icon, svg };
})();
