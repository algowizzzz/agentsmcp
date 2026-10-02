/* Graph model helpers and renderer shared by the builder and the run page. */
(function () {
  "use strict";
  const NODE_W = 220, NODE_H = 64, ROUTE_ROW = 24, END = "END";
  const SVGNS = "http://www.w3.org/2000/svg";

  function nodeHeight(n) {
    if (n.type !== "router") return NODE_H;
    return Math.max(NODE_H, 44 + ROUTE_ROW * ((n.routes || []).length + 1));
  }

  function leaf(n) { return n.type === "for_each" ? (n.body || {}) : n; }

  /* Outgoing connections per node, mirroring jsonflow.engine.successors. */
  function successors(def) {
    const out = {};
    const nodes = def.nodes || [];
    nodes.forEach((n, i) => {
      if (n.type === "router") {
        out[n.id] = (n.routes || []).map((r, k) => ({ to: r.goto || END, port: "r" + k }))
          .concat([{ to: n.default || END, port: "else" }]);
      } else if (Array.isArray(def.edges)) {
        out[n.id] = def.edges.filter((e) => e[0] === n.id).map((e) => ({ to: e[1], port: "out" }));
      } else {
        const nxt = n.next || (i + 1 < nodes.length ? nodes[i + 1].id : END);
        out[n.id] = [{ to: nxt, port: "out" }];
      }
    });
    return out;
  }

  /* Builder always works with explicit edges. Converts listed-order/next documents. */
  function normalize(def) {
    if (!Array.isArray(def.edges)) {
      const succ = successors(def);
      def.edges = [];
      for (const n of def.nodes || []) {
        if (n.type === "router") continue;
        for (const s of succ[n.id]) if (s.to !== END) def.edges.push([n.id, s.to]);
      }
    }
    (def.nodes || []).forEach((n) => { delete n.next; n.ui = n.ui || {}; });
    return def;
  }

  function startId(def) { return def.start || ((def.nodes || [])[0] || {}).id; }

  function incoming(def) {
    const inc = {};
    (def.nodes || []).forEach((n) => (inc[n.id] = 0));
    const succ = successors(def);
    for (const n of def.nodes || []) {
      if (n.type === "router") continue;
      for (const s of succ[n.id]) if (s.to in inc) inc[s.to] += 1;
    }
    return inc;
  }

  function autoLayout(def, force) {
    const nodes = def.nodes || [];
    if (!force && nodes.every((n) => n.ui && Number.isFinite(n.ui.x))) return false;
    const succ = successors(def), depth = {}, start = startId(def);
    const queue = start ? [start] : [];
    if (start) depth[start] = 0;
    while (queue.length) {
      const cur = queue.shift();
      for (const s of succ[cur] || []) {
        if (s.to === END || !(s.to in succ)) continue;
        if (!(s.to in depth)) { depth[s.to] = depth[cur] + 1; queue.push(s.to); }
      }
    }
    const maxD = Math.max(0, ...Object.values(depth));
    const cols = {};
    nodes.forEach((n) => {
      const d = n.id in depth ? depth[n.id] : maxD + 1;
      (cols[d] = cols[d] || []).push(n);
    });
    // Wrap depths into rows of PER_ROW columns so long chains stay readable.
    const PER_ROW = 3, rowH = {};
    Object.entries(cols).forEach(([d, list]) => {
      const r = Math.floor(Number(d) / PER_ROW);
      const hgt = list.reduce((a, n) => a + nodeHeight(n) + 40, 0);
      rowH[r] = Math.max(rowH[r] || 0, hgt);
    });
    const rowY = {}; let acc = 96;
    Object.keys(rowH).map(Number).sort((a, b) => a - b).forEach((r) => { rowY[r] = acc; acc += rowH[r] + 56; });
    Object.entries(cols).forEach(([d, list]) => {
      const r = Math.floor(Number(d) / PER_ROW), c = Number(d) % PER_ROW;
      let y = rowY[r];
      list.forEach((n) => { n.ui = n.ui || {}; n.ui.x = 80 + c * 320; n.ui.y = y; y += nodeHeight(n) + 40; });
    });
    return true;
  }

  function kindOf(n, toolCats) {
    const l = leaf(n);
    if (l.type === "llm") return "llm";
    if (l.type === "router") return "router";
    if (l.type === "transform") return "transform";
    if (l.type === "tool") {
      if (l.server === "agents") return "agents";
      return (toolCats && toolCats[l.server + "/" + l.tool]) || "other";
    }
    return "other";
  }

  function subtitle(n) {
    const l = leaf(n);
    let s = { llm: "llm" + (l.output_schema ? " · structured output" : ""), transform: "transform · " + ((l.steps || []).length) + " steps",
      router: "router · " + ((n.routes || []).length) + " route" + ((n.routes || []).length === 1 ? "" : "s"),
      tool: (l.server === "agents" ? "agent · " : "") + (l.tool || "tool") }[l.type] || l.type || "";
    if (n.type === "for_each") s = "repeat · " + s;
    return s;
  }

  function portY(n, port) {
    if (port === "out") return NODE_H / 2;
    if (port === "else") return 44 + ROUTE_ROW * (n.routes || []).length - 4;
    return 44 + ROUTE_ROW * Number(port.slice(1)) - 4;
  }

  function el(tag, attrs) {
    const e = document.createElementNS(SVGNS, tag);
    for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
    return e;
  }

  function curve(x1, y1, x2, y2) {
    if (x2 < x1 + 30) {  // target is behind: loop out, across and back in
      const my = (y1 + y2) / 2;
      return `M ${x1} ${y1} C ${x1 + 70} ${y1}, ${x1 + 70} ${my}, ${(x1 + x2) / 2} ${my} S ${x2 - 70} ${y2}, ${x2} ${y2}`;
    }
    const dx = Math.max(40, Math.abs(x2 - x1) / 2);
    return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
  }

  /* Render into `world`. Returns nothing; callers re-render on change. */
  function render(world, def, opts) {
    opts = opts || {};
    const byId = {};
    (def.nodes || []).forEach((n) => (byId[n.id] = n));
    const svg = el("svg", { class: "edges" });
    const defs = el("defs");
    for (const [name, color] of [["arrow", "#8E95A2"], ["arrow-sel", "#1F4FD1"], ["arrow-taken", "#3D63D6"], ["arrow-skip", "#C3C8D0"]]) {
      const m = el("marker", { id: name, viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" });
      m.append(el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: color }));
      defs.append(m);
    }
    svg.append(defs);
    const succ = successors(def);
    for (const n of def.nodes || []) {
      for (const s of succ[n.id] || []) {
        const t = byId[s.to];
        if (!t) continue;
        const key = n.id + "|" + s.port + "|" + s.to;
        const x1 = n.ui.x + NODE_W, y1 = n.ui.y + portY(n, s.port), x2 = t.ui.x - 2, y2 = t.ui.y + NODE_H / 2;
        const d = curve(x1, y1, x2, y2);
        const state = (opts.edgeStates || {})[key];
        const sel = opts.selectedEdge === key;
        const cls = "line" + (sel ? " sel" : "") + (state ? " " + state : "");
        const marker = sel ? "arrow-sel" : state === "taken" ? "arrow-taken" : state === "skipped" ? "arrow-skip" : "arrow";
        if (opts.onEdgeDown) {
          const hit = el("path", { d, class: "hit", "data-edge": key });
          hit.addEventListener("pointerdown", (e) => { e.stopPropagation(); opts.onEdgeDown(e, key); });
          svg.append(hit);
        }
        svg.append(el("path", { d, class: cls, "marker-end": `url(#${marker})` }));
      }
    }
    if (opts.draft) svg.append(el("path", { d: curve(opts.draft.x1, opts.draft.y1, opts.draft.x2, opts.draft.y2), class: "line sel", "stroke-dasharray": "6 4" }));

    const start = startId(def);
    const nodes = (def.nodes || []).map((n) => {
      const status = (opts.statuses || {})[n.id];
      const cls = ["node", n.type === "router" ? "router" : "", opts.selected === n.id ? "sel" : "",
        (opts.errors || new Set()).has(n.id) ? "err" : "", status ? "st-" + status : ""].filter(Boolean).join(" ");
      const card = JF.h("div", { class: cls, "data-id": n.id, style: { left: n.ui.x + "px", top: n.ui.y + "px", height: nodeHeight(n) + "px" },
        role: "button", tabindex: "0", "aria-label": n.id + ", " + subtitle(n) + (status ? ", " + status : "") },
        n.id === start ? JF.h("span", { class: "badge-start", text: "start" }) : null,
        JF.icon(n.type === "for_each" && kindOf(n, opts.toolCats) === "transform" ? "loop" : kindOf(n, opts.toolCats)),
        JF.h("span", { class: "t" }, JF.h("span", { class: "id", text: n.id }),
          JF.h("span", { class: "sub", text: (opts.subtitles && opts.subtitles[n.id]) || subtitle(n) })),
        JF.h("span", { class: "port in", "aria-hidden": "true" }));
      if (n.type === "router") {
        (n.routes || []).forEach((r, k) => {
          card.append(JF.h("span", { class: "port-label", style: { top: (portY(n, "r" + k) - 8) + "px" }, text: "if " + (k + 1) }));
          card.append(JF.h("span", { class: "port out", "data-port": "r" + k, style: { top: (portY(n, "r" + k) - 7) + "px" }, title: "Route " + (k + 1) }));
        });
        card.append(JF.h("span", { class: "port-label", style: { top: (portY(n, "else") - 8) + "px" }, text: "else" }));
        card.append(JF.h("span", { class: "port out", "data-port": "else", style: { top: (portY(n, "else") - 7) + "px" }, title: "Otherwise" }));
      } else {
        card.append(JF.h("span", { class: "port out", "data-port": "out", style: { top: (NODE_H / 2 - 7) + "px" }, title: "Drag to connect" }));
      }
      if (opts.onNodeDown) card.addEventListener("pointerdown", (e) => {
        const port = e.target.closest(".port.out");
        if (port && opts.onPortDown) { e.stopPropagation(); opts.onPortDown(e, n.id, port.dataset.port); return; }
        e.stopPropagation(); opts.onNodeDown(e, n.id);
      });
      if (opts.onNodeKey) card.addEventListener("keydown", (e) => opts.onNodeKey(e, n.id));
      if (opts.onNodeClick) card.addEventListener("click", () => opts.onNodeClick(n.id));
      return card;
    });
    world.replaceChildren(svg, ...nodes);
  }

  function bbox(def) {
    const ns = def.nodes || [];
    if (!ns.length) return { x: 0, y: 0, w: 400, h: 300 };
    const xs = ns.map((n) => n.ui.x), ys = ns.map((n) => n.ui.y);
    const x2 = Math.max(...ns.map((n) => n.ui.x + NODE_W)), y2 = Math.max(...ns.map((n) => n.ui.y + nodeHeight(n)));
    return { x: Math.min(...xs), y: Math.min(...ys), w: x2 - Math.min(...xs), h: y2 - Math.min(...ys) };
  }

  window.JFGraph = { NODE_W, NODE_H, END, nodeHeight, successors, normalize, autoLayout, startId, incoming, subtitle, kindOf, leaf, render, bbox, portY };
})();
