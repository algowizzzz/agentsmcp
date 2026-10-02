/* Agent builder: palette, canvas and inspector over one workflow document. */
(function () {
  "use strict";
  const { h, api, toast, modal, field } = JF;
  const G = JFGraph;
  const END = G.END;

  const S = {
    agent: null, def: null, version: 0, dirty: false, user: null,
    palette: null, toolInfo: {}, toolCats: {}, sel: null, scale: 1,
    problems: { errors: [], warnings: [] }, errorIds: new Set(), draft: null, palQuery: "",
  };

  const TRANSFORM_FIELDS = {
    flatten: [{ k: "path", t: "text", ph: "results", help: "Field holding a list in each item. Leave empty for a list of lists." }],
    filter: [{ k: "when", t: "cond" }],
    dedupe: [{ k: "key", t: "text", ph: "url" }, { k: "normalize", t: "select", opts: ["none", "url", "text"] }],
    sort: [{ k: "by", t: "json", ph: '[{"key": "score", "order": "desc"}]', help: 'Keys in priority order. Add "rank": {"high": 3, "medium": 2} to order words.' }],
    limit: [{ k: "n", t: "value", type: "integer" }],
    enumerate: [{ k: "field", t: "text", ph: "rank" }, { k: "start", t: "number" }],
    map: [{ k: "fields", t: "json", ph: '{"title": "{{ item.title }}"}' }, { k: "merge", t: "bool", label: "Keep existing fields" }],
    pick: [{ k: "fields", t: "list", ph: "title, url" }],
    lookup: [{ k: "from", t: "value", type: "array" }, { k: "field", t: "text", ph: "source_refs" }, { k: "match", t: "text", ph: "ref" },
      { k: "as", t: "text", ph: "sources" }, { k: "single", t: "bool", label: "Attach one match, not a list" }],
    render: [{ k: "template", t: "json", ph: '{"count": "{{ value | length }}"}' }],
  };
  const UNARY = new Set(["empty", "not_empty", "truthy", "falsy"]);

  // ================================================================ helpers
  const agentId = () => decodeURIComponent(location.pathname.split("/").pop());
  const node = (id) => S.def.nodes.find((n) => n.id === id);
  const leaf = (n) => (n.type === "for_each" ? n.body : n);
  const clone = (v) => JSON.parse(JSON.stringify(v));

  function markDirty() {
    S.dirty = true;
    document.getElementById("dirty").classList.remove("hidden");
  }

  function uniqueId(base) {
    let b = String(base || "step").replace(/[^A-Za-z0-9_]/g, "_").replace(/^_+|_+$/g, "").slice(0, 40) || "step";
    if (!/^[A-Za-z_]/.test(b)) b = "n_" + b;
    let id = b, i = 2;
    while (S.def.nodes.some((n) => n.id === id)) id = b + "_" + i++;
    return id;
  }

  function sourcesFor(n, inLoop) {
    const out = [];
    for (const k of Object.keys(S.def.inputs || {})) out.push("inputs." + k);
    if (inLoop && n.type === "for_each") { out.push(n.as || "item", "index"); }
    for (const o of S.def.nodes) {
      if (o.id === n.id) continue;
      out.push("nodes." + o.id);
      const l = leaf(o);
      const props = l.output_schema && l.output_schema.properties;
      if (props) Object.keys(props).forEach((p) => out.push("nodes." + o.id + "." + p));
    }
    out.push("run.date", "run.id");
    return out;
  }

  // ================================================================ render
  function renderCanvas() {
    const world = document.getElementById("world");
    world.style.transform = `scale(${S.scale})`;
    document.getElementById("z-val").textContent = Math.round(S.scale * 100) + "%";
    G.render(world, S.def, {
      selected: S.sel && S.sel.type === "node" ? S.sel.id : null,
      selectedEdge: S.sel && S.sel.type === "edge" ? S.sel.id : null,
      errors: S.errorIds, toolCats: S.toolCats, draft: S.draft,
      onNodeDown: nodeDown, onPortDown: portDown, onEdgeDown: (e, key) => select({ type: "edge", id: key }),
      onNodeKey: (e, id) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select({ type: "node", id }); } },
    });
  }

  function renderHeader() {
    const a = S.agent;
    document.getElementById("agent-name").textContent = S.def.name || a.id;
    document.title = (S.def.name || a.id) + " · Builder · jsonflow";
    document.getElementById("agent-meta").replaceChildren(
      h("span", { class: "mono muted", text: a.id }), h("span", { class: "chip", text: S.def.category || a.category }),
      h("span", { class: "chip", text: "v" + S.version }),
      a.published ? h("span", { class: "chip pub", text: "Published" }) : h("span", { class: "chip", text: "Draft" }));
    document.getElementById("btn-publish").textContent = a.published ? "Unpublish" : "Publish";
  }

  function select(sel) {
    S.sel = sel;
    renderCanvas();
    renderInspector();
  }

  function renderProblems() {
    const box = document.getElementById("problems");
    const { errors, warnings } = S.problems;
    S.errorIds = new Set();
    const ids = new Set(S.def.nodes.map((n) => n.id));
    const idOf = (msg) => { const m = /^([A-Za-z_][A-Za-z0-9_]*)[.:]/.exec(msg); return m && ids.has(m[1]) ? m[1] : null; };
    errors.forEach((e) => { const id = idOf(e); if (id) S.errorIds.add(id); });
    if (!errors.length && !warnings.length) { box.classList.add("hidden"); return; }
    box.classList.remove("hidden");
    const item = (msg, cls) => {
      const id = idOf(msg);
      return h("li", { class: cls, tabindex: id ? "0" : null, onclick: () => id && select({ type: "node", id }),
        onkeydown: (e) => { if (id && e.key === "Enter") select({ type: "node", id }); } }, msg);
    };
    box.replaceChildren(h("div", { class: "row" }, h("b", { text: errors.length + " problem" + (errors.length === 1 ? "" : "s") + ", " + warnings.length + " warning" + (warnings.length === 1 ? "" : "s") }),
      h("div", { class: "grow" }), h("button", { class: "btn small ghost", type: "button", onclick: () => box.classList.add("hidden") }, "Hide")),
      h("ul", { style: { margin: "6px 0 0", paddingLeft: "18px" } }, errors.map((e) => item(e, "e")), warnings.map((w) => item(w, "w"))));
  }

  // ================================================================ palette
  function renderPalette() {
    const list = document.getElementById("pal-list");
    const q = S.palQuery.toLowerCase();
    const groups = [];
    const logic = S.palette.logic.filter((x) => !q || (x.label + x.description).toLowerCase().includes(q));
    if (logic.length) groups.push(["Logic", logic.map((x) => ({ kind: x.type, name: x.label, desc: x.description, tpl: { type: x.type } }))]);
    const labels = { web: "Web", structured: "Structured data", unstructured: "Documents", agents: "Agents", other: "Other" };
    for (const cat of S.palette.category_order) {
      const tools = (S.palette.categories[cat] || []).filter((t) => !q || (t.tool + " " + t.description + " " + (t.raw_category || "")).toLowerCase().includes(q));
      if (tools.length) groups.push([labels[cat] + " · " + tools.length, tools.map((t) => ({ kind: cat, name: t.tool, desc: (cat === "agents" ? "[" + t.raw_category + "] " : "") + t.description, tpl: t.node_template }))]);
    }
    list.replaceChildren(...groups.flatMap(([title, items]) => [h("div", { class: "pal-group", text: title }),
      ...items.map((it) => {
        const b = h("button", { type: "button", class: "pal-item", draggable: "true", title: it.desc, onclick: () => addNode(it.tpl) },
          JF.icon(it.kind), h("span", { class: "grow" }, h("div", { class: "nm", text: it.name }), h("div", { class: "ds", text: it.desc })));
        b.addEventListener("dragstart", (e) => { e.dataTransfer.setData("application/x-jsonflow", JSON.stringify(it.tpl)); e.dataTransfer.effectAllowed = "copy"; });
        return b;
      })]));
    if (!groups.length) list.append(h("p", { class: "small muted", style: { padding: "8px" }, text: "Nothing matches." }));
    const errs = Object.entries(S.palette.errors || {});
    document.getElementById("pal-status").replaceChildren(...(errs.length ? errs.map(([s, e]) => h("div", { class: "notice bad small", text: s + " is unreachable: " + e }))
      : [h("span", { text: Object.values(S.palette.categories).reduce((a, b) => a + b.length, 0) + " tools available" })]));
  }

  async function loadPalette(refresh) {
    S.palette = await api("/api/palette" + (refresh ? "?refresh=1" : ""));
    S.toolInfo = {}; S.toolCats = {};
    for (const [cat, tools] of Object.entries(S.palette.categories)) {
      for (const t of tools) { S.toolInfo[t.server + "/" + t.tool] = t; S.toolCats[t.server + "/" + t.tool] = cat; }
    }
    renderPalette();
  }

  function newNodeFrom(tpl, x, y) {
    let n;
    if (tpl.type === "tool") n = { id: uniqueId(tpl.tool), type: "tool", server: tpl.server, tool: tpl.tool, args: {} };
    else if (tpl.type === "llm") n = { id: uniqueId("llm"), type: "llm", prompt: "" };
    else if (tpl.type === "transform") n = { id: uniqueId("transform"), type: "transform", input: "", steps: [] };
    else if (tpl.type === "router") n = { id: uniqueId("router"), type: "router", routes: [{ when: { left: "", op: "truthy" }, goto: END }], default: END };
    else return null;
    n.ui = { x: Math.round(x / 8) * 8, y: Math.round(y / 8) * 8 };
    return n;
  }

  function addNode(tpl, x, y) {
    if (x === undefined) {
      const wrap = document.getElementById("canvas");
      x = (wrap.scrollLeft + wrap.clientWidth / 2) / S.scale - G.NODE_W / 2;
      y = (wrap.scrollTop + wrap.clientHeight / 2) / S.scale - G.NODE_H / 2;
    }
    const n = newNodeFrom(tpl, x, y);
    if (!n) return;
    S.def.nodes.push(n);
    if (S.def.nodes.length === 1) S.def.start = n.id;
    markDirty();
    select({ type: "node", id: n.id });
  }

  // ================================================================ canvas interactions
  function worldPoint(e) {
    const r = document.getElementById("world").getBoundingClientRect();
    return { x: (e.clientX - r.left) / S.scale, y: (e.clientY - r.top) / S.scale };
  }

  function nodeDown(e, id) {
    const n = node(id), p0 = worldPoint(e), ox = p0.x - n.ui.x, oy = p0.y - n.ui.y;
    let moved = false;
    const move = (ev) => {
      const p = worldPoint(ev);
      const nx = Math.max(0, Math.round((p.x - ox) / 8) * 8), ny = Math.max(0, Math.round((p.y - oy) / 8) * 8);
      if (nx !== n.ui.x || ny !== n.ui.y) { n.ui.x = nx; n.ui.y = ny; moved = true; renderCanvas(); }
    };
    const up = () => {
      window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up);
      if (moved) markDirty();
      if (!moved || !S.sel || S.sel.id !== id) select({ type: "node", id });
    };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
  }

  function portDown(e, id, port) {
    const n = node(id);
    const x1 = n.ui.x + G.NODE_W, y1 = n.ui.y + G.portY(n, port);
    S.draft = { x1, y1, x2: x1, y2: y1 };
    const move = (ev) => { const p = worldPoint(ev); S.draft.x2 = p.x; S.draft.y2 = p.y; renderCanvas(); };
    const up = (ev) => {
      window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up);
      S.draft = null;
      const target = document.elementFromPoint(ev.clientX, ev.clientY);
      const card = target && target.closest && target.closest(".node");
      if (card && card.dataset.id !== id) connect(id, port, card.dataset.id);
      else renderCanvas();
    };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
  }

  function connect(from, port, to) {
    const n = node(from);
    if (port === "out") {
      if (S.def.edges.some((e) => e[0] === from && e[1] === to)) { renderCanvas(); return; }
      S.def.edges.push([from, to]);
    } else if (port === "else") n.default = to;
    else n.routes[Number(port.slice(1))].goto = to;
    markDirty();
    select({ type: "edge", id: from + "|" + port + "|" + to });
  }

  function deleteEdge(key) {
    const [from, port, to] = key.split("|");
    const n = node(from);
    if (!n) return;
    if (port === "out") S.def.edges = S.def.edges.filter((e) => !(e[0] === from && e[1] === to));
    else if (port === "else") n.default = END;
    else n.routes[Number(port.slice(1))].goto = END;
    markDirty();
    select(null);
  }

  function deleteNode(id) {
    S.def.nodes = S.def.nodes.filter((n) => n.id !== id);
    S.def.edges = S.def.edges.filter((e) => e[0] !== id && e[1] !== id);
    for (const n of S.def.nodes) {
      if (n.type !== "router") continue;
      (n.routes || []).forEach((r) => { if (r.goto === id) r.goto = END; });
      if (n.default === id) n.default = END;
    }
    if (S.def.start === id) S.def.start = S.def.nodes.length ? S.def.nodes[0].id : undefined;
    markDirty();
    select(null);
  }

  function renameNode(oldId, newId) {
    if (newId === oldId) return true;
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(newId) || newId === "END") { toast("Ids use letters, digits and underscores, and start with a letter.", true); return false; }
    if (S.def.nodes.some((n) => n.id === newId)) { toast("Another step already uses that id.", true); return false; }
    const re = new RegExp("nodes\\." + oldId + "(?![A-Za-z0-9_])", "g");
    const nodes = JSON.parse(JSON.stringify(S.def.nodes).replace(re, "nodes." + newId));
    const output = S.def.output == null ? S.def.output : JSON.parse(JSON.stringify(S.def.output).replace(re, "nodes." + newId));
    nodes.forEach((n) => {
      if (n.id === oldId) n.id = newId;
      if (n.type === "router") { (n.routes || []).forEach((r) => { if (r.goto === oldId) r.goto = newId; }); if (n.default === oldId) n.default = newId; }
    });
    S.def.nodes = nodes; S.def.output = output;
    S.def.edges = S.def.edges.map(([a, b]) => [a === oldId ? newId : a, b === oldId ? newId : b]);
    if (S.def.start === oldId) S.def.start = newId;
    markDirty();
    S.sel = { type: "node", id: newId };
    renderCanvas();
    return true;
  }

  function setupCanvas() {
    const wrap = document.getElementById("canvas");
    wrap.addEventListener("dragover", (e) => { if (e.dataTransfer.types.includes("application/x-jsonflow")) { e.preventDefault(); e.dataTransfer.dropEffect = "copy"; } });
    wrap.addEventListener("drop", (e) => {
      const raw = e.dataTransfer.getData("application/x-jsonflow");
      if (!raw) return;
      e.preventDefault();
      const p = worldPoint(e);
      addNode(JSON.parse(raw), p.x - G.NODE_W / 2, p.y - G.NODE_H / 2);
    });
    wrap.addEventListener("pointerdown", (e) => {
      if (e.target.closest(".node, .canvas-tools, path.hit")) return;
      const sx = e.clientX, sy = e.clientY, l = wrap.scrollLeft, t = wrap.scrollTop;
      let moved = false;
      const move = (ev) => {
        if (Math.abs(ev.clientX - sx) + Math.abs(ev.clientY - sy) > 3) { moved = true; wrap.classList.add("panning"); }
        wrap.scrollLeft = l - (ev.clientX - sx); wrap.scrollTop = t - (ev.clientY - sy);
      };
      const up = () => {
        window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up);
        wrap.classList.remove("panning");
        if (!moved) select(null);
      };
      window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
    });
    const zoom = (f) => { S.scale = Math.min(1.6, Math.max(0.4, Math.round(S.scale * f * 10) / 10)); renderCanvas(); };
    document.getElementById("z-in").onclick = () => zoom(1.15);
    document.getElementById("z-out").onclick = () => zoom(1 / 1.15);
    document.getElementById("z-fit").onclick = fit;
    document.getElementById("z-tidy").onclick = () => { G.autoLayout(S.def, true); markDirty(); renderCanvas(); fit(); };
  }

  function fit() {
    const wrap = document.getElementById("canvas"), b = G.bbox(S.def);
    S.scale = Math.min(1.2, Math.max(0.4, Math.min((wrap.clientWidth - 80) / (b.w + 80), (wrap.clientHeight - 80) / (b.h + 120))));
    S.scale = Math.round(S.scale * 20) / 20;
    renderCanvas();
    wrap.scrollLeft = Math.max(0, (b.x - 40) * S.scale);
    wrap.scrollTop = Math.max(0, (b.y - 60) * S.scale);
  }

  // ================================================================ value fields (three modes)
  const PICK_RE = /^\{\{\s*([A-Za-z_][\w.]*(?:\[-?\d+\])*)\s*\}\}$/;

  function inferMode(value, sources) {
    if (typeof value === "string") {
      const m = PICK_RE.exec(value);
      if (m && sources.includes(m[1])) return "pick";
      if (value.includes("{{")) return "expr";
    }
    return "fixed";
  }

  /* opts: {label, help, required, type, enumVals, get(), set(v), sources, modes, modeKey} */
  function valueField(opts) {
    const wrap = h("div", { class: "arg" });
    const draw = () => {
      const value = opts.get();
      const mode = (opts.modes && opts.modes[opts.modeKey]) || inferMode(value, opts.sources);
      const setMode = (m) => {
        if (opts.modes) opts.modes[opts.modeKey] = m;
        const v = opts.get();
        if (m === "pick" && !(typeof v === "string" && PICK_RE.test(v))) opts.set(undefined);
        if (m === "fixed" && typeof v === "string" && v.includes("{{")) opts.set(undefined);
        if (m === "expr" && v !== undefined && typeof v !== "string") opts.set("{{ " + JSON.stringify(v) + " }}");
        markDirty(); draw();
      };
      const seg = h("div", { class: "seg", role: "group", "aria-label": "How " + opts.label + " is set" },
        [["fixed", "Fixed value"], ["pick", "Pick from data"], ["expr", "Expression"]].map(([m, l]) =>
          h("button", { type: "button", "aria-pressed": mode === m ? "true" : "false", onclick: () => setMode(m) }, l)));
      let control;
      const fid = "f" + Math.random().toString(36).slice(2, 9);
      if (mode === "pick") {
        const cur = typeof value === "string" ? (PICK_RE.exec(value) || [])[1] : "";
        control = h("select", { id: fid, class: "input expr", onchange: (e) => { opts.set(e.target.value ? "{{ " + e.target.value + " }}" : undefined); markDirty(); renderCanvas(); } },
          h("option", { value: "", text: "Choose a value…" }), opts.sources.map((s) => h("option", { value: s, text: s, selected: s === cur })));
      } else if (mode === "expr") {
        control = h("input", { id: fid, class: "input expr", value: typeof value === "string" ? value : "", placeholder: "{{ nodes.step.field | default([]) }}",
          oninput: (e) => { opts.set(e.target.value === "" ? undefined : e.target.value); markDirty(); } });
      } else {
        control = fixedControl(fid, opts, value);
      }
      wrap.replaceChildren(
        h("div", { class: "row", style: { flexWrap: "wrap" } }, h("label", { for: fid, class: "arg-name", text: opts.label }),
          opts.required ? h("span", { class: "req", text: "required" }) : null, opts.type ? h("span", { class: "small muted", text: opts.type }) : null),
        seg, control, opts.help ? h("div", { class: "small muted", text: opts.help }) : null);
    };
    draw();
    return wrap;
  }

  function fixedControl(fid, opts, value) {
    const set = (v) => { opts.set(v); markDirty(); renderCanvas(); };
    const t = opts.type;
    if (opts.enumVals) {
      return h("select", { id: fid, class: "input", onchange: (e) => set(e.target.value === "" ? undefined : e.target.value) },
        h("option", { value: "", text: "(not set)" }), opts.enumVals.map((v) => h("option", { value: v, text: v, selected: v === value })));
    }
    if (t === "boolean") {
      return h("select", { id: fid, class: "input", onchange: (e) => set(e.target.value === "" ? undefined : e.target.value === "true") },
        h("option", { value: "", text: "(not set)" }), h("option", { value: "true", text: "true", selected: value === true }), h("option", { value: "false", text: "false", selected: value === false }));
    }
    if (t === "integer" || t === "number") {
      return h("input", { id: fid, class: "input mono", type: "number", step: t === "integer" ? "1" : "any", value: typeof value === "number" ? String(value) : "",
        oninput: (e) => set(e.target.value === "" ? undefined : Number(e.target.value)) });
    }
    if (t === "array") {
      const simple = !Array.isArray(value) || value.every((x) => typeof x === "string");
      if (simple) {
        return h("input", { id: fid, class: "input mono", value: Array.isArray(value) ? value.join(", ") : "", placeholder: "comma, separated, values",
          oninput: (e) => set(e.target.value.trim() === "" ? undefined : e.target.value.split(",").map((s) => s.trim()).filter(Boolean)) });
      }
    }
    if (t === "array" || t === "object") {
      const ta = h("textarea", { id: fid, class: "input", rows: 4, value: value === undefined ? "" : JSON.stringify(value, null, 2) });
      ta.addEventListener("input", () => {
        if (ta.value.trim() === "") { ta.classList.remove("invalid"); set(undefined); return; }
        try { const v = JSON.parse(ta.value); ta.classList.remove("invalid"); set(v); } catch (e) { ta.classList.add("invalid"); }
      });
      return ta;
    }
    return h("input", { id: fid, class: "input", value: value === undefined || value === null ? "" : (typeof value === "string" ? value : JSON.stringify(value)),
      oninput: (e) => set(e.target.value === "" ? undefined : e.target.value) });
  }

  function condEditor(get, set, sourcesHint) {
    const cond = get() || {};
    if (cond.all || cond.any || cond.not) {
      const ta = h("textarea", { class: "input", rows: 4, value: JSON.stringify(cond, null, 2) });
      ta.addEventListener("input", () => { try { set(JSON.parse(ta.value)); ta.classList.remove("invalid"); markDirty(); } catch (e) { ta.classList.add("invalid"); } });
      return h("div", { class: "stack" }, ta, h("div", { class: "small muted", text: "Combined condition, edited as JSON." }));
    }
    const left = h("input", { class: "input expr", value: cond.left === undefined ? "" : (typeof cond.left === "string" ? cond.left : JSON.stringify(cond.left)),
      placeholder: sourcesHint || "{{ item.score }}", "aria-label": "Value to test" });
    const op = h("select", { class: "input", "aria-label": "Comparison" }, S.palette.condition_ops.map((o) => h("option", { value: o, text: o.replace(/_/g, " "), selected: o === (cond.op || "truthy") })));
    const right = h("input", { class: "input mono", value: cond.right === undefined ? "" : (typeof cond.right === "string" ? cond.right : JSON.stringify(cond.right)), placeholder: "0", "aria-label": "Compare with" });
    const update = () => {
      const c = { left: left.value, op: op.value };
      right.classList.toggle("hidden", UNARY.has(op.value));
      if (!UNARY.has(op.value)) { let r = right.value; try { r = JSON.parse(r); } catch (e) { /* keep as text */ } c.right = r; }
      set(c); markDirty();
    };
    [left, right].forEach((x) => x.addEventListener("input", update));
    op.addEventListener("change", update);
    right.classList.toggle("hidden", UNARY.has(op.value));
    return h("div", { class: "stack", style: { gap: "6px" } }, left, h("div", { class: "row" }, op, right));
  }

  function section(title, ...children) {
    return h("section", { class: "stack" }, h("h3", { class: "section-title", text: title }), ...children);
  }

  // ================================================================ inspector
  function renderInspector() {
    const head = document.getElementById("insp-head"), body = document.getElementById("insp-body");
    body.replaceChildren();
    if (!S.sel) { agentSettings(head, body); return; }
    if (S.sel.type === "edge") {
      const [from, port, to] = S.sel.id.split("|");
      head.replaceChildren(h("span", { class: "chip", text: "Connection" }), h("div", { class: "mono", text: from + "  →  " + to }));
      body.append(h("p", { class: "muted", style: { margin: 0 }, text: port === "out" ? "Runs " + to + " after " + from + " finishes." :
        port === "else" ? "Followed when no route of " + from + " matches." : "Followed when route " + (Number(port.slice(1)) + 1) + " of " + from + " matches." }),
        h("button", { class: "btn danger", type: "button", onclick: () => deleteEdge(S.sel.id) }, "Delete connection"));
      return;
    }
    const n = node(S.sel.id);
    if (!n) { select(null); return; }
    n.ui = n.ui || {};
    n.ui.modes = n.ui.modes || {};
    const l = leaf(n);
    const typeLabel = { tool: l.server === "agents" ? "Agent" : "Tool", llm: "LLM call", transform: "Transform", router: "Router" }[l.type] || n.type;
    const idInput = h("input", { class: "input mono", value: n.id, "aria-label": "Step id" });
    idInput.addEventListener("change", () => { if (!renameNode(n.id, idInput.value.trim())) idInput.value = n.id; else renderInspector(); });
    head.replaceChildren(
      h("div", { class: "row" }, JF.icon(G.kindOf(n, S.toolCats)), h("b", { text: typeLabel + (n.type === "for_each" ? ", repeated" : "") }),
        h("div", { class: "grow" }), G.startId(S.def) === n.id ? h("span", { class: "chip", text: "start" }) :
          h("button", { class: "btn small", type: "button", onclick: () => { S.def.start = n.id; markDirty(); renderCanvas(); renderInspector(); } }, "Start here")),
      field("Step id", idInput, "Renaming updates references in other steps."));
    const desc = h("textarea", { class: "input", rows: 2, value: n.description || "", style: { fontFamily: "var(--sans)", fontSize: "13px" } });
    desc.addEventListener("input", () => { n.description = desc.value || undefined; markDirty(); });
    body.append(field("Description", desc));

    if (n.type !== "router") body.append(loopSection(n));
    if (l.type === "tool") body.append(...toolForm(n, l));
    if (l.type === "llm") body.append(...llmForm(n, l));
    if (l.type === "transform") body.append(...transformForm(n, l));
    if (n.type === "router") body.append(...routerForm(n));
    body.append(...commonForm(n));
  }

  function loopSection(n) {
    const isLoop = n.type === "for_each";
    const toggle = h("input", { type: "checkbox", checked: isLoop, id: "loop-toggle" });
    toggle.addEventListener("change", () => {
      if (toggle.checked) {
        const keep = { id: n.id, ui: n.ui, description: n.description, on_error: n.on_error, join: n.join };
        const body = clone(n); ["id", "ui", "description", "on_error", "join", "next"].forEach((k) => delete body[k]);
        Object.keys(n).forEach((k) => delete n[k]);
        Object.assign(n, keep, { type: "for_each", items: "", as: "item", concurrency: 1, on_item_error: "continue", body });
      } else {
        const body = n.body;
        const keep = { id: n.id, ui: n.ui, description: n.description, on_error: n.on_error, join: n.join };
        Object.keys(n).forEach((k) => delete n[k]);
        Object.assign(n, body, keep);
      }
      Object.keys(n).forEach((k) => n[k] === undefined && delete n[k]);
      markDirty(); renderCanvas(); renderInspector();
    });
    const parts = [h("label", { class: "row", style: { fontWeight: 500 } }, toggle, "Repeat for each item in a list")];
    if (isLoop) {
      const src = sourcesFor(n, false).filter((s) => !s.startsWith("run."));
      const as = h("input", { class: "input mono", value: n.as || "item" });
      as.addEventListener("change", () => { n.as = as.value.trim() || "item"; markDirty(); renderInspector(); });
      const max = h("input", { class: "input mono", value: n.max_items === undefined || n.max_items === null ? "" : String(n.max_items), placeholder: "no limit" });
      max.addEventListener("input", () => { const v = max.value.trim(); n.max_items = v === "" ? undefined : (/^\d+$/.test(v) ? Number(v) : v); markDirty(); });
      const conc = h("input", { class: "input mono", type: "number", min: "1", max: "16", value: String(n.concurrency || 1) });
      conc.addEventListener("input", () => { n.concurrency = Math.min(16, Math.max(1, Number(conc.value) || 1)); markDirty(); });
      const onErr = h("select", { class: "input" }, h("option", { value: "continue", text: "Continue with the rest", selected: n.on_item_error !== "fail" }),
        h("option", { value: "fail", text: "Stop this step", selected: n.on_item_error === "fail" }));
      onErr.addEventListener("change", () => { n.on_item_error = onErr.value; markDirty(); });
      const pairs = h("input", { type: "checkbox", checked: !!n.include_item });
      pairs.addEventListener("change", () => { n.include_item = pairs.checked || undefined; markDirty(); });
      parts.push(valueField({ label: "List to repeat over", type: "array", required: true, get: () => n.items, set: (v) => { n.items = v; }, sources: src, modes: n.ui.modes, modeKey: "items" }),
        h("div", { style: { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "10px" } },
          field("Name for each item", as), field("Concurrency, at once", conc), field("Most items", max, "Number or {{ inputs.x }}"), field("If one item fails", onErr)),
        h("label", { class: "row small" }, pairs, "Output pairs of item and result"));
    }
    return h("section", { class: "stack", style: { padding: "12px", borderRadius: "10px", border: "1px solid var(--line)", background: "var(--sunken)" } }, ...parts);
  }

  function toolForm(n, l) {
    const info = S.toolInfo[l.server + "/" + l.tool];
    const sources = sourcesFor(n, true);
    const out = [];
    if (!info) {
      const ta = h("textarea", { class: "input", rows: 6, value: JSON.stringify(l.args || {}, null, 2) });
      ta.addEventListener("input", () => { try { l.args = JSON.parse(ta.value); ta.classList.remove("invalid"); markDirty(); } catch (e) { ta.classList.add("invalid"); } });
      out.push(h("div", { class: "notice warn", text: `Tool ${l.server}.${l.tool} is not in the current tool list. Its server may be offline or the tool blocked. Arguments are shown as JSON.` }),
        section("Arguments", ta));
    } else {
      const schema = info.input_schema || {};
      const props = schema.properties || {};
      const req = new Set(info.required || []);
      l.args = l.args || {};
      out.push(h("div", { class: "notice small" }, h("b", { class: "mono", text: l.tool }), " on ", h("span", { class: "mono", text: l.server }), h("div", { text: info.description })));
      const fields = Object.entries(props).map(([name, p]) => valueField({
        label: name, help: p.description, required: req.has(name), type: Array.isArray(p.type) ? p.type[0] : p.type,
        enumVals: p.enum, get: () => l.args[name], set: (v) => { if (v === undefined) delete l.args[name]; else l.args[name] = v; },
        sources, modes: n.ui.modes, modeKey: "args." + name }));
      out.push(section("Arguments", ...(fields.length ? fields : [h("p", { class: "small muted", style: { margin: 0 }, text: "This tool takes no arguments." })])));
    }
    const sel = h("input", { class: "input mono", value: l.select || "", placeholder: "whole result" });
    sel.addEventListener("input", () => { l.select = sel.value.trim() || undefined; markDirty(); });
    const timeout = h("input", { class: "input mono", type: "number", min: "1", value: l.timeout || "", placeholder: "server default" });
    timeout.addEventListener("input", () => { l.timeout = timeout.value ? Number(timeout.value) : undefined; markDirty(); });
    const retries = h("select", { class: "input" }, [0, 1, 2, 3].map((r) => h("option", { value: r, text: String(r), selected: (l.retries || 0) === r })));
    retries.addEventListener("change", () => { l.retries = Number(retries.value) || undefined; markDirty(); });
    out.push(section("Result", field("Keep from result", sel, "A field such as results. Leave empty to keep everything."),
      h("div", { style: { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "10px" } }, field("Timeout, seconds", timeout), field("Retries", retries))));
    return out;
  }

  function llmForm(n, l) {
    const sources = sourcesFor(n, true);
    const provider = h("select", { class: "input" }, [["", "Default"], ["anthropic", "Anthropic"], ["openai_compat", "OpenAI-compatible"]]
      .map(([v, t]) => h("option", { value: v, text: t, selected: (l.provider || "") === v })));
    provider.addEventListener("change", () => { l.provider = provider.value || undefined; markDirty(); });
    const model = h("input", { class: "input mono", value: l.model || "", placeholder: "default" });
    model.addEventListener("input", () => { l.model = model.value.trim() || undefined; markDirty(); });
    const temp = h("input", { class: "input mono", type: "number", min: "0", max: "1", step: "0.1", value: String(l.temperature || 0) });
    temp.addEventListener("input", () => { l.temperature = Number(temp.value) || undefined; markDirty(); });
    const maxTok = h("input", { class: "input mono", type: "number", min: "1", value: String(l.max_tokens || 4096) });
    maxTok.addEventListener("input", () => { l.max_tokens = Number(maxTok.value) || undefined; markDirty(); });
    const system = h("textarea", { class: "input", rows: 3, value: l.system || "", placeholder: "Standing rules, such as: work only from the supplied articles." });
    system.addEventListener("input", () => { l.system = system.value || undefined; markDirty(); });
    const prompt = h("textarea", { class: "input", rows: 9, value: l.prompt || "", placeholder: "Write the task. Insert data with the buttons below." });
    prompt.addEventListener("input", () => { l.prompt = prompt.value; markDirty(); });
    const chips = h("div", { class: "insert-chips" }, sources.map((s) => h("button", { type: "button", title: "Insert " + s, onclick: () => {
      const ins = "{{ " + s + (s.startsWith("nodes.") ? " | pretty" : "") + " }}";
      const a = prompt.selectionStart ?? prompt.value.length, b = prompt.selectionEnd ?? a;
      prompt.value = prompt.value.slice(0, a) + ins + prompt.value.slice(b);
      l.prompt = prompt.value; markDirty(); prompt.focus(); prompt.selectionStart = prompt.selectionEnd = a + ins.length;
    } }, s)));
    const structured = h("input", { type: "checkbox", checked: !!l.output_schema });
    const schemaBox = h("textarea", { class: "input", rows: 10, value: l.output_schema ? JSON.stringify(l.output_schema, null, 2) : "" });
    const example = { type: "object", required: ["answer"], properties: { answer: { type: "string" }, confidence: { type: "number", minimum: 0, maximum: 1 } } };
    const schemaWrap = h("div", { class: "stack" + (l.output_schema ? "" : " hidden") }, schemaBox,
      h("div", { class: "row" }, h("span", { class: "small muted grow", text: "JSON Schema with type object at the top. Later steps can pick its fields." }),
        h("button", { class: "btn small", type: "button", onclick: () => { schemaBox.value = JSON.stringify(example, null, 2); schemaBox.dispatchEvent(new Event("input")); } }, "Example")));
    schemaBox.addEventListener("input", () => {
      try { const v = JSON.parse(schemaBox.value); if (v.type !== "object") throw new Error(); l.output_schema = v; schemaBox.classList.remove("invalid"); markDirty(); renderCanvas(); }
      catch (e) { schemaBox.classList.add("invalid"); }
    });
    structured.addEventListener("change", () => {
      if (structured.checked) { l.output_schema = l.output_schema || example; schemaBox.value = JSON.stringify(l.output_schema, null, 2); }
      else delete l.output_schema;
      schemaWrap.classList.toggle("hidden", !structured.checked); markDirty(); renderCanvas();
    });
    return [
      section("Model", h("div", { style: { display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "10px" } },
        field("Provider", provider), field("Model", model), field("Temperature", temp), field("Max tokens", maxTok))),
      section("Prompt", field("System prompt, optional", system), field("Prompt", prompt), h("div", { class: "small muted", text: "Insert" }), chips),
      section("Output", h("label", { class: "row" }, structured, "Structured output, checked against a JSON Schema"), schemaWrap),
    ];
  }

  function transformForm(n, l) {
    const sources = sourcesFor(n, true);
    l.steps = l.steps || [];
    const list = h("div", { class: "stack" });
    const draw = () => {
      list.replaceChildren(...l.steps.map((st, i) => stepCard(n, l, st, i, sources, draw)));
      if (!l.steps.length) list.append(h("p", { class: "small muted", style: { margin: 0 }, text: "No steps: the input passes through unchanged." }));
    };
    draw();
    const opSel = h("select", { class: "input", "aria-label": "Step to add" }, S.palette.transform_ops.map((o) => h("option", { value: o, text: o })));
    return [
      section("Input", valueField({ label: "Input", get: () => l.input, set: (v) => { l.input = v; }, sources, modes: n.ui.modes, modeKey: "input" })),
      section("Steps, in order", list, h("div", { class: "row" }, opSel,
        h("button", { class: "btn small", type: "button", onclick: () => { l.steps.push({ op: opSel.value }); markDirty(); draw(); renderCanvas(); } }, "Add step"))),
    ];
  }

  function stepCard(n, l, st, i, sources, redraw) {
    const move = (d) => { const j = i + d; if (j < 0 || j >= l.steps.length) return; [l.steps[i], l.steps[j]] = [l.steps[j], l.steps[i]]; markDirty(); redraw(); };
    const fields = (TRANSFORM_FIELDS[st.op] || []).map((f) => {
      if (f.t === "value") return valueField({ label: f.k, type: f.type, get: () => st[f.k], set: (v) => { if (v === undefined) delete st[f.k]; else st[f.k] = v; },
        sources: sources.concat(["item", "index"]), modes: n.ui.modes, modeKey: "steps." + i + "." + f.k });
      if (f.t === "cond") return field("Keep items where", condEditor(() => st.when, (c) => { st.when = c; }, "{{ item.score }}"));
      if (f.t === "bool") { const c = h("input", { type: "checkbox", checked: !!st[f.k] }); c.addEventListener("change", () => { st[f.k] = c.checked || undefined; markDirty(); }); return h("label", { class: "row small" }, c, f.label || f.k); }
      if (f.t === "select") { const s = h("select", { class: "input" }, f.opts.map((o) => h("option", { value: o, text: o, selected: (st[f.k] || f.opts[0]) === o })));
        s.addEventListener("change", () => { st[f.k] = s.value === f.opts[0] ? undefined : s.value; markDirty(); }); return field(f.k, s); }
      if (f.t === "json") { const ta = h("textarea", { class: "input", rows: 4, placeholder: f.ph, value: st[f.k] === undefined ? "" : JSON.stringify(st[f.k], null, 2) });
        ta.addEventListener("input", () => { if (!ta.value.trim()) { delete st[f.k]; ta.classList.remove("invalid"); markDirty(); return; }
          try { st[f.k] = JSON.parse(ta.value); ta.classList.remove("invalid"); markDirty(); } catch (e) { ta.classList.add("invalid"); } });
        return field(f.k, ta, f.help); }
      if (f.t === "list") { const inp = h("input", { class: "input mono", placeholder: f.ph, value: (st[f.k] || []).join(", ") });
        inp.addEventListener("input", () => { st[f.k] = inp.value.split(",").map((x) => x.trim()).filter(Boolean); markDirty(); }); return field(f.k, inp); }
      if (f.t === "number") { const inp = h("input", { class: "input mono", type: "number", value: st[f.k] === undefined ? "" : String(st[f.k]) });
        inp.addEventListener("input", () => { if (inp.value === "") delete st[f.k]; else st[f.k] = Number(inp.value); markDirty(); }); return field(f.k, inp); }
      const inp = h("input", { class: "input mono", placeholder: f.ph || "", value: st[f.k] === undefined ? "" : String(st[f.k]) });
      inp.addEventListener("input", () => { if (inp.value === "") delete st[f.k]; else st[f.k] = inp.value; markDirty(); });
      return field(f.k, inp, f.help);
    });
    return h("div", { class: "step" },
      h("div", { class: "row" }, h("span", { class: "small muted", text: String(i + 1) }), h("span", { class: "op", text: st.op }), h("div", { class: "grow" }),
        h("button", { class: "btn small ghost", type: "button", "aria-label": "Move up", onclick: () => move(-1) }, "↑"),
        h("button", { class: "btn small ghost", type: "button", "aria-label": "Move down", onclick: () => move(1) }, "↓"),
        h("button", { class: "btn small ghost", type: "button", "aria-label": "Remove step", onclick: () => { l.steps.splice(i, 1); markDirty(); redraw(); renderCanvas(); } }, "×")),
      ...fields);
  }

  function routerForm(n) {
    const targets = [END].concat(S.def.nodes.filter((o) => o.id !== n.id).map((o) => o.id));
    const targetSel = (get, set) => {
      const s = h("select", { class: "input mono" }, targets.map((t) => h("option", { value: t, text: t === END ? "end the agent" : t, selected: (get() || END) === t })));
      s.addEventListener("change", () => { set(s.value); markDirty(); renderCanvas(); });
      return s;
    };
    n.routes = n.routes || [];
    const routes = n.routes.map((r, i) => h("div", { class: "step" },
      h("div", { class: "row" }, h("b", { text: "Route " + (i + 1) }), h("div", { class: "grow" }),
        h("button", { class: "btn small ghost", type: "button", "aria-label": "Remove route", onclick: () => { n.routes.splice(i, 1); markDirty(); renderCanvas(); renderInspector(); } }, "×")),
      field("When", condEditor(() => r.when, (c) => { r.when = c; }, "{{ nodes.step | length }}")),
      field("Then go to", targetSel(() => r.goto, (v) => { r.goto = v; }))));
    return [
      section("Routes, first match wins", h("p", { class: "small muted", style: { margin: 0 }, text: "You can also connect each route's circle on the card to a step." }), ...routes,
        h("button", { class: "btn small", type: "button", onclick: () => { n.routes.push({ when: { left: "", op: "truthy" }, goto: END }); markDirty(); renderCanvas(); renderInspector(); } }, "Add route")),
      section("Otherwise", field("Go to", targetSel(() => n.default, (v) => { n.default = v; }))),
    ];
  }

  function commonForm(n) {
    const out = [];
    const inc = G.incoming(S.def)[n.id] || 0;
    if (inc > 1 || n.join === "all") {
      const seg = h("div", { class: "seg", role: "group", "aria-label": "Join" },
        [["all", "Wait for all"], ["any", "Run per branch"]].map(([v, t]) => h("button", { type: "button", "aria-pressed": (n.join || "any") === v ? "true" : "false",
          onclick: () => { n.join = v === "any" ? undefined : v; markDirty(); renderInspector(); } }, t)));
      out.push(section("When several branches lead here", seg, h("div", { class: "small muted", text: inc + " branches lead here. Wait for all suits parallel branches; run per branch suits alternatives a router chose between." })));
    }
    const onErr = h("select", { class: "input" }, h("option", { value: "fail", text: "Stop the run", selected: n.on_error !== "continue" }),
      h("option", { value: "continue", text: "Continue; this step's output is empty", selected: n.on_error === "continue" }));
    onErr.addEventListener("change", () => { n.on_error = onErr.value === "fail" ? undefined : onErr.value; markDirty(); });
    out.push(section("If this step fails", onErr));
    out.push(h("div", { class: "row", style: { paddingTop: "8px", borderTop: "1px solid var(--line)" } },
      h("button", { class: "btn small", type: "button", onclick: () => {
        const c = clone(n); c.id = uniqueId(n.id); c.ui = { ...(n.ui || {}), x: (n.ui.x || 0) + 32, y: (n.ui.y || 0) + 96 };
        S.def.nodes.push(c); markDirty(); select({ type: "node", id: c.id }); } }, "Duplicate"),
      h("div", { class: "grow" }), h("button", { class: "btn small danger", type: "button", onclick: () => deleteNode(n.id) }, "Delete step")));
    return out;
  }

  // ================================================================ agent settings
  function agentSettings(head, body) {
    const d = S.def;
    head.replaceChildren(h("b", { text: "Agent settings" }), h("span", { class: "small muted", text: "Select a step to edit it. Click empty canvas to come back here." }));
    const name = h("input", { class: "input", value: d.name || "" });
    name.addEventListener("input", () => { d.name = name.value; markDirty(); renderHeader(); });
    const cat = h("select", { class: "input" }, S.categories.map((c) => h("option", { value: c.name, text: c.name, selected: c.name === d.category })));
    cat.addEventListener("change", () => { d.category = cat.value; markDirty(); renderHeader(); });
    const desc = h("textarea", { class: "input", rows: 3, value: d.description || "", style: { fontFamily: "var(--sans)", fontSize: "13px" } });
    desc.addEventListener("input", () => { d.description = desc.value; markDirty(); });
    body.append(section("About", field("Name", name), field("Category", cat), field("Description, shown to MCP clients", desc)));
    body.append(inputsEditor());
    body.append(outputEditor());
    d.budgets = d.budgets || {};
    const num = (k, def, label) => { const i = h("input", { class: "input mono", type: "number", min: "0", value: String(d.budgets[k] ?? def) });
      i.addEventListener("input", () => { d.budgets[k] = Number(i.value); markDirty(); }); return field(label, i); };
    body.append(section("Budgets per run", h("div", { style: { display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "8px" } },
      num("max_tool_calls", 20, "Tool calls"), num("max_llm_calls", 10, "LLM calls"), num("max_steps", 50, "Steps"))));
    const versions = h("div", { class: "stack small" }, h("button", { class: "btn small", type: "button", onclick: () => loadVersions(versions) }, "Show versions"));
    body.append(section("Versions", versions));
  }

  function inputsEditor() {
    const d = S.def;
    d.inputs = d.inputs || {};
    const box = h("div", { class: "stack" });
    const draw = () => {
      box.replaceChildren(...Object.entries(d.inputs).map(([name, p]) => {
        const nm = h("input", { class: "input mono", value: name, "aria-label": "Input name" });
        nm.addEventListener("change", () => {
          const nv = nm.value.trim();
          if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(nv) || (nv !== name && nv in d.inputs)) { toast("Use a new name of letters, digits and underscores.", true); nm.value = name; return; }
          const entries = Object.entries(d.inputs).map(([k, v]) => [k === name ? nv : k, v]);
          d.inputs = Object.fromEntries(entries); markDirty(); draw();
        });
        const type = h("select", { class: "input", "aria-label": "Type" }, ["string", "integer", "number", "boolean", "array", "object"].map((t) => h("option", { value: t, text: t, selected: p.type === t })));
        type.addEventListener("change", () => { p.type = type.value; markDirty(); });
        const def = h("input", { class: "input mono", value: p.default === undefined || p.default === null ? "" : (typeof p.default === "string" ? p.default : JSON.stringify(p.default)), placeholder: "no default", "aria-label": "Default" });
        def.addEventListener("input", () => {
          if (def.value === "") { delete p.default; markDirty(); return; }
          if ((p.type || "string") === "string") p.default = def.value;
          else { try { p.default = JSON.parse(def.value); def.classList.remove("invalid"); } catch (e) { def.classList.add("invalid"); return; } }
          markDirty();
        });
        const req = h("input", { type: "checkbox", checked: !!p.required });
        req.addEventListener("change", () => { p.required = req.checked || undefined; markDirty(); });
        const ds = h("input", { class: "input", value: p.description || "", placeholder: "Description", "aria-label": "Description" });
        ds.addEventListener("input", () => { p.description = ds.value || undefined; markDirty(); });
        return h("div", { class: "step" }, h("div", { class: "row" }, nm, type,
            h("button", { class: "btn small ghost", type: "button", "aria-label": "Remove input", onclick: () => { delete d.inputs[name]; markDirty(); draw(); } }, "×")),
          def, ds, h("label", { class: "row small" }, req, "Required"));
      }));
      if (!Object.keys(d.inputs).length) box.append(h("p", { class: "small muted", style: { margin: 0 }, text: "No inputs. Add some so each run, and each MCP call, can pass values in." }));
    };
    draw();
    return section("Inputs", box, h("button", { class: "btn small", type: "button", onclick: () => {
      let k = "input", i = 2; while (k in d.inputs) k = "input_" + i++;
      d.inputs[k] = { type: "string" }; markDirty(); draw(); } }, "Add input"));
  }

  function outputEditor() {
    const d = S.def;
    const single = typeof d.output === "string" && /^\{\{\s*nodes\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}$/.exec(d.output);
    const mode = d.output == null ? "all" : single ? "node" : "custom";
    const modeSel = h("select", { class: "input" }, [["all", "Every step's output"], ["node", "One step's output"], ["custom", "Custom JSON template"]]
      .map(([v, t]) => h("option", { value: v, text: t, selected: v === mode })));
    const nodeSel = h("select", { class: "input mono" }, S.def.nodes.map((n) => h("option", { value: n.id, text: n.id, selected: single && single[1] === n.id })));
    const ta = h("textarea", { class: "input", rows: 6, value: mode === "custom" ? JSON.stringify(d.output, null, 2) : "", placeholder: '{"events": "{{ nodes.rank | default([]) }}"}' });
    const sync = () => { nodeSel.classList.toggle("hidden", modeSel.value !== "node"); ta.classList.toggle("hidden", modeSel.value !== "custom"); };
    modeSel.addEventListener("change", () => {
      if (modeSel.value === "all") d.output = null;
      if (modeSel.value === "node") d.output = "{{ nodes." + nodeSel.value + " }}";
      if (modeSel.value === "custom") { d.output = d.output == null ? {} : d.output; ta.value = JSON.stringify(d.output, null, 2); }
      sync(); markDirty();
    });
    nodeSel.addEventListener("change", () => { d.output = "{{ nodes." + nodeSel.value + " }}"; markDirty(); });
    ta.addEventListener("input", () => { try { d.output = JSON.parse(ta.value); ta.classList.remove("invalid"); markDirty(); } catch (e) { ta.classList.add("invalid"); } });
    sync();
    return section("Output", h("p", { class: "small muted", style: { margin: 0 }, text: "What a run returns, and what MCP callers receive." }), modeSel, nodeSel, ta);
  }

  async function loadVersions(box) {
    const vs = await api("/api/agents/" + encodeURIComponent(S.agent.id) + "/versions");
    box.replaceChildren(...vs.map((v) => h("div", { class: "row" }, h("b", { text: "v" + v.version }), h("span", { class: "muted grow", text: v.saved_by + ", " + JF.ago(v.saved_at) }),
      h("button", { class: "btn small", type: "button", onclick: async () => {
        const def = await api("/api/agents/" + encodeURIComponent(S.agent.id) + "/versions/" + v.version);
        modal({ title: "Version " + v.version, wide: true, body: JF.jsonBlock(def), actions: [{ label: "Close" },
          { label: "Load into editor", primary: true, onClick: () => { S.def = G.normalize(def); G.autoLayout(S.def); markDirty(); select(null); renderHeader();
            toast("Loaded version " + v.version + ". Save to make it the newest version."); } }] });
      } }, "View"))));
  }

  // ================================================================ actions
  async function validate(quiet) {
    try {
      S.problems = await api("/api/agents/" + encodeURIComponent(S.agent.id) + "/validate", { method: "POST", body: { definition: S.def } });
    } catch (e) { toast(e.message, true); return false; }
    renderProblems(); renderCanvas();
    if (!quiet) toast(S.problems.ok ? "No problems found." + (S.problems.warnings.length ? " " + S.problems.warnings.length + " warning(s)." : "") : S.problems.errors.length + " problem(s) found.", !S.problems.ok);
    return S.problems.ok;
  }

  async function save() {
    try {
      const r = await api("/api/agents/" + encodeURIComponent(S.agent.id), { method: "PUT", body: { definition: S.def, version: S.version } });
      S.version = r.version; S.dirty = false;
      document.getElementById("dirty").classList.add("hidden");
      S.problems = r.validation; renderProblems(); renderCanvas();
      if (r.validation.unpublished) { S.agent.published = false; toast("Saved with problems, so the agent was unpublished.", true); }
      else toast("Saved version " + r.version + (r.validation.ok ? "." : ", with " + r.validation.errors.length + " problem(s)."));
      renderHeader();
      return true;
    } catch (e) { toast(e.message, true); return false; }
  }

  async function togglePublish() {
    if (S.dirty && !(await save())) return;
    try {
      await api("/api/agents/" + encodeURIComponent(S.agent.id) + "/publish", { method: "POST", body: { published: !S.agent.published } });
      S.agent.published = !S.agent.published; renderHeader();
      toast(S.agent.published ? "Published. It is now an MCP tool in " + S.def.category + "." : "Unpublished.");
    } catch (e) { toast(e.message, true); await validate(true); }
  }

  async function runDialog() {
    if (S.dirty && !(await save())) return;
    if (!(await validate(true))) { toast("Fix the problems listed under the canvas before running.", true); return; }
    const controls = {};
    const rows = Object.entries(S.def.inputs || {}).map(([name, p]) => {
      const def = p.default === undefined || p.default === null ? "" : (typeof p.default === "string" ? p.default : JSON.stringify(p.default));
      const el = h("input", { class: "input" + ((p.type || "string") === "string" ? "" : " mono"), value: def });
      controls[name] = [el, p];
      return field(name + " (" + (p.type || "string") + ")" + (p.required ? " · required" : ""), el, p.description);
    });
    modal({ title: "Run " + (S.def.name || S.agent.id), body: h("div", { class: "stack" }, rows.length ? rows : h("p", { class: "muted", text: "This agent takes no inputs." })),
      actions: [{ label: "Cancel" }, { label: "Run", primary: true, onClick: async () => {
        const vals = {};
        for (const [name, [el, p]] of Object.entries(controls)) {
          if (el.value === "") continue;
          if ((p.type || "string") === "string") vals[name] = el.value;
          else { try { vals[name] = JSON.parse(el.value); } catch (e) { toast(name + " must be valid " + p.type, true); return true; } }
        }
        try { const r = await api("/api/agents/" + encodeURIComponent(S.agent.id) + "/run", { method: "POST", body: { inputs: vals } });
          location.href = "/app/runs/" + r.run_id; } catch (e) { toast(e.message, true); return true; }
      } }] });
  }

  function jsonDialog() {
    const ta = h("textarea", { class: "input", rows: 22, value: JSON.stringify(S.def, null, 2) });
    modal({ title: "Agent JSON", wide: true, body: h("div", { class: "stack" }, h("p", { class: "small muted", style: { margin: 0 }, text: "Copy this to move the agent between installations, or edit and apply." }), ta),
      actions: [{ label: "Close" }, { label: "Copy", onClick: async () => { try { await navigator.clipboard.writeText(ta.value); toast("Copied."); } catch (e) { ta.select(); } return true; } },
        { label: "Apply", primary: true, onClick: () => {
          try { const d = JSON.parse(ta.value); if (!Array.isArray(d.nodes)) throw new Error("needs a nodes list");
            S.def = G.normalize(d); G.autoLayout(S.def); markDirty(); select(null); renderHeader(); }
          catch (e) { toast("Cannot apply: " + e.message, true); return true; }
        } }] });
  }

  function keys(e) {
    const tag = (e.target.tagName || "").toLowerCase();
    const typing = ["input", "textarea", "select"].includes(tag);
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); save(); return; }
    if (typing || !S.sel) return;
    if (e.key === "Delete" || e.key === "Backspace") {
      e.preventDefault();
      if (S.sel.type === "node") deleteNode(S.sel.id); else deleteEdge(S.sel.id);
    }
    if (e.key === "Escape") select(null);
  }

  // ================================================================ boot
  document.addEventListener("DOMContentLoaded", async () => {
    try { S.user = await api("/api/me"); } catch (e) { return; }
    let agent;
    try { agent = await api("/api/agents/" + encodeURIComponent(agentId())); }
    catch (e) { document.getElementById("insp-body").replaceChildren(h("div", { class: "notice bad", text: e.message })); return; }
    S.agent = agent; S.version = agent.version;
    S.def = G.normalize(clone(agent.definition));
    const laidOut = G.autoLayout(S.def);
    S.categories = await api("/api/categories");
    S.problems = agent.validation;
    try { await loadPalette(false); } catch (e) { toast("Could not load the tool list: " + e.message, true); S.palette = { categories: {}, logic: [], category_order: [], transform_ops: [], condition_ops: [] }; }
    renderHeader(); renderProblems(); select(null); setupCanvas(); fit();
    if (laidOut) toast("Steps were laid out automatically. Save to keep the layout.");
    document.getElementById("pal-search").addEventListener("input", (e) => { S.palQuery = e.target.value; renderPalette(); });
    document.getElementById("pal-refresh").onclick = async () => { await loadPalette(true); toast("Tool list refreshed."); };
    document.getElementById("btn-validate").onclick = () => validate(false);
    document.getElementById("btn-save").onclick = save;
    document.getElementById("btn-run").onclick = runDialog;
    document.getElementById("btn-publish").onclick = togglePublish;
    document.getElementById("btn-json").onclick = jsonDialog;
    document.addEventListener("keydown", keys);
    window.addEventListener("beforeunload", (e) => { if (S.dirty) { e.preventDefault(); e.returnValue = ""; } });
  });
})();
