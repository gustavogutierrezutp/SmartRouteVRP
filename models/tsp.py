def as_route(route, closed=True):
    return [0] + list(route) + ([0] if closed else [])
