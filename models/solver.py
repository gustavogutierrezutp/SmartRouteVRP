"""UI-independent solving pipeline shared by the Pythonista and web front ends."""

from algorithms.abc import ABCTSP
from algorithms.aco import ACOTSP
from algorithms.ga import GeneticTSP
from algorithms.som import SOMTSP
from models.core import Solution
from models.cvrp import as_routes, split_capacity
from models.tsp import as_route
from models.vrptw import split_vrptw

PROBLEMS = ["TSP", "CVRP", "OVRP", "VRPTW"]
ALGORITHMS = ["GA", "ACO", "SOM", "ABC"]


def solve_tsp(algorithm, points, distance_matrix, closed=True):
    if algorithm == "GA":
        return GeneticTSP(distance_matrix, closed=closed).solve()

    if algorithm == "ACO":
        return ACOTSP(distance_matrix, closed=closed).solve()

    if algorithm == "SOM":
        return SOMTSP(points, closed=closed).solve(distance_matrix)

    if algorithm == "ABC":
        return ABCTSP(distance_matrix, closed=closed).solve()

    raise ValueError("Algoritmo no reconocido: {}".format(algorithm))


def solve_problem(
    problem,
    algorithm,
    points,
    vehicles,
    distance_matrix,
    duration_matrix,
    source="unknown",
    start_time=480.0,
):
    closed = problem != "OVRP"
    tsp_route, tsp_cost = solve_tsp(algorithm, points, distance_matrix, closed=closed)

    feasible = True
    penalty = 0.0

    if problem == "TSP":
        routes = [as_route(tsp_route, closed=True)]
        cost = tsp_cost

    elif problem == "OVRP":
        routes = [as_route(tsp_route, closed=False)]
        cost = tsp_cost

    elif problem == "CVRP":
        raw_routes, cost = split_capacity(
            tsp_route,
            points,
            vehicles,
            distance_matrix,
            closed=True,
        )
        routes = as_routes(raw_routes, closed=True)
        feasible = cost != float("inf")

    elif problem == "VRPTW":
        raw_routes, cost, feasible, penalty = split_vrptw(
            tsp_route,
            points,
            vehicles,
            distance_matrix,
            duration_matrix,
            closed=True,
            start_time=start_time,
        )
        routes = as_routes(raw_routes, closed=True)

    else:
        raise ValueError("Problema no reconocido: {}".format(problem))

    return Solution(
        problem=problem,
        algorithm=algorithm,
        cost=cost,
        routes=routes,
        source=source,
        feasible=feasible,
        penalty=penalty,
    )
