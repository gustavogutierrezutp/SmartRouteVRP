"""Bridge between the browser worker (Pyodide) and the shared Python core.

Every public function returns a JSON string so the worker can hand it to
the page without converting Python objects.
"""

import json

from models.loader import load_points, load_vehicles
from models.solver import ALGORITHMS, solve_problem
from routing.osrm import RouteEngine


class BrowserRouteEngine(RouteEngine):
    """RouteEngine that fetches through the browser instead of urllib."""

    def _open_json(self, url):
        from pyodide.http import open_url  # synchronous XHR, fine inside a worker

        return json.loads(open_url(url).read())


class State:
    points = []
    vehicles = []
    distance_matrix = []
    duration_matrix = []
    source = "none"
    use_osrm = True


engine = BrowserRouteEngine()


def _rebuild_matrix():
    (
        State.distance_matrix,
        State.duration_matrix,
        State.source,
    ) = engine.build_matrix(State.points, use_osrm=State.use_osrm)


def load(points_path, vehicles_path, use_osrm):
    State.points = load_points(points_path)
    State.vehicles = load_vehicles(vehicles_path)
    State.use_osrm = bool(use_osrm)
    _rebuild_matrix()

    return json.dumps(
        {
            "points": [p._asdict() for p in State.points],
            "vehicles": len(State.vehicles),
            "source": State.source,
        }
    )


def set_osrm(use_osrm):
    State.use_osrm = bool(use_osrm)

    if State.points:
        _rebuild_matrix()

    return json.dumps({"source": State.source})


def _cost(value):
    return None if value == float("inf") else round(value, 3)


def solve(problem, algorithm):
    if not State.points:
        raise RuntimeError("Primero pulse Cargar.")

    algorithms = ALGORITHMS if algorithm == "Todos" else [algorithm]

    results = [
        solve_problem(
            problem,
            name,
            State.points,
            State.vehicles,
            State.distance_matrix,
            State.duration_matrix,
            source=State.source,
        )
        for name in algorithms
    ]

    best = min(results, key=lambda s: s.cost)
    layers = []

    if best.cost != float("inf"):
        use_real_geometry = State.use_osrm and State.source.startswith("OSRM")

        for i, route in enumerate(best.routes):
            layers.append(
                {
                    "name": "{} ruta {}".format(best.algorithm, i + 1),
                    "route": route,
                    "path": engine.route_geometry(
                        route,
                        State.points,
                        use_osrm=use_real_geometry,
                    ),
                }
            )

    return json.dumps(
        {
            "results": [
                {
                    "problem": s.problem,
                    "algorithm": s.algorithm,
                    "cost": _cost(s.cost),
                    "routes": s.routes,
                    "source": s.source,
                    "feasible": s.feasible,
                    "penalty": _cost(s.penalty),
                    "summary": s.summary(),
                }
                for s in results
            ],
            "best": results.index(best),
            "layers": layers,
        }
    )
