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
