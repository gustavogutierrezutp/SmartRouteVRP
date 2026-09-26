from routing.geo import route_distance


def split_capacity(tsp_route, points, vehicles, matrix, closed=True):
    if not vehicles:
        return [], float("inf")

    routes = []
    current = []
    current_load = 0.0
    vehicle_idx = 0
    capacity = vehicles[0].capacity

    for customer_id in tsp_route:
        demand = points[customer_id].demand

        if demand > capacity:
            return [], float("inf")

        if current and current_load + demand > capacity:
            routes.append(current)
            current = []
            current_load = 0.0
            vehicle_idx += 1

            if vehicle_idx >= len(vehicles):
                return routes, float("inf")

            capacity = vehicles[vehicle_idx].capacity

        current.append(customer_id)
        current_load += demand

    if current:
        routes.append(current)

    total = sum(route_distance(r, matrix, closed=closed) for r in routes)
    return routes, total


def as_routes(routes, closed=True):
    return [[0] + list(r) + ([0] if closed else []) for r in routes]
