// PROTOTYPE — throwaway. Branch prototype/som-teaching only.
// Question: how should step-by-step playback of an algorithm work for teaching?
// Three structurally different SOM teaching views on the existing page,
// switchable via ?proto=som&variant=A|B|C and the floating bottom bar (← →).
//   A  "Reproductor"    — full map, video-player controls, minimal overlay
//   B  "Laboratorio"    — map + side panel: parameters, live charts, event log
//   C  "Lección guiada" — pseudocode + narrated sub-steps of one iteration
(() => {
  const params = new URLSearchParams(location.search);
  if (params.get("proto") !== "som" && document.body.dataset.proto !== "som") return;

  const VARIANTS = [
    { key: "A", name: "Reproductor", mount: mountA },
    { key: "B", name: "Laboratorio", mount: mountB },
    { key: "C", name: "Lección guiada", mount: mountC },
  ];

  const DEFAULTS = { iterations: 5000, neuronFactor: 8, lr0: 0.8, seed: 7 };
  const SPEEDS = [
    { label: "Muy lento", n: 1, delay: 700 },
    { label: "Lento", n: 1, delay: 150 },
    { label: "Normal", n: 5, delay: 40 },
    { label: "Rápido", n: 25, delay: 16 },
    { label: "Muy rápido", n: 100, delay: 16 },
  ];

  // ---- Page takeover (host page stays: header, map, worker, data) ---------

  document.querySelector("footer").style.display = "none";
  $("results").hidden = true;
  const main = document.querySelector("main");
  main.style.position = "relative";

  const css = document.createElement("style");
  css.textContent = `
    .p-panel { width: 380px; overflow: auto; border-left: 1px solid var(--border); padding: 12px; display: flex; flex-direction: column; gap: 12px; background: var(--bg); }
    .p-panel.left { border-left: 0; border-right: 1px solid var(--border); order: -1; width: 420px; }
    .p-panel h3 { margin: 0; font-size: 13px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
    .p-row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
    .p-row label { flex: 1; font-size: 12px; }
    .p-row input[type=range] { width: 100%; }
    .p-btn { padding: 7px 12px; }
    .p-btn.primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
    .p-metric { font-variant-numeric: tabular-nums; }
    .p-overlay { position: absolute; z-index: 1000; background: var(--bg); color: var(--text); border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.25); padding: 8px 12px; }
    .p-log { white-space: pre; font: 12px/1.5 ui-monospace, monospace; max-height: 220px; overflow: auto; background: var(--panel); border-radius: 8px; padding: 8px; }
    .p-code { font: 13px/1.7 ui-monospace, monospace; background: var(--panel); border-radius: 8px; padding: 10px; white-space: pre; }
    .p-code .on { background: #ffd60a55; outline: 2px solid #ffd60a; border-radius: 3px; }
    .p-explain { font-size: 14px; line-height: 1.5; min-height: 120px; }
    .p-progress { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
    .p-progress > div { height: 100%; background: var(--accent); }
    #p-switcher { position: fixed; left: 50%; bottom: 12px; transform: translateX(-50%); z-index: 5000;
      background: #111; color: #fff; border-radius: 999px; padding: 6px 8px; display: flex; gap: 8px; align-items: center;
      font: 600 13px -apple-system, sans-serif; box-shadow: 0 4px 16px rgba(0,0,0,.4); }
    #p-switcher button { background: #333; color: #fff; border: 0; border-radius: 999px; padding: 4px 12px; }
    @media (max-width: 700px) { .p-panel, .p-panel.left { width: auto; max-height: 45vh; order: 0; } }
  `;
  document.head.appendChild(css);

  // ---- SOM engine (shared by all variants) --------------------------------

  const som = {
    snap: null,
    onRefresh: null,
    history: [],
    settings: { ...DEFAULTS },
    async reset(settings = this.settings) {
      this.settings = settings;
      const s = settings;
      this.snap = await call("proto_som_reset", s.iterations, s.neuronFactor, s.lr0, s.seed);
      this.history = [[0, this.snap.tour_length]];
      return this.snap;
    },
    async step(n = 1) {
      this.snap = await call("proto_som_step", n, true);
      this.history.push([this.snap.step, this.snap.tour_length]);
      return this.snap;
    },
  };

  function player(onFrame) {
    let playing = false;
    let speed = 2;
    return {
      get playing() { return playing; },
      get speed() { return speed; },
      set speed(v) { speed = v; },
      async play() {
        if (playing) return;
        playing = som.playing = true;
        while (playing && !som.snap.done) {
          const { n, delay } = SPEEDS[speed];
          onFrame(await som.step(n));
          await new Promise((r) => setTimeout(r, delay));
        }
        playing = som.playing = false;
        onFrame(som.snap);
      },
      pause() { playing = false; },
    };
  }

  // ---- Map drawing (shared) -----------------------------------------------

  const renderer = L.canvas({ padding: 0.2 });
  const layer = L.layerGroup().addTo(map);
  const byId = () => Object.fromEntries(points.map((p) => [p.id, p]));

  function heat(h) {
    // 0 → light grey, 1 → strong orange
    const a = Math.min(1, Math.max(0, h));
    return `rgb(${Math.round(200 + 55 * a)}, ${Math.round(200 - 90 * a)}, ${Math.round(200 - 180 * a)})`;
  }

  const road = {
    on: true,
    cache: new Map(),
    path(tour) {
      const key = tour.join(",");
      if (!this.cache.has(key)) {
        this.cache.set(key, call("proto_route_geometry", JSON.stringify(tour)).then((r) => r.path));
      }
      return this.cache.get(key);
    },
  };

  function draw(snap, opt = {}) {
    layer.clearLayers();
    const pts = byId();
    const neurons = opt.useBefore && snap.last ? snap.last.before : snap.neurons;
    const last = snap.last;

    if (opt.tour === "solid" || opt.tour === "dashed") {
      const style = { color: "#34c759", weight: opt.tour === "solid" ? 4 : 2, dashArray: opt.tour === "dashed" ? "6 6" : null, renderer };
      const straight = L.polyline(snap.tour.map((id) => [pts[id].lat, pts[id].lon]), style).addTo(layer);

      // Road geometry only while the route is stable (not during playback): OSRM demo is rate-limited.
      if (road.on && !som.playing) {
        road.path(snap.tour).then((path) => {
          if (som.snap !== snap || !layer.hasLayer(straight)) return; // a newer frame was drawn meanwhile
          layer.removeLayer(straight);
          L.polyline(path, style).addTo(layer).bringToBack();
        }).catch(() => {});
      }
    }

    L.polyline([...neurons, neurons[0]], { color: "#5e5ce6", weight: 2, opacity: 0.9, renderer }).addTo(layer);

    if (opt.moves && last) {
      last.before.forEach((b, i) => {
        if (last.influence[i] > 0.02) {
          L.polyline([b, snap.neurons[i]], { color: "#ff9500", weight: 1.5, renderer }).addTo(layer);
        }
      });
    }

    neurons.forEach((n, i) => {
      const h = opt.influence && last ? last.influence[i] : 0;
      L.circleMarker(n, {
        radius: opt.influence && last ? 3 + 4 * h : 3, renderer, weight: 1,
        color: "#5e5ce6", fillColor: opt.influence && last ? heat(h) : "#fff", fillOpacity: 1,
      }).addTo(layer);
    });

    if (opt.target && last) {
      const t = pts[last.target];
      L.circleMarker([t.lat, t.lon], { radius: 16, color: "#0a84ff", weight: 3, fill: false, renderer }).addTo(layer);
    }

    if (opt.winner && last) {
      const w = neurons[last.winner];
      L.circleMarker(w, { radius: 7, color: "#ff3b30", fillColor: "#ff3b30", fillOpacity: 1, renderer }).addTo(layer);
      const t = pts[last.target];
      L.polyline([[t.lat, t.lon], w], { color: "#ff3b30", weight: 2, dashArray: "4 4", renderer }).addTo(layer);
    }
  }

  const fmt = (x, d = 3) => Number(x).toFixed(d);
  const km = (x) => `${fmt(x, 2)} km`;

  function speedSelect(p) {
    const sel = document.createElement("select");
    SPEEDS.forEach((s, i) => sel.add(new Option(s.label, i, false, i === p.speed)));
    sel.onchange = () => (p.speed = Number(sel.value));
    return sel;
  }

  function el(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  // ---- Variant A: Reproductor ---------------------------------------------

  function mountA() {
    const bar = el(`
      <div class="p-overlay" style="left:50%;bottom:64px;transform:translateX(-50%);display:flex;gap:8px;align-items:center;min-width:min(620px,92vw)">
        <button class="p-btn" data-a="reset" title="Reiniciar">⟲</button>
        <button class="p-btn primary" data-a="play" style="min-width:48px">▶</button>
        <button class="p-btn" data-a="step" title="Una iteración">⏭</button>
        <div style="flex:1"><div class="p-progress"><div style="width:0%"></div></div>
          <div class="p-metric" style="font-size:11px;margin-top:3px" data-m="prog"></div></div>
      </div>`);
    const hud = el(`<div class="p-overlay p-metric" style="top:10px;right:10px;font-size:13px;line-height:1.6"></div>`);
    main.append(bar, hud);
    const p = player(render);
    bar.insertBefore(speedSelect(p), bar.querySelector("div"));

    function render(s) {
      draw(s, { influence: true, winner: SPEEDS[p.speed].n === 1, target: SPEEDS[p.speed].n === 1, tour: s.done ? "solid" : null });
      bar.querySelector(".p-progress > div").style.width = `${(100 * s.step) / s.iterations}%`;
      bar.querySelector("[data-m=prog]").textContent = `Iteración ${s.step} / ${s.iterations}`;
      bar.querySelector("[data-a=play]").textContent = p.playing ? "⏸" : "▶";
      hud.innerHTML = `<b>SOM</b> · ${s.neuron_count} neuronas<br>η (aprendizaje) ${fmt(s.lr)}<br>σ (radio) ${fmt(s.radius, 1)}<br>` +
        `Ruta actual ${km(s.tour_length)}${s.done ? "<br><b>✓ Terminado</b>" : ""}`;
    }

    bar.onclick = async (e) => {
      const a = e.target.dataset.a;
      if (a === "play") p.playing ? p.pause() : p.play();
      if (a === "step") { p.pause(); render(await som.step(1)); }
      if (a === "reset") { p.pause(); render(await som.reset()); }
      render(som.snap);
    };

    som.onRefresh = () => render(som.snap);
    som.reset().then(render);
    return () => { p.pause(); bar.remove(); hud.remove(); };
  }

  // ---- Variant B: Laboratorio ---------------------------------------------

  function mountB() {
    const panel = el(`
      <aside class="p-panel">
        <h3>Parámetros</h3>
        <div class="p-row"><label>Iteraciones <b data-v="iterations"></b><input type="range" min="500" max="10000" step="500" data-p="iterations"></label></div>
        <div class="p-row"><label>Neuronas por cliente <b data-v="neuronFactor"></b><input type="range" min="1" max="12" step="1" data-p="neuronFactor"></label></div>
        <div class="p-row"><label>η₀ tasa inicial <b data-v="lr0"></b><input type="range" min="0.1" max="1" step="0.05" data-p="lr0"></label></div>
        <div class="p-row"><label>Semilla <b data-v="seed"></b><input type="range" min="1" max="50" step="1" data-p="seed"></label></div>
        <div class="p-row">
          <button class="p-btn" data-a="reset">⟲ Reiniciar</button>
          <button class="p-btn primary" data-a="play">▶ Ejecutar</button>
          <button class="p-btn" data-a="step">+1</button>
          <button class="p-btn" data-a="step100">+100</button>
        </div>
        <div class="p-row"><label style="flex:0">Velocidad</label></div>
        <div class="p-row"><label><input type="checkbox" data-o="tour" checked> Ruta implícita</label>
          <label><input type="checkbox" data-o="influence" checked> Vecindario</label></div>
        <h3>Estado</h3>
        <div class="p-metric" data-m="state" style="font-size:13px;line-height:1.6"></div>
        <h3>η y σ en el tiempo</h3>
        <svg data-c="sched" viewBox="0 0 340 110" style="width:100%;background:var(--panel);border-radius:8px"></svg>
        <h3>Longitud de la ruta</h3>
        <svg data-c="len" viewBox="0 0 340 110" style="width:100%;background:var(--panel);border-radius:8px"></svg>
        <h3>Registro</h3>
        <div class="p-log" data-m="log"></div>
      </aside>`);
    main.appendChild(panel);
    map.invalidateSize();

    const p = player(render);
    panel.querySelectorAll(".p-row")[5].appendChild(speedSelect(p));
    const settings = { ...som.settings };
    const log = panel.querySelector("[data-m=log]");
    const logLines = [];
    let loggedStep = -1;

    panel.querySelectorAll("[data-p]").forEach((input) => {
      const k = input.dataset.p;
      input.value = settings[k];
      panel.querySelector(`[data-v=${k}]`).textContent = settings[k];
      input.oninput = () => {
        settings[k] = Number(input.value);
        panel.querySelector(`[data-v=${k}]`).textContent = input.value;
      };
      input.onchange = async () => { p.pause(); logLines.length = 0; render(await som.reset({ ...settings })); };
    });
    panel.querySelectorAll("[data-o]").forEach((c) => (c.onchange = () => render(som.snap)));

    function chart(svg, series, cursor, max) {
      const W = 340, H = 110, P = 8;
      const x = (v) => P + ((W - 2 * P) * v) / som.snap.iterations;
      const y = (v, m) => H - P - ((H - 2 * P) * v) / m;
      svg.innerHTML =
        series.map(([pts, color, m]) =>
          `<polyline fill="none" stroke="${color}" stroke-width="2" points="${pts.map(([a, b]) => `${x(a)},${y(b, m)}`).join(" ")}"/>`
        ).join("") +
        (cursor != null ? `<line x1="${x(cursor)}" x2="${x(cursor)}" y1="0" y2="${H}" stroke="#ff3b30" stroke-width="1.5"/>` : "");
    }

    function render(s) {
      const o = Object.fromEntries([...panel.querySelectorAll("[data-o]")].map((c) => [c.dataset.o, c.checked]));
      draw(s, { influence: o.influence, winner: true, target: true, tour: o.tour ? (s.done ? "solid" : "dashed") : null });
      panel.querySelector("[data-a=play]").textContent = p.playing ? "⏸ Pausa" : "▶ Ejecutar";

      panel.querySelector("[data-m=state]").innerHTML =
        `Iteración <b>${s.step}</b> / ${s.iterations} · ${s.neuron_count} neuronas<br>` +
        `η = ${fmt(s.lr)} · σ = ${fmt(s.radius, 1)} neuronas<br>Ruta implícita: <b>${km(s.tour_length)}</b>` +
        (s.done ? " · <b>✓ terminado</b>" : "");

      const T = s.iterations, s0 = s.neuron_count / 2;
      const sched = [[0, 1], [T, 0]];
      chart(panel.querySelector("[data-c=sched]"), [
        [sched.map(([t]) => [t, settings.lr0 * (1 - t / T)]), "#0a84ff", 1],
        [sched.map(([t]) => [t, Math.max(1, s0 * (1 - t / T))]), "#ff9500", s0],
      ], s.step);
      const maxLen = Math.max(...som.history.map(([, v]) => v));
      chart(panel.querySelector("[data-c=len]"), [[som.history, "#34c759", maxLen * 1.05]], s.step);

      if (s.last && s.step !== loggedStep) {
        loggedStep = s.step;
        logLines.unshift(`#${s.step}  cliente ${s.last.target} (${s.last.target_name}) → neurona ${s.last.winner}`);
        logLines.length = Math.min(logLines.length, 200);
        log.textContent = logLines.join("\n");
      }
    }

    panel.onclick = async (e) => {
      const a = e.target.dataset.a;
      if (!a) return;
      if (a === "play") p.playing ? p.pause() : p.play();
      if (a === "step") { p.pause(); render(await som.step(1)); }
      if (a === "step100") { p.pause(); render(await som.step(100)); }
      if (a === "reset") { p.pause(); logLines.length = 0; render(await som.reset({ ...settings })); }
    };

    som.onRefresh = () => render(som.snap);
    som.reset({ ...settings }).then(render);
    return () => { p.pause(); panel.remove(); map.invalidateSize(); };
  }

  // ---- Variant C: Lección guiada ------------------------------------------

  function mountC() {
    const CODE = [
      "para t = 0 … T−1:",
      "    x ← cliente al azar",
      "    g ← neurona más cercana a x",
      "    para cada neurona i:",
      "        h ← exp(−d(i,g)² / 2σ²)",
      "        wᵢ ← wᵢ + η · h · (x − wᵢ)",
      "    η ← η₀(1 − t/T);  σ ← σ₀(1 − t/T)",
      "ruta ← clientes ordenados por su neurona",
    ];
    const panel = el(`
      <aside class="p-panel left">
        <h3>Mapa autoorganizado (SOM) para el TSP</h3>
        <div class="p-code" data-m="code"></div>
        <div class="p-explain" data-m="explain"></div>
        <div class="p-row">
          <button class="p-btn primary" data-a="next">Siguiente ▶</button>
          <button class="p-btn" data-a="skip">+100 iteraciones</button>
          <button class="p-btn" data-a="end">Hasta el final</button>
          <button class="p-btn" data-a="reset">⟲</button>
        </div>
        <div class="p-progress"><div style="width:0%"></div></div>
        <div class="p-metric" data-m="foot" style="font-size:12px;color:var(--muted)"></div>
      </aside>`);
    main.appendChild(panel);
    map.invalidateSize();

    let phase = 0; // 0 intro, 1 pick, 2 winner, 3 neighborhood, 4 update+decay, 5 final
    let busy = false;

    function code(lines) {
      panel.querySelector("[data-m=code]").innerHTML = CODE.map((c, i) =>
        `<span class="${lines.includes(i) ? "on" : ""}">${c.replace(/</g, "&lt;")}</span>`).join("\n");
    }

    function render() {
      const s = som.snap, last = s.last;
      const explain = panel.querySelector("[data-m=explain]");
      panel.querySelector(".p-progress > div").style.width = `${(100 * s.step) / s.iterations}%`;
      panel.querySelector("[data-m=foot]").textContent =
        `Iteración ${s.step} / ${s.iterations} · η = ${fmt(s.lr)} · σ = ${fmt(s.radius, 1)} · ruta implícita ${km(s.tour_length)}`;

      if (phase === 0) {
        code([]);
        draw(s, {});
        explain.innerHTML = `Tenemos un <b>anillo de ${s.neuron_count} neuronas</b> (morado) colocado al azar sobre la zona de los clientes. ` +
          `En cada iteración el anillo se deforma un poco hacia un cliente. Al final, el orden de las neuronas a lo largo del anillo nos da el orden de visita.`;
      } else if (phase === 1) {
        code([0, 1]);
        draw(s, { useBefore: true, target: true });
        explain.innerHTML = `<b>1. Elegir un cliente al azar.</b> Esta vez salió el cliente <b>${last.target} — ${last.target_name}</b> (círculo azul).`;
      } else if (phase === 2) {
        code([2]);
        draw(s, { useBefore: true, target: true, winner: true });
        explain.innerHTML = `<b>2. Neurona ganadora.</b> Buscamos la neurona más cercana al cliente: la <b>neurona ${last.winner}</b> (rojo). ` +
          `Ella y sus vecinas en el anillo serán atraídas hacia el cliente.`;
      } else if (phase === 3) {
        code([3, 4]);
        draw(s, { useBefore: true, target: true, winner: true, influence: true });
        const affected = last.influence.filter((h) => h > 0.1).length;
        explain.innerHTML = `<b>3. Vecindario.</b> Cada neurona recibe una influencia <i>h</i> según su distancia <b>en el anillo</b> a la ganadora ` +
          `(no en el mapa). Con σ = ${fmt(last.radius, 1)}, unas <b>${affected}</b> neuronas tienen h &gt; 0.1 (naranja = más influencia).`;
      } else if (phase === 4) {
        code([5, 6]);
        draw(s, { target: true, influence: true, moves: true });
        explain.innerHTML = `<b>4. Mover y enfriar.</b> Cada neurona se acerca al cliente una fracción η·h (líneas naranjas). ` +
          `Luego η y σ disminuyen: al principio el anillo se mueve mucho y en bloque; al final solo ajusta detalles. Ahora η = ${fmt(s.lr)}, σ = ${fmt(s.radius, 1)}.`;
      } else if (phase === 5) {
        code([7]);
        draw(s, { tour: "solid" });
        explain.innerHTML = `<b>5. Leer la ruta.</b> Cada cliente se asigna a su neurona más cercana y se visitan en el orden del anillo. ` +
          `Resultado: <b>${km(s.tour_length)}</b> (verde).`;
      }

      panel.querySelector("[data-a=next]").textContent =
        phase === 5 ? "Reiniciar ⟲" : phase === 0 || phase === 4 ? "Siguiente iteración ▶" : "Siguiente ▶";
    }

    async function act(a) {
      if (busy) return;
      busy = true;
      try {
        if (a === "reset" || (a === "next" && phase === 5)) { await som.reset(); phase = 0; }
        else if (a === "next") {
          if (phase === 0 || phase === 4) { await som.step(1); phase = 1; }
          else phase += 1;
        }
        else if (a === "skip") { await som.step(100); phase = som.snap.done ? 5 : 4; }
        else if (a === "end") { await som.step(som.snap.iterations); phase = 5; }
        if (som.snap.done && phase === 4) phase = 5;
        render();
      } finally { busy = false; }
    }

    panel.onclick = (e) => e.target.dataset.a && act(e.target.dataset.a);
    som.onRefresh = render;
    som.reset().then(render);
    return () => { panel.remove(); map.invalidateSize(); };
  }

  // ---- Floating variant switcher (prototype only) --------------------------

  let current = Math.max(0, VARIANTS.findIndex((v) => v.key === params.get("variant")));
  let unmount = null;
  const sw = el(`<div id="p-switcher"><button data-d="-1">‹</button><span></span><button data-d="1">›</button></div>`);
  document.body.appendChild(sw);

  function show(i) {
    unmount?.();
    current = (i + VARIANTS.length) % VARIANTS.length;
    const v = VARIANTS[current];
    params.set("variant", v.key);
    history.replaceState(null, "", `?${params}`);
    sw.querySelector("span").textContent = `${v.key} (${v.name})`;
    unmount = v.mount();
  }

  sw.onclick = (e) => e.target.dataset.d && show(current + Number(e.target.dataset.d));
  addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, select, [contenteditable]")) return;
    if (e.key === "ArrowLeft") show(current - 1);
    if (e.key === "ArrowRight") show(current + 1);
  });

  // OSRM toggle: rebuild the distance matrix and recompute the current route length in place.
  const sourceEl = $("osrm-source");
  const showSource = (src) => {
    road.on = src === "OSRM";
    sourceEl.textContent = road.on ? "· por calles" : `· ${src} (línea recta)`;
  };
  osrmBox.onchange = async () => {
    osrmBox.disabled = true;
    try {
      const { source } = await call("set_osrm", osrmBox.checked);
      showSource(source);
      if (som.snap) {
        const keep = som.snap.last;
        som.snap = await call("proto_som_step", 0, true);
        som.snap.last = keep;
        som.onRefresh?.();
      }
    } finally {
      osrmBox.disabled = false;
    }
  };

  // Auto-load data once Python is ready, then mount the first variant.
  setStatus("Prototipo SOM: cargando Python…");
  worker.addEventListener("message", async ({ data }) => {
    if (data.type !== "ready") return;
    await loadBtn.onclick();
    showSource(statusEl.textContent.split(", ").pop());
    show(current);
  });
})();
