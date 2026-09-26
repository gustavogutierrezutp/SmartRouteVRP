import json


def build_map_html(
    points,
    route_layers=None,
    title="SmartRouteVRP v2.2",
    source="",
):
    if route_layers is None:
        route_layers = []

    center_lat = points[0].lat if points else 4.8143
    center_lon = points[0].lon if points else -75.6946

    points_js = json.dumps(
        [
            {
                "id": p.id,
                "name": p.name,
                "lat": p.lat,
                "lon": p.lon,
                "demand": p.demand,
                "tw_start": p.tw_start,
                "tw_end": p.tw_end,
            }
            for p in points
        ]
    )

    layers_js = json.dumps(route_layers)

    return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
html, body, #map {{ width:100%; height:100%; margin:0; padding:0; }}
.legend {{
 position:absolute; bottom:14px; left:12px; background:white; padding:8px 10px;
 border-radius:8px; font-family:-apple-system,BlinkMacSystemFont,sans-serif; font-size:12px;
 z-index:999; box-shadow:0 1px 5px rgba(0,0,0,.3);
}}
</style>
</head>
<body>
<div id="map"></div>
<div class="legend"><b>SmartRouteVRP v2.2</b><br>{source}<br>TSP/CVRP/OVRP/VRPTW</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([{center_lat}, {center_lon}], 13);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
 maxZoom:19, attribution:'© OpenStreetMap'
}}).addTo(map);

var points = {points_js};
var layers = {layers_js};
var colors = ['red','blue','green','purple','orange','brown','black'];
var bounds = [];

function hm(m) {{
 var h = Math.floor(m / 60);
 var mm = Math.floor(m % 60);
 return String(h).padStart(2, '0') + ':' + String(mm).padStart(2, '0');
}}

points.forEach(function(p) {{
 var text = '<b>' + p.id + ' - ' + p.name + '</b><br>Demanda: ' + p.demand +
            '<br>Ventana: ' + hm(p.tw_start) + ' - ' + hm(p.tw_end);
 var marker = L.marker([p.lat, p.lon]).addTo(map);
 marker.bindPopup(text);
 bounds.push([p.lat, p.lon]);
}});

layers.forEach(function(layer, idx) {{
 var path = layer.path || [];
 var color = colors[idx % colors.length];

 if (path.length > 1) {{
   L.polyline(path, {{color:color, weight:4, opacity:0.82}}).addTo(map);
   path.forEach(function(x) {{ bounds.push(x); }});
 }}
}});

if (bounds.length > 1) {{
 map.fitBounds(bounds, {{padding:[24,24]}});
}}
</script>
</body>
</html>
""".format(
        title=title,
        center_lat=center_lat,
        center_lon=center_lon,
        points_js=points_js,
        layers_js=layers_js,
        source=source,
    )
