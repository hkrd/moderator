import click
import json
import uuid
from typing import Any, Optional


def _parse_conversations(input_file: str) -> list[dict[str, Any]]:
    """Parses a conversation text file into a structured list of conversations.

    Each conversation consists of multiple messages between a user and a character.
    The function identifies each conversation, assigns a unique ID to the conversation,
    and assigns unique IDs to each message.

    Args:
        input_file (str): The path to the input text file containing the conversations.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, where each dictionary represents
        a conversation with fields `conversation_id`, `character_name`, and `messages`.
        Each message contains `message_id`, `role_idx`, and `content`.
    """
    conversations: list[dict[str, Any]] = []
    message_id_counter: int = 0

    with open(input_file, "r", encoding="utf-8") as file:
        file_content: str = file.read()

    raw_conversations: list[str] = file_content.strip().split("\n\n")

    for raw_conversation in raw_conversations:
        lines: list[str] = raw_conversation.strip().split("\n")
        if not lines:
            continue

        character_name: Optional[str] = None
        messages: list[dict[str, Any]] = []

        for line in lines:
            if line.startswith("USER:"):
                role_idx: int = 0
                content: str = line.split("USER:", 1)[1].strip()
            else:
                role_idx = 1
                character_name, content = line.split(":", 1)
                character_name = character_name.strip().title()
                content = content.strip()

            messages.append(
                {
                    "message_id": message_id_counter,
                    "role_idx": role_idx,
                    "content": content,
                }
            )
            message_id_counter += 1

        conversation: dict[str, Any] = {
            "conversation_id": str(uuid.uuid4()),
            "character_name": character_name,
            "messages": messages,
        }
        conversations.append(conversation)

    return conversations


def convert_to_json(input_file: str, output_file: str) -> None:
    """Converts a conversation text file to a structured JSON file.

    This function reads the input conversation text file, processes it into a structured
    format, and then writes the output to a JSON file. The structure includes unique IDs for
    each conversation and each message, with character names converted to title case.

    Args:
        input_file (str): The path to the input text file containing the conversations.
        output_file (str): The path to the output JSON file where the structured data will be saved.
    """
    conversations: list[dict[str, Any]] = _parse_conversations(input_file)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(conversations, file, ensure_ascii=False, indent=4)

    click.echo(f"Conversion complete! Structured JSON saved to {output_file}")
