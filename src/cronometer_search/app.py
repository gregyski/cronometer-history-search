from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.events import Key
from textual.widgets import Input, Static
from textual import on
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cronometer_search.loader import Meal
from cronometer_search.search import search_meals


def _meal_panel(meal: Meal, query: str) -> Panel:
    query_lower = query.lower()

    table = Table.grid(padding=(0, 2), expand=True)
    table.add_column(no_wrap=True, style="dim")
    table.add_column(ratio=1)
    table.add_column(justify="right")

    for food in meal.foods:
        name = Text(food.food_name)
        if query_lower in food.food_name.lower():
            name.stylize("bold yellow")
        table.add_row(food.amount, name, f"{food.kcal:.1f}")

    table.add_section()
    table.add_row(
        "",
        Text("Total", style="bold"),
        Text(f"{meal.total_kcal:.1f} kcal", style="bold"),
    )

    return Panel(
        table,
        title=f"[bold]{meal.day}[/bold] — {meal.group}",
        title_align="left",
    )


class CronometerApp(App):
    CSS = """
    Input {
        dock: top;
        margin: 1 2 0 2;
    }
    VerticalScroll {
        margin: 0 2;
    }
    Static {
        margin-bottom: 1;
    }
    """

    def __init__(self, meals: list[Meal], count: int) -> None:
        super().__init__()
        self._meals = meals
        self._count = count

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search food name…")
        yield VerticalScroll(id="results")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.query_one(Input).value = ""

    @on(Input.Changed)
    def update_results(self, event: Input.Changed) -> None:
        query = event.value
        results = search_meals(self._meals, query, self._count)
        scroll = self.query_one("#results", VerticalScroll)
        scroll.remove_children()
        for meal in results:
            scroll.mount(Static(_meal_panel(meal, query)))
