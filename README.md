# SmartRouteVRP v2.2 — Pythonista

Correcciones principales:

- El tipo de problema ahora se escoge con un `SegmentedControl` visible:
  - TSP
  - CVRP
  - OVRP
  - VRPTW
- El switch OSRM queda en la misma línea del selector de problema.
- Código reformateado y más limpio.
- OSRM ON:
  - usa matriz real por calles
  - dibuja geometría real de la ruta
- OSRM OFF:
  - usa Haversine
  - dibuja líneas directas
- Si OSRM falla, usa Haversine fallback.

Ejecute `app.py` desde Pythonista.

## Versión web (GitHub Pages)

La carpeta `web/` contiene una versión que corre en el navegador con
[Pyodide](https://pyodide.org) (Python compilado a WebAssembly). Reutiliza
`algorithms/`, `models/` y `routing/` sin cambios; Python corre en un Web
Worker para no congelar la página.

Probar localmente:

```bash
web/build.sh                          # genera _site/
python3 -m http.server -d _site 8000  # abrir http://localhost:8000
```

Publicar: en GitHub, *Settings → Pages → Source: GitHub Actions*. El workflow
`.github/workflows/pages.yml` construye y publica `_site/` en cada push a `main`.
