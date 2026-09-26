import json
import urllib.request

from .geo import build_duration_matrix, build_haversine_matrix, route_to_latlngs

OSRM_BASE = "https://router.project-osrm.org"


class RouteEngine:
    def __init__(self, base_url=OSRM_BASE, timeout=15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.source = "unknown"

    def _open_json(self, url):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "SmartRouteVRP-Pythonista/2.2"},
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def build_matrix(self, points, use_osrm=True):
        if not use_osrm:
            return self._haversine(points, "Haversine")

        try:
            coords = ";".join("{},{}".format(p.lon, p.lat) for p in points)
            url = (
                self.base_url
                + "/table/v1/driving/"
                + coords
                + "?annotations=distance,duration"
            )

            data = self._open_json(url)

            if data.get("code") != "Ok":
                raise RuntimeError(data.get("code"))

            distances = data.get("distances")
            durations = data.get("durations")

            if not distances or not durations:
                raise RuntimeError("OSRM no devolvió matriz completa")

            distance_km = [
                [
                    float(x) / 1000.0 if x is not None else 999999.0
                    for x in row
                ]
                for row in distances
            ]

            duration_min = [
                [
                    float(x) / 60.0 if x is not None else 999999.0
                    for x in row
                ]
                for row in durations
            ]

            self.source = "OSRM"
            return distance_km, duration_min, self.source

        except Exception:
            return self._haversine(points, "Haversine fallback")

    def _haversine(self, points, source):
        distance_km = build_haversine_matrix(points)
        duration_min = build_duration_matrix(distance_km)
        self.source = source
        return distance_km, duration_min, source

    def route_geometry(self, route, points, use_osrm=True):
        if not route or len(route) < 2:
            return []

        if not use_osrm:
            return route_to_latlngs(route, points)

        try:
            coords = ";".join(
                "{},{}".format(points[i].lon, points[i].lat)
                for i in route
            )

            url = (
                self.base_url
                + "/route/v1/driving/"
                + coords
                + "?overview=full&geometries=geojson"
            )

            data = self._open_json(url)

            if data.get("code") != "Ok":
                raise RuntimeError(data.get("code"))

            coords = data["routes"][0]["geometry"]["coordinates"]
            return [[lat, lon] for lon, lat in coords]

        except Exception:
            return route_to_latlngs(route, points)
