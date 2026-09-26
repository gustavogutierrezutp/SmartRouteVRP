import ui


class ResultsDataSource:
    def __init__(self, solutions):
        self.solutions = solutions

    def tableview_number_of_rows(self, tableview, section):
        return len(self.solutions)

    def tableview_cell_for_row(self, tableview, section, row):
        solution = self.solutions[row]

        cell = ui.TableViewCell("subtitle")
        cell.text_label.text = "{} - {}".format(
            solution.problem,
            solution.algorithm,
        )

        cost = (
            "INF"
            if solution.cost == float("inf")
            else "{:.2f} km".format(solution.cost)
        )

        state = "OK" if solution.feasible else "PEN {:.1f}".format(solution.penalty)

        cell.detail_text_label.text = "{} | {} rutas | {} | {}".format(
            cost,
            len(solution.routes),
            solution.source,
            state,
        )

        return cell


class ResultsView(ui.View):
    def __init__(self, solutions):
        super().__init__()

        self.name = "Comparación"
        self.background_color = "white"

        self.data_source = ResultsDataSource(solutions)

        self.table = ui.TableView()
        self.table.data_source = self.data_source
        self.table.delegate = self.data_source
        self.add_subview(self.table)

        self.close_button = ui.Button(title="Cerrar")
        self.close_button.action = self.close_action
        self.add_subview(self.close_button)

    def layout(self):
        self.close_button.frame = (10, 10, self.width - 20, 44)
        self.table.frame = (0, 64, self.width, self.height - 64)

    def close_action(self, sender):
        self.close()
