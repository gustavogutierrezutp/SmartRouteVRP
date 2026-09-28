// Runs Pyodide off the main thread so solving never freezes the page.
const PYODIDE_VERSION = "314.0.7";
const { loadPyodide } = await import(`https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.mjs`);

let pyodide = null;
let webapp = null;
let proto = null;

async function init() {
  postMessage({ type: "status", text: "Descargando Python (Pyodide)…" });
  pyodide = await loadPyodide();

  postMessage({ type: "status", text: "Copiando código fuente…" });
  const files = await (await fetch("files.json")).json();

  for (const path of files) {
    const text = await (await fetch(path)).text();
    const dir = path.split("/").slice(0, -1).join("/");
    if (dir) pyodide.FS.mkdirTree(dir);
    pyodide.FS.writeFile(path, text);
  }

  webapp = pyodide.pyimport("webapp");
  proto = pyodide.pyimport("prototype_som_trace"); // PROTOTYPE: SOM teaching view
  postMessage({ type: "ready", python: pyodide.runPython("import sys; sys.version.split()[0]") });
}

const ready = init().catch((err) => {
  postMessage({ type: "fatal", error: String(err) });
  throw err;
});

onmessage = async ({ data }) => {
  const { id, method, args } = data;

  try {
    await ready;
    const module = method.startsWith("proto_") ? proto : webapp;
    const result = JSON.parse(module[method](...args));
    postMessage({ type: "result", id, result });
  } catch (err) {
    postMessage({ type: "result", id, error: String(err.message || err) });
  }
};
