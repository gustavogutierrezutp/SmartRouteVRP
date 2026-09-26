import random


class ACOTSP:
    def __init__(
        self,
        matrix,
        ants=50,
        iterations=230,
        alpha=1.0,
        beta=3.0,
        rho=0.25,
        q=100.0,
        closed=True,
    ):
        self.matrix = matrix
        self.n = len(matrix)
        self.ants = ants
        self.iterations = iterations
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.q = q
        self.closed = closed
        self.pheromone = [[1.0] * self.n for _ in range(self.n)]

    def solve(self):
        if self.n <= 1:
            return [], 0.0

        best = None
        best_cost = float("inf")

        for _ in range(self.iterations):
            routes = []

            for _ in range(self.ants):
                route = self.construct()
                cost = self.cost(route)
                routes.append((route, cost))

                if cost < best_cost:
                    best = route[:]
                    best_cost = cost

            self.evaporate()
            self.deposit(routes)

        return best, best_cost

    def construct(self):
        unvisited = set(range(1, self.n))
        route = []
        current = 0

        while unvisited:
            next_node = self.choose(current, unvisited)
            route.append(next_node)
            unvisited.remove(next_node)
            current = next_node

        return route

    def choose(self, current, unvisited):
        weights = []

        for node in unvisited:
            tau = self.pheromone[current][node] ** self.alpha
            eta = (1.0 / max(self.matrix[current][node], 0.0001)) ** self.beta
            weights.append((node, tau * eta))

        total = sum(weight for _, weight in weights)

        if total <= 0:
            return random.choice(list(unvisited))

        r = random.random() * total
        acc = 0.0

        for node, weight in weights:
            acc += weight

            if acc >= r:
                return node

        return weights[-1][0]

    def evaporate(self):
        for i in range(self.n):
            for j in range(self.n):
                self.pheromone[i][j] *= 1.0 - self.rho

    def deposit(self, routes):
        for route, cost in routes:
            amount = self.q / max(cost, 0.0001)
            full_route = [0] + route + ([0] if self.closed else [])

            for i in range(len(full_route) - 1):
                a = full_route[i]
                b = full_route[i + 1]

                self.pheromone[a][b] += amount
                self.pheromone[b][a] += amount

    def cost(self, route):
        if not route:
            return 0.0

        total = self.matrix[0][route[0]]

        for i in range(len(route) - 1):
            total += self.matrix[route[i]][route[i + 1]]

        if self.closed:
            total += self.matrix[route[-1]][0]

        return total
