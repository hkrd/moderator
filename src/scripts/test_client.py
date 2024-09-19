import json
import signal
import sys
import requests
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.utils.category_validator import validate_categories


stop_event = False


def load_results(file_path: str) -> dict[int, dict[str, Any]]:
    """
    Load moderation results from a JSON file and index by message_id.

    Args:
        file_path (str): Path to the JSON file with CLI moderation results.

    Returns:
        dict[int, dict[str, Any]]: dictionary of results indexed by message_id.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        results_list = json.load(file)

    # Convert list of results into a dictionary indexed by message_id
    results_dict = {result["message_id"]: result for result in results_list}
    return results_dict


def fetch_moderation_from_api(
    api_url: str, api_key: str, content: dict[str, Any], categories: list[str]
) -> dict[str, Any]:
    """
    Fetch moderation results from the FastAPI endpoint.

    Args:
        api_url (str): URL of the FastAPI moderation endpoint.
        api_key (str): Authorization key for the FastAPI endpoint.
        content (str): The content to be moderated.
        categories (list[str]): list of categories to check.

    Returns:
        dict[str, Any]: Moderation result for the given content.
    """

    if stop_event:
        return {}

    body = {
        "message_id": str(content["message_id"]),
        "content": content["content"],
        "categories": categories,
    }
    response = requests.post(
        api_url, json=body, headers={"Authorization": f"Bearer {api_key}"}
    )

    response.raise_for_status()
    api_result = response.json()

    # Extract the relevant fields from the API response
    return {
        "message_id": content["message_id"],
        "content": content["content"],
        "category_scores": {
            category: api_result["category_scores"].get(category, 0.0)
            for category in categories
        },
    }


def compare_results(
    file_results: dict[int, dict[str, Any]], api_result: dict[str, Any]
) -> None:
    """
    Compare the result from the API with the corresponding result from the file.

    Args:
        file_results (dict[int, dict[str, Any]]): Results from the JSON file.
        api_result (dict[str, Any]): Result from the API for a single content.
    """
    message_id = api_result["message_id"]
    file_result = file_results.get(int(message_id), {})

    if file_result:
        discrepancies = []
        file_scores = file_result.get("category_scores", {})
        api_scores = api_result.get("category_scores", {})

        for category in file_scores:
            file_score = file_scores.get(category, 0.0)
            api_score = api_scores.get(category, 0.0)

            if file_score != 0:
                percentage_discrepancy = abs(api_score - file_score) / file_score * 100
            else:
                percentage_discrepancy = 0.0

            discrepancies.append(
                {
                    "category": category,
                    "file_score": file_score,
                    "api_score": api_score,
                    "percentage_discrepancy": percentage_discrepancy,
                }
            )

        if discrepancies:
            print(f"Message ID: {message_id}")
            print(f"File Result: {file_result['category_scores']}")
            print(f"API Result: {api_result['category_scores']}")
            print("Discrepancies:")
            for discrepancy in discrepancies:
                print(
                    f"  Category: {discrepancy['category']} -> Discrepancy: {discrepancy['percentage_discrepancy']:.2f}%"
                )
            print()


def fetch_all_moderations(
    api_url: str,
    api_key: str,
    contents: list[dict[str, Any]],
    categories: list[str],
    num_threads: int,
    file_results: dict[int, dict[str, Any]],
) -> None:
    """
    Fetch moderation results for all contents using a thread pool and compare as results come in.

    Args:
        api_url (str): URL of the FastAPI moderation endpoint.
        api_key (str): Authorization key for the FastAPI endpoint.
        contents (list[dict[str, Any]]): list of content strings to be moderated.
        categories (list[str]): list of categories to check.
        num_threads (int): Number of threads to use for parallel requests.
        file_results (dict[int, dict[str, Any]]): Results from the JSON file.
    """
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {
            executor.submit(
                fetch_moderation_from_api, api_url, api_key, content, categories
            ): content
            for content in contents
        }

        for future in as_completed(futures):
            try:
                if stop_event:
                    print("Stopping early due to user interruption.")
                    break
                api_result = future.result()
                compare_results(file_results, api_result)
            except Exception as exc:
                print(f"An error occurred while processing content: {exc}")


def signal_handler(sig, frame):
    """
    Handle the signal to stop the script gracefully.
    """
    global stop_event
    stop_event = True
    print("Stopping all threads...")
    # Allow some time for threads to complete
    sys.exit(0)


def main(
    file_results: str, api_url: str, api_key: str, categories: str, num_threads: int
) -> None:
    """
    Compare moderation results from CLI and API in real-time.

    Args:
        file_results (str): Path to the JSON file with CLI moderation results.
        api_url (str): URL of the FastAPI moderation endpoint.
        api_key (str): Authorization key for the FastAPI endpoint.
        categories (str): Comma-separated list of categories to check.
        num_threads (int): Number of threads to use for parallel requests.
    """

    global stop_event

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # validate provided categories
    validated_categories = validate_categories(categories)

    # Load CLI results
    file_results_data = load_results(file_results)

    # Extract contents for moderation
    contents = [result for result in file_results_data.values()]

    # Fetch API results and compare in real-time
    fetch_all_moderations(
        api_url,
        api_key,
        contents,
        validated_categories,
        num_threads,
        file_results_data,
    )
