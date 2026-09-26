import math


def haversine_km(a, b):
    radius_km = 6371.0

    lat1 = math.radians(a.lat)
    lon1 = math.radians(a.lon)
    lat2 = math.radians(b.lat)
    lon2 = math.radians(b.lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    return 2 * radius_km * math.asin(math.sqrt(h))


def build_haversine_matrix(points):
    n = len(points)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = haversine_km(points[i], points[j])

    return matrix


def build_duration_matrix(distance_matrix, speed_kmh=28.0):
    return [
        [(distance / speed_kmh) * 60.0 for distance in row]
        for row in distance_matrix
    ]


def route_distance(route, matrix, closed=True):
    if not route:
        return 0.0

    total = 0.0

    if closed:
        total += matrix[0][route[0]]

    for i in range(len(route) - 1):
        total += matrix[route[i]][route[i + 1]]

    if closed:
        total += matrix[route[-1]][0]

    return total


def route_to_latlngs(route, points):
    return [[points[i].lat, points[i].lon] for i in route]
