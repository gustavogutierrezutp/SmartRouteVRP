import random


class GeneticTSP:
    def __init__(
        self,
        matrix,
        pop_size=100,
        generations=320,
        mutation_rate=0.16,
        closed=True,
    ):
        self.matrix = matrix
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.closed = closed
        self.n = len(matrix)

    def solve(self):
        if self.n <= 1:
            return [], 0.0

        customers = list(range(1, self.n))
        population = [
            random.sample(customers, len(customers))
            for _ in range(self.pop_size)
        ]

        best = None
        best_cost = float("inf")

        for _ in range(self.generations):
            population.sort(key=self.cost)

            candidate_cost = self.cost(population[0])
            if candidate_cost < best_cost:
                best = population[0][:]
                best_cost = candidate_cost

            elite_count = max(2, self.pop_size // 8)
            new_population = population[:elite_count]

            while len(new_population) < self.pop_size:
                p1 = self.tournament(population)
                p2 = self.tournament(population)
                child = self.crossover(p1, p2)

                if random.random() < self.mutation_rate:
                    self.mutate(child)

                new_population.append(child)

            population = new_population

        return best, best_cost

    def cost(self, route):
        if not route:
            return 0.0

        total = self.matrix[0][route[0]]

        for i in range(len(route) - 1):
            total += self.matrix[route[i]][route[i + 1]]

        if self.closed:
            total += self.matrix[route[-1]][0]

        return total

    def tournament(self, population, k=5):
        sample = random.sample(population, min(k, len(population)))
        sample.sort(key=self.cost)
        return sample[0][:]

    def crossover(self, p1, p2):
        if len(p1) < 2:
            return p1[:]

        start, end = sorted(random.sample(range(len(p1)), 2))

        child = [None] * len(p1)
        child[start:end] = p1[start:end]

        fill = [x for x in p2 if x not in child]
        fill_index = 0

        for i in range(len(child)):
            if child[i] is None:
                child[i] = fill[fill_index]
                fill_index += 1

        return child

    def mutate(self, route):
        if len(route) < 2:
            return

        i, j = random.sample(range(len(route)), 2)
        route[i], route[j] = route[j], route[i]
