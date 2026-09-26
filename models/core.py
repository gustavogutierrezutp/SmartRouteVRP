from collections import namedtuple

Point = namedtuple(
    "Point",
    "id name lat lon demand service_time tw_start tw_end",
)

Vehicle = namedtuple("Vehicle", "id capacity max_time")


class Solution:
    def __init__(
        self,
        problem,
        algorithm,
        cost,
        routes,
        source="unknown",
        feasible=True,
        penalty=0.0,
    ):
        self.problem = problem
        self.algorithm = algorithm
        self.cost = float(cost)
        self.routes = routes
        self.source = source
        self.feasible = feasible
        self.penalty = float(penalty)

    def summary(self):
        cost = "INF" if self.cost == float("inf") else "{:.2f} km".format(self.cost)
        state = "factible" if self.feasible else "con penalización"

        return "{} | {} | {} | {} rutas | {} | {}".format(
            self.problem,
            self.algorithm,
            cost,
            len(self.routes),
            self.source,
            state,
        )
