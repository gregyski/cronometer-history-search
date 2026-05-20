from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class FoodEntry:
    food_name: str
    amount: str
    kcal: float


@dataclass
class Meal:
    day: str
    group: str
    foods: list[FoodEntry] = field(default_factory=list)

    @property
    def total_kcal(self) -> float:
        return sum(f.kcal for f in self.foods)


def discover_csv(input_dir: Path) -> Path:
    csvs = list(input_dir.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")
    return max(csvs, key=lambda p: p.stat().st_mtime)


def load_meals(csv_path: Path) -> list[Meal]:
    df = pd.read_csv(
        csv_path,
        usecols=["Day", "Group", "Food Name", "Amount", "Energy (kcal)"],
    )
    df["Energy (kcal)"] = pd.to_numeric(df["Energy (kcal)"], errors="coerce").fillna(0.0)

    meals: list[Meal] = []
    for (day, group), group_df in df.groupby(["Day", "Group"], sort=False):
        foods = [
            FoodEntry(
                food_name=str(row["Food Name"]),
                amount=str(row["Amount"]),
                kcal=float(row["Energy (kcal)"]),
            )
            for _, row in group_df.iterrows()
        ]
        meals.append(Meal(day=str(day), group=str(group), foods=foods))

    meals.sort(key=lambda m: m.day, reverse=True)
    return meals
