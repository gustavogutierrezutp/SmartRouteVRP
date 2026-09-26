const PROBLEMS = ["TSP", "CVRP", "OVRP", "VRPTW"];
const ALGORITHMS = ["GA", "ACO", "SOM", "ABC", "Todos"];
const COLORS = ["red", "blue", "green", "purple", "orange", "brown", "black"];

const $ = (id) => document.getElementById(id);
const statusEl = $("status");
const loadBtn = $("load");
const solveBtn = $("solve");
const osrmBox = $("osrm");

// ---- Worker RPC -----------------------------------------------------------

const worker = new Worker("worker.js", { type: "module" });
worker.onerror = (event) => setStatus(`Error en el worker: ${event.message || "no se pudo iniciar"}`);
const pending = new Map();
let nextId = 0;

function call(method, ...args) {
  return new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, method, args });
  });
}

worker.onmessage = ({ data }) => {
  if (data.type === "status") {
    setStatus(data.text);
  } else if (data.type === "ready") {
    setStatus(`Listo (Python ${data.python}). Pulse Cargar.`);
    loadBtn.disabled = false;
  } else if (data.type === "fatal") {
    setStatus(`Error iniciando Python: ${data.error}`);
  } else if (data.type === "result") {
    const { resolve, reject } = pending.get(data.id);
    pending.delete(data.id);
    data.error ? reject(new Error(data.error)) : resolve(data.result);
  }
};

// ---- Controls -------------------------------------------------------------

function segmented(el, labels, onChange) {
  let value = labels[0];

  labels.forEach((label, i) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.setAttribute("role", "radio");
    button.setAttribute("aria-checked", String(i === 0));
    button.onclick = () => {
      el.querySelectorAll("button").forEach((b) => b.setAttribute("aria-checked", "false"));
      button.setAttribute("aria-checked", "true");
      value = label;
      onChange?.(label);
    };
    el.appendChild(button);
  });

  return () => value;
}

const getProblem = segmented($("problem"), PROBLEMS, clearRoutes);
const getAlgorithm = segmented($("algorithm"), ALGORITHMS);

function setStatus(text) {
  statusEl.textContent = text;
  statusEl.title = text;
}

async function busy(text, fn) {
  loadBtn.disabled = solveBtn.disabled = osrmBox.disabled = true;
  setStatus(text);
  try {
    await fn();
  } catch (err) {
    setStatus(`Error: ${err.message}`);
  } finally {
    loadBtn.disabled = osrmBox.disabled = false;
    solveBtn.disabled = points.length === 0;
  }
}

// ---- Map ------------------------------------------------------------------

const map = L.map("map").setView([4.8143, -75.6946], 13);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "© OpenStreetMap",
}).addTo(map);

const markerLayer = L.layerGroup().addTo(map);
const routeLayer = L.layerGroup().addTo(map);
let points = [];

function hm(m) {
  const h = Math.floor(m / 60);
  const mm = Math.floor(m % 60);
  return `${String(h).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}

function drawPoints() {
  markerLayer.clearLayers();

  points.forEach((p) => {
    L.marker([p.lat, p.lon])
      .bindPopup(
        `<b>${p.id} - ${p.name}</b><br>Demanda: ${p.demand}` +
          `<br>Ventana: ${hm(p.tw_start)} - ${hm(p.tw_end)}`
      )
      .addTo(markerLayer);
  });

  if (points.length > 1) {
    map.fitBounds(points.map((p) => [p.lat, p.lon]), { padding: [24, 24] });
  }
}

function drawRoutes(layers) {
  routeLayer.clearLayers();
  const bounds = [];

  layers.forEach((layer, i) => {
    if (layer.path.length > 1) {
      L.polyline(layer.path, { color: COLORS[i % COLORS.length], weight: 4, opacity: 0.82 })
        .bindTooltip(layer.name)
        .addTo(routeLayer);
      bounds.push(...layer.path);
    }
  });

  if (bounds.length > 1) map.fitBounds(bounds, { padding: [24, 24] });
}

function clearRoutes() {
  routeLayer.clearLayers();
  $("results").hidden = true;
}

// ---- Results table --------------------------------------------------------

function showResults(results, best) {
  const tbody = document.querySelector("#results tbody");
  tbody.innerHTML = "";

  results.forEach((r, i) => {
    const tr = document.createElement("tr");
    if (i === best) tr.className = "best";

    const cost = r.cost === null ? "INF" : `${r.cost.toFixed(2)} km`;
    const state = r.feasible ? "OK" : `PEN ${(r.penalty ?? Infinity).toFixed(1)}`;

    for (const text of [r.algorithm, cost, r.routes.length, state]) {
      const td = document.createElement("td");
      td.textContent = text;
      tr.appendChild(td);
    }

    if (!r.feasible) tr.lastChild.className = "bad";
    tbody.appendChild(tr);
  });

  $("results").hidden = false;
  map.invalidateSize();
}

// ---- Actions --------------------------------------------------------------

loadBtn.onclick = () =>
  busy("Cargando datos y matriz de distancias…", async () => {
    const data = await call("load", "data/points.csv", "data/vehicles.csv", osrmBox.checked);
    points = data.points;
    clearRoutes();
    drawPoints();
    setStatus(`${points.length} puntos, ${data.vehicles} vehículos, ${data.source}`);
  });

solveBtn.onclick = () =>
  busy(`Resolviendo ${getProblem()} con ${getAlgorithm()}…`, async () => {
    const t0 = performance.now();
    const data = await call("solve", getProblem(), getAlgorithm());
    const seconds = ((performance.now() - t0) / 1000).toFixed(1);
    const best = data.results[data.best];

    showResults(data.results, data.best);
    drawRoutes(data.layers);

    setStatus(
      best.cost === null
        ? "Sin solución: revise demandas, capacidades o ventanas de tiempo."
        : `${best.summary} (${seconds} s)`
    );
  });

osrmBox.onchange = () => {
  clearRoutes();
  if (points.length === 0) return;

  busy("Recalculando matriz…", async () => {
    const data = await call("set_osrm", osrmBox.checked);
    setStatus(`Matriz: ${data.source}`);
  });
};
