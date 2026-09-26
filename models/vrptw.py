from routing.geo import route_distance


def evaluate_route_tw(
    route,
    points,
    distance_matrix,
    duration_matrix,
    start_time=480.0,
    closed=True,
):
    if not route:
        return 0.0, 0.0, True

    time = start_time
    penalty = 0.0
    feasible = True
    previous = 0

    for customer_id in route:
        time += duration_matrix[previous][customer_id]
        point = points[customer_id]

        if time < point.tw_start:
            time = point.tw_start

        if time > point.tw_end:
            feasible = False
            penalty += time - point.tw_end

        time += point.service_time
        previous = customer_id

    if closed:
        time += duration_matrix[previous][0]

    distance = route_distance(route, distance_matrix, closed=closed)
    return distance, penalty, feasible


def split_vrptw(
    tsp_route,
    points,
    vehicles,
    distance_matrix,
    duration_matrix,
    closed=True,
    start_time=480.0,
):
    if not vehicles:
        return [], float("inf"), False, float("inf")

    routes = []
    current = []
    load = 0.0
    vehicle_idx = 0
    capacity = vehicles[0].capacity

    for customer_id in tsp_route:
        demand = points[customer_id].demand

        if demand > capacity:
            return [], float("inf"), False, float("inf")

        trial = current + [customer_id]
        _, penalty, _ = evaluate_route_tw(
            trial,
            points,
            distance_matrix,
            duration_matrix,
            start_time,
            closed,
        )

        should_split = current and (load + demand > capacity or penalty > 0)

        if should_split:
            routes.append(current)
            vehicle_idx += 1

            if vehicle_idx >= len(vehicles):
                return routes, float("inf"), False, float("inf")

            capacity = vehicles[vehicle_idx].capacity
            current = [customer_id]
            load = demand
        else:
            current = trial
            load += demand

    if current:
        routes.append(current)

    feasible = True
    total_distance = 0.0
    total_penalty = 0.0

    for route in routes:
        distance, penalty, ok = evaluate_route_tw(
            route,
            points,
            distance_matrix,
            duration_matrix,
            start_time,
            closed,
        )

        total_distance += distance
        total_penalty += penalty
        feasible = feasible and ok

    objective = total_distance + 0.20 * total_penalty
    return routes, objective, feasible, total_penalty
