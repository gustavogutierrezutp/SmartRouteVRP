import csv

from .core import Point, Vehicle


def _float(row, key, default=0.0):
    value = row.get(key, "")

    if value is None or value == "":
        return float(default)

    return float(value)


def load_points(path):
    points = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            points.append(
                Point(
                    id=int(row["id"]),
                    name=row["name"],
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    demand=_float(row, "demand", 0),
                    service_time=_float(row, "service_time", 0),
                    tw_start=_float(row, "tw_start", 0),
                    tw_end=_float(row, "tw_end", 1440),
                )
            )

    points.sort(key=lambda p: p.id)
    return points


def load_vehicles(path):
    vehicles = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            vehicles.append(
                Vehicle(
                    id=int(row["id"]),
                    capacity=float(row["capacity"]),
                    max_time=float(row.get("max_time", 480) or 480),
                )
            )

    return vehicles
