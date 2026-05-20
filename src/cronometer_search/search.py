from cronometer_search.loader import Meal

MIN_SEARCH_CHARS = 1


def search_meals(meals: list[Meal], query: str, count: int) -> list[Meal]:
    if len(query) < MIN_SEARCH_CHARS:
        return []

    query_lower = query.lower()
    results: list[Meal] = []
    for meal in meals:
        if any(query_lower in food.food_name.lower() for food in meal.foods):
            results.append(meal)
            if len(results) >= count:
                break
    return results
