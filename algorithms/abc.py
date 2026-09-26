import random


class ABCTSP:
    def __init__(
        self,
        matrix,
        colony_size=60,
        cycles=260,
        limit=45,
        closed=True,
    ):
        self.matrix = matrix
        self.n = len(matrix)
        self.food_count = max(10, colony_size // 2)
        self.cycles = cycles
        self.limit = limit
        self.closed = closed

    def solve(self):
        if self.n <= 1:
            return [], 0.0

        customers = list(range(1, self.n))
        sources = [
            random.sample(customers, len(customers))
            for _ in range(self.food_count)
        ]
        trials = [0] * self.food_count

        best = min(sources, key=self.cost)[:]
        best_cost = self.cost(best)

        for _ in range(self.cycles):
            self.employed_phase(sources, trials)
            self.onlooker_phase(sources, trials)
            self.scout_phase(sources, trials, customers)

            current = min(sources, key=self.cost)
            current_cost = self.cost(current)

            if current_cost < best_cost:
                best = current[:]
                best_cost = current_cost

        return best, best_cost

    def employed_phase(self, sources, trials):
        for i in range(self.food_count):
            self.try_improve(i, sources, trials)

    def onlooker_phase(self, sources, trials):
        fitness = [1.0 / (1.0 + self.cost(s)) for s in sources]
        total = sum(fitness)

        for _ in range(self.food_count):
            index = self.roulette(fitness, total)
            self.try_improve(index, sources, trials)

    def scout_phase(self, sources, trials, customers):
        for i in range(self.food_count):
            if trials[i] > self.limit:
                sources[i] = random.sample(customers, len(customers))
                trials[i] = 0

    def try_improve(self, index, sources, trials):
        candidate = self.neighbor(sources[index])

        if self.cost(candidate) < self.cost(sources[index]):
            sources[index] = candidate
            trials[index] = 0
        else:
            trials[index] += 1

    def roulette(self, fitness, total):
        if total <= 0:
            return random.randrange(len(fitness))

        r = random.random() * total
        acc = 0.0

        for i, value in enumerate(fitness):
            acc += value

            if acc >= r:
                return i

        return len(fitness) - 1

    def neighbor(self, route):
        candidate = route[:]

        if len(candidate) >= 2:
            i, j = random.sample(range(len(candidate)), 2)
            candidate[i], candidate[j] = candidate[j], candidate[i]

        return candidate

    def cost(self, route):
        if not route:
            return 0.0

        total = self.matrix[0][route[0]]

        for i in range(len(route) - 1):
            total += self.matrix[route[i]][route[i + 1]]

        if self.closed:
            total += self.matrix[route[-1]][0]

        return total
