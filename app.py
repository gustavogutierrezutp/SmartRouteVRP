import os

import console
import ui

from algorithms.abc import ABCTSP
from algorithms.aco import ACOTSP
from algorithms.ga  import GeneticTSP
from algorithms.som import SOMTSP
from models.core    import Solution
from models.cvrp    import as_routes, split_capacity
from models.loader  import load_points, load_vehicles
from models.tsp     import as_route
from models.vrptw   import split_vrptw
from routing.osrm   import RouteEngine
from views.mapview  import build_map_html
from views.tables   import ResultsView


PROBLEMS   = ["TSP", "CVRP", "OVRP", "VRPTW"]
ALGORITHMS = ["GA", "ACO", "SOM", "ABC", "Todos"]


class SmartRouteVRPApp(ui.View):
	def __init__(self):
		super().__init__()
		
		self.name = "SmartRouteVRP v2.2"
		self.background_color = "white"
		
		self.root_dir = os.path.dirname(__file__)
		self.data_dir = os.path.join(self.root_dir, "data")
		
		self.points = []
		self.vehicles = []
		self.distance_matrix = []
		self.duration_matrix = []
		self.matrix_source = "none"
		self.results = []
		self.route_layers = []
		
		self.problem_name = "TSP"
		self.use_osrm = True
		
		self.engine = RouteEngine()
		
		self.build_ui()
		self.show_empty_map()
		
	def build_ui(self):
		screen_width, screen_height = ui.get_screen_size()
		
		self.header = ui.View(frame=(0, 0, screen_width, 96))
		self.header.background_color = "#f2f2f7"
		self.add_subview(self.header)
		
		self.problem_selector = ui.SegmentedControl(
			frame=(8, 8, screen_width - 118, 34)
		)
		self.problem_selector.segments = PROBLEMS
		self.problem_selector.selected_index = 0
		self.problem_selector.action = self.problem_changed_action
		self.header.add_subview(self.problem_selector)
		
		self.osrm_label = ui.Label(frame=(screen_width - 104, 8, 48, 34))
		self.osrm_label.text = "OSRM"
		self.osrm_label.alignment = ui.ALIGN_RIGHT
		self.osrm_label.font = ("<system-bold>", 13)
		self.header.add_subview(self.osrm_label)
		
		self.osrm_switch = ui.Switch(frame=(screen_width - 52, 9, 44, 32))
		self.osrm_switch.value = True
		self.osrm_switch.action = self.osrm_switch_action
		self.header.add_subview(self.osrm_switch)
		
		self.algorithm_selector = ui.SegmentedControl(
			frame=(8, 52, screen_width - 16, 32)
		)
		self.algorithm_selector.segments = ALGORITHMS
		self.algorithm_selector.selected_index = 0
		self.header.add_subview(self.algorithm_selector)
		
		self.web = ui.WebView(
			frame=(0, 96, screen_width, screen_height - 176)
		)
		self.add_subview(self.web)
		
		self.footer = ui.View(frame=(0, screen_height - 80, screen_width, 80))
		self.footer.background_color = "#f2f2f7"
		self.add_subview(self.footer)
		
		self.build_footer_buttons(screen_width)
		
	def build_footer_buttons(self, width):
		titles = ["Cargar", "Resolver", "Comparar", "Ayuda"]
		button_width = width / 4.0
		
		for i, title in enumerate(titles):
			button = ui.Button(
				frame=(i * button_width + 4, 10, button_width - 8, 50)
			)
			button.title = title
			button.background_color = "white"
			button.corner_radius = 8
			button.border_width = 1
			button.border_color = "#cccccc"
			
			if title == "Cargar":
				button.action = self.load_action
			elif title == "Resolver":
				button.action = self.solve_action
			elif title == "Comparar":
				button.action = self.compare_action
			else:
				button.action = self.help_action
				
			self.footer.add_subview(button)
			
	def layout(self):
		width, height = self.width, self.height
		
		self.header.frame = (0, 0, width, 96)
		self.problem_selector.frame = (8, 8, width - 118, 34)
		self.osrm_label.frame = (width - 104, 8, 48, 34)
		self.osrm_switch.frame = (width - 52, 9, 44, 32)
		self.algorithm_selector.frame = (8, 52, width - 16, 32)
		
		self.web.frame = (0, 96, width, height - 176)
		
		self.footer.frame = (0, height - 80, width, 80)
		button_width = width / 4.0
		
		for i, button in enumerate(self.footer.subviews):
			button.frame = (i * button_width + 4, 10, button_width - 8, 50)
			
	def show_empty_map(self):
		self.web.load_html(build_map_html([], [], source="Sin datos"))
		
	def refresh_map(self):
		source = "Distancia: {}".format(self.matrix_source)
		html = build_map_html(self.points, self.route_layers, source=source)
		self.web.load_html(html)
		
	def problem_changed_action(self, sender):
		index = sender.selected_index
		
		if 0 <= index < len(PROBLEMS):
			self.problem_name = PROBLEMS[index]
			
		self.results = []
		self.route_layers = []
		
		if self.points:
			self.refresh_map()
			
	def osrm_switch_action(self, sender):
		self.use_osrm = bool(sender.value)
		self.results = []
		self.route_layers = []
		
		if self.points:
			self.rebuild_matrix()
			self.refresh_map()
			console.hud_alert("Matriz: {}".format(self.matrix_source))
			
	def rebuild_matrix(self):
		(
			self.distance_matrix,
			self.duration_matrix,
			self.matrix_source,
		) = self.engine.build_matrix(self.points, use_osrm=self.use_osrm)
		
	def load_action(self, sender):
		try:
			points_path = os.path.join(self.data_dir, "points.csv")
			vehicles_path = os.path.join(self.data_dir, "vehicles.csv")
			
			self.points = load_points(points_path)
			self.vehicles = load_vehicles(vehicles_path)
			
			self.rebuild_matrix()
			
			self.results = []
			self.route_layers = []
			self.refresh_map()
			
			console.hud_alert(
				"{} puntos, {} vehículos, {}".format(
					len(self.points),
					len(self.vehicles),
					self.matrix_source,
				)
			)
			
		except Exception as exc:
			console.alert(
				"Error cargando datos",
				str(exc),
				"OK",
				hide_cancel_button=True,
			)
			
	def solve_action(self, sender):
		if not self.points or not self.distance_matrix:
			console.alert(
				"Datos no cargados",
				"Primero pulse Cargar.",
				"OK",
				hide_cancel_button=True,
			)
			return
			
		algorithms = self.selected_algorithms()
		
		self.results = []
		self.route_layers = []
		
		for algorithm in algorithms:
			solution = self.solve_problem(algorithm)
			self.results.append(solution)
			
		best = min(self.results, key=lambda s: s.cost)
		
		if best.cost == float("inf"):
			console.alert(
				"Sin solución",
				"Revise demandas, capacidades o ventanas de tiempo.",
				"OK",
				hide_cancel_button=True,
			)
			return
			
		self.route_layers = self.build_route_layers(best)
		self.refresh_map()
		
		console.alert(
			"Mejor solución",
			best.summary(),
			"OK",
			hide_cancel_button=True,
		)
		
	def selected_algorithms(self):
		selected = ALGORITHMS[
			self.algorithm_selector.selected_index
		]
		
		if selected == "Todos":
			return ["GA", "ACO", "SOM", "ABC"]
			
		return [selected]
		
	def solve_problem(self, algorithm):
		closed = self.problem_name != "OVRP"
		tsp_route, tsp_cost = self.solve_tsp(algorithm, closed=closed)
		
		feasible = True
		penalty = 0.0
		
		if self.problem_name == "TSP":
			routes = [as_route(tsp_route, closed=True)]
			cost = tsp_cost
			
		elif self.problem_name == "OVRP":
			routes = [as_route(tsp_route, closed=False)]
			cost = tsp_cost
			
		elif self.problem_name == "CVRP":
			raw_routes, cost = split_capacity(
				tsp_route,
				self.points,
				self.vehicles,
				self.distance_matrix,
				closed=True,
			)
			routes = as_routes(raw_routes, closed=True)
			feasible = cost != float("inf")
			
		elif self.problem_name == "VRPTW":
			raw_routes, cost, feasible, penalty = split_vrptw(
				tsp_route,
				self.points,
				self.vehicles,
				self.distance_matrix,
				self.duration_matrix,
				closed=True,
				start_time=480.0,
			)
			routes = as_routes(raw_routes, closed=True)
			
		else:
			raise ValueError("Problema no reconocido: {}".format(self.problem_name))
			
		return Solution(
			problem=self.problem_name,
			algorithm=algorithm,
			cost=cost,
			routes=routes,
			source=self.matrix_source,
			feasible=feasible,
			penalty=penalty,
		)
		
	def solve_tsp(self, algorithm, closed=True):
		if algorithm == "GA":
			return GeneticTSP(self.distance_matrix, closed=closed).solve()
			
		if algorithm == "ACO":
			return ACOTSP(self.distance_matrix, closed=closed).solve()
			
		if algorithm == "SOM":
			return SOMTSP(self.points, closed=closed).solve(self.distance_matrix)
			
		if algorithm == "ABC":
			return ABCTSP(self.distance_matrix, closed=closed).solve()
			
		raise ValueError("Algoritmo no reconocido: {}".format(algorithm))
		
	def build_route_layers(self, solution):
		layers = []
		use_real_geometry = self.use_osrm and self.matrix_source.startswith("OSRM")
		
		for i, route in enumerate(solution.routes):
			path = self.engine.route_geometry(
				route,
				self.points,
				use_osrm=use_real_geometry,
			)
			
			layers.append(
				{
					"name": "{} ruta {}".format(solution.algorithm, i + 1),
					"route": route,
					"path": path,
				}
			)
			
		return layers
		
	def compare_action(self, sender):
		if not self.results:
			console.alert(
				"Sin resultados",
				"Primero pulse Resolver.",
				"OK",
				hide_cancel_button=True,
			)
			return
			
		ResultsView(self.results).present("sheet")
		
	def help_action(self, sender):
		text = (
			"SmartRouteVRP v2.2\n\n"
			"Cambios:\n"
			"- Selector visible de problema.\n"
			"- OSRM queda en la misma línea.\n"
			"- Código reformateado.\n\n"
			"Problemas:\n"
			"- TSP\n"
			"- CVRP\n"
			"- OVRP\n"
			"- VRPTW básico\n\n"
			"Algoritmos:\n"
			"- GA, ACO, SOM, ABC\n\n"
			"OSRM ON: rutas reales por calles.\n"
			"OSRM OFF: Haversine."
		)
		
		console.alert("Ayuda", text, "OK", hide_cancel_button=True)
		
		
if __name__ == "__main__":
	SmartRouteVRPApp().present("fullscreen")

