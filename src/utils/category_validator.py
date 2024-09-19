import logging
import sys
from src.models import Category


def convert_to_enum(category_strings: list[str]) -> None:
    for cat_str in category_strings:
        try:
            Category(cat_str)
        except ValueError:
            raise


def validate_categories(categories_str: str) -> list[str]:
    """Parses and validates a comma-separated string of categories, uses all by default.

    Args:
        categories_str (str): string containing comma seperated categories to be validated

    Returns:
        list[str]: the validated list of category strings
    """

    all_categories = [member.value for member in Category]
    if not categories_str:  # If no input provided, return all categories
        return all_categories

    try:
        # Split and trim the categories from the input string
        categories = [category.strip() for category in categories_str.split(",")]

        convert_to_enum(categories)

        return categories
    except ValueError as e:
        logging.error(
            f"Invalid values for categories given: {e}. Choose only categories from: {all_categories}"
        )
        sys.exit(1)
