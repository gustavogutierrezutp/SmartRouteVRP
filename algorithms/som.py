import math
import random


class SOMTSP:
    def __init__(self, points, iterations=5000, neuron_factor=8, closed=True):
        self.points = points
        self.customers = points[1:]
        self.iterations = iterations
        self.neuron_count = max(20, len(self.customers) * neuron_factor)
        self.closed = closed

    def solve(self, matrix):
        if not self.customers:
            return [], 0.0

        coords = [(p.lat, p.lon) for p in self.customers]

        min_lat = min(lat for lat, _ in coords)
        max_lat = max(lat for lat, _ in coords)
        min_lon = min(lon for _, lon in coords)
        max_lon = max(lon for _, lon in coords)

        neurons = [
            [
                random.uniform(min_lat, max_lat),
                random.uniform(min_lon, max_lon),
            ]
            for _ in range(self.neuron_count)
        ]

        learning_rate0 = 0.8
        radius0 = self.neuron_count / 2.0

        for step in range(self.iterations):
            point = random.choice(self.customers)
            target = [point.lat, point.lon]
            winner = self.closest(neurons, target)

            progress = float(step) / float(max(1, self.iterations))
            learning_rate = learning_rate0 * (1.0 - progress)
            radius = max(1.0, radius0 * (1.0 - progress))

            for i in range(self.neuron_count):
                ring_distance = min(
                    abs(i - winner),
                    self.neuron_count - abs(i - winner),
                )
                influence = math.exp(
                    -(ring_distance ** 2) / (2.0 * radius ** 2)
                )

                neurons[i][0] += learning_rate * influence * (
                    target[0] - neurons[i][0]
                )
                neurons[i][1] += learning_rate * influence * (
                    target[1] - neurons[i][1]
                )

        assigned = []

        for point in self.customers:
            neuron_index = self.closest(neurons, [point.lat, point.lon])
            assigned.append((neuron_index, point.id))

        assigned.sort()
        route = [point_id for _, point_id in assigned]

        return route, self.cost(route, matrix)

    def closest(self, neurons, target):
        best = 0
        best_distance = float("inf")

        for i, neuron in enumerate(neurons):
            distance = (
                (neuron[0] - target[0]) ** 2
                + (neuron[1] - target[1]) ** 2
            )

            if distance < best_distance:
                best = i
                best_distance = distance

        return best

    def cost(self, route, matrix):
        if not route:
            return 0.0

        total = matrix[0][route[0]]

        for i in range(len(route) - 1):
            total += matrix[route[i]][route[i + 1]]

        if self.closed:
            total += matrix[route[-1]][0]

        return total
