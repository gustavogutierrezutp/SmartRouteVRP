"""PROTOTYPE — throwaway. Step-by-step SOM trace for the teaching view.

Copies the loop from algorithms/som.py but keeps state between calls so the
page can advance one iteration (or many) at a time and inspect everything.
Lives on branch prototype/som-teaching only.
"""

import json
import math
import random

from routing.geo import route_distance
from webapp import State, engine


class SomTrace:
    def __init__(self, points, iterations, neuron_factor, lr0, seed):
        self.rng = random.Random(seed)
        self.customers = points[1:]
        self.iterations = iterations
        self.n = max(20, len(self.customers) * neuron_factor)
        self.lr0 = lr0
        self.radius0 = self.n / 2.0
        self.step_index = 0

        lats = [p.lat for p in self.customers]
        lons = [p.lon for p in self.customers]
        self.neurons = [
            [self.rng.uniform(min(lats), max(lats)), self.rng.uniform(min(lons), max(lons))]
            for _ in range(self.n)
        ]
        self.last = None

    def schedule(self, step):
        progress = step / max(1, self.iterations)
        return self.lr0 * (1.0 - progress), max(1.0, self.radius0 * (1.0 - progress))

    def closest(self, target):
        return min(
            range(self.n),
            key=lambda i: (self.neurons[i][0] - target[0]) ** 2 + (self.neurons[i][1] - target[1]) ** 2,
        )

    def step(self):
        point = self.rng.choice(self.customers)
        target = [point.lat, point.lon]
        winner = self.closest(target)
        lr, radius = self.schedule(self.step_index)
        before = [n[:] for n in self.neurons]
        influence = []

        for i in range(self.n):
            ring = min(abs(i - winner), self.n - abs(i - winner))
            h = math.exp(-(ring ** 2) / (2.0 * radius ** 2))
            influence.append(h)
            self.neurons[i][0] += lr * h * (target[0] - self.neurons[i][0])
            self.neurons[i][1] += lr * h * (target[1] - self.neurons[i][1])

        self.step_index += 1
        self.last = {
            "target": point.id,
            "target_name": point.name,
            "winner": winner,
            "lr": lr,
            "radius": radius,
            "influence": influence,
            "before": before,
        }

    def tour(self):
        assigned = sorted((self.closest([p.lat, p.lon]), p.id) for p in self.customers)
        return [pid for _, pid in assigned]

    def snapshot(self, detail):
        tour = self.tour()
        lr, radius = self.schedule(self.step_index)
        return {
            "step": self.step_index,
            "iterations": self.iterations,
            "neurons": self.neurons,
            "lr": lr,
            "radius": radius,
            "neuron_count": self.n,
            "tour": [0] + tour + [0],
            "tour_length": route_distance(tour, State.distance_matrix, closed=True),  # follows the OSRM toggle
            "done": self.step_index >= self.iterations,
            "last": self.last if detail else None,
        }


_trace = None


def proto_som_reset(iterations, neuron_factor, lr0, seed):
    global _trace
    if not State.points:
        raise RuntimeError("Primero pulse Cargar.")
    _trace = SomTrace(State.points, int(iterations), int(neuron_factor), float(lr0), int(seed))
    return json.dumps(_trace.snapshot(detail=False))


def proto_som_step(count, detail=True):
    for _ in range(int(count)):
        if _trace.step_index >= _trace.iterations:
            break
        _trace.step()
    return json.dumps(_trace.snapshot(detail=bool(detail)))


def proto_route_geometry(tour_json):
    road = State.use_osrm and State.source.startswith("OSRM")
    path = engine.route_geometry(json.loads(tour_json), State.points, use_osrm=road)
    return json.dumps({"path": path})
