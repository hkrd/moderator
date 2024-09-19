import os
import openai
from openai.types.moderation import Moderation
import time
import logging


def moderate_content(
    content: str,
    openai_key_file: str = "openai_key.txt",
    max_retries: int = 3,
    retry_delay: int = 1,
) -> None | Moderation:
    """
    Moderates the given content using OpenAI's moderation API with graceful error handling.

    Args:
        content (str): The content to moderate.
        max_retries (int): The maximum number of retry attempts in case of transient failures.
        retry_delay (int): Delay in seconds between retries.

    Returns:
        Dict[str, Any]: The moderation response or an empty dictionary if a failure occurred.
    """

    retries = 0
    # Give the option to define the openai key with env var instead
    if os.getenv("OPENAI_API_KEY"):
        api_key = os.getenv("OPENAI_API_KEY")
    else:
        with open(openai_key_file, "r") as key_file:
            api_key = key_file.read().strip()

    openai.api_key = api_key

    while retries < max_retries:
        try:
            # Call OpenAI's moderation API
            response = openai.moderations.create(input=content)

            # Return the response if successful
            return response.results[0]

        except openai.RateLimitError as e:
            logging.warning(
                f"Rate limit exceeded: {e}. Retrying in {retry_delay} seconds..."
            )
            retries += 1
            time.sleep(retry_delay)

        except openai.APIConnectionError as e:
            logging.error(
                f"Connection error: {e}. Retrying in {retry_delay} seconds..."
            )
            retries += 1
            time.sleep(retry_delay)

        except openai.OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            raise

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise

    logging.error("Max retries reached. Failed to moderate content.")
    return None
