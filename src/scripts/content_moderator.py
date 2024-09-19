from typing import Any
import click
import json
import openai
from openai.types.moderation import Moderation
from concurrent.futures import ThreadPoolExecutor, as_completed

import tqdm

from src.utils.category_validator import validate_categories
from src.utils.openai_moderation_handler import moderate_content


def moderate_message(
    content: str, openai_api_key: str = "openai_key.txt"
) -> None | Moderation:
    """Send a message content to the OpenAI moderation API.

    Args:
        content (str): The content of the message to be moderated.

    Returns:
        openai.Moderation: The response from the API containing category scores.
    """
    return moderate_content(content=content, openai_key_file=openai_api_key)


def process_message(
    message: dict[str, Any],
    categories: list[str],
    openai_api_key: str = "openai_key.txt",
) -> dict[str, Any]:
    """Process a single message by moderating its content and extracting category scores.

    Args:
        message (dict[str, Any]): A dictionary containing the message data.
        categories (list[str]): The list of categories to extract from the moderation response.

    Returns:
        dict[str, Any]: A dictionary containing the message_id, content, and selected category scores.
    """
    content = message["content"]
    message_id = message["message_id"]

    try:
        moderation_response = moderate_message(content, openai_api_key)
    except openai.OpenAIError as e:
        click.echo(f"Error moderating message {message_id}: {e}", err=True)
        return {}

    if moderation_response:
        category_scores = moderation_response.category_scores

        selected_scores = {
            category: getattr(category_scores, category) for category in categories
        }

        return {
            "message_id": message_id,
            "content": content,
            "category_scores": selected_scores,
        }

    return {}


def process_conversations(
    conversations: list[dict[str, Any]],
    categories: list[str],
    num_threads: int,
    openai_api_key: str = "openai_key.txt",
) -> list[dict[str, Any]]:
    """Process all messages in the conversations concurrently using threads.

    Args:
        conversations (list[dict[str, Any]]): A list of conversation dictionaries.
        categories (list[str]): The list of categories to extract from the moderation response.
        num_threads (int): The number of concurrent threads to use.

    Returns:
        list[dict[str, Any]]: A list of dictionaries containing the moderated messages.
    """
    moderated_messages = []
    all_messages = [
        message
        for conversation in conversations
        for message in conversation["messages"]
    ]
    total_messages = len(all_messages)
    pbar = tqdm.tqdm(total=total_messages)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(process_message, message, categories, openai_api_key)
            for message in all_messages
        ]

        try:
            for future in as_completed(futures):
                result = future.result()
                if result:
                    moderated_messages.append(result)
                pbar.update(n=1)
        except KeyboardInterrupt:
            click.echo("Process interrupted. Shutting down...", err=True)
            # Cancel remaining futures
            for future in futures:
                if not future.done():
                    future.cancel()
            # Shutdown the executor
            executor.shutdown(wait=False)
            raise
        finally:
            pbar.close()

    return moderated_messages


def moderate_conversations(
    input_file: str,
    output_file: str,
    categories: str,
    num_threads: int,
    api_key_file: str = "openai_key.txt",
) -> None:
    """Moderates the content of each message in the input file using OpenAI Moderation API.

    Args:
        input_file (str): The path to the input structured JSON file containing the conversations.
        output_file (str): The path to the output JSON file where the moderated data will be saved.
        categories (str): Comma seperated categories to extract from the moderation results.
        num_threads (int): The number of concurrent threads to use for processing.
        api_key_file (str): The path to the file containing the OpenAI API key.
    """

    with open(input_file, "r", encoding="utf-8") as file:
        conversations = json.load(file)

    # validate provided categories
    validated_categories = validate_categories(categories)

    try:
        moderated_messages = process_conversations(
            conversations, validated_categories, num_threads, api_key_file
        )
    except KeyboardInterrupt:
        click.echo("Moderation process interrupted.", err=True)
        return

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(moderated_messages, file, ensure_ascii=False, indent=4)

    click.echo(f"Moderation complete! Results saved to {output_file}")
