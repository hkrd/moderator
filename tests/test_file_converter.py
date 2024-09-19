import pytest
from unittest import mock
from src.scripts.file_converter import _parse_conversations


@pytest.fixture
def raw_conversation_text():
    return (
        "USER: Hello there!\nCharacter: Hi!\n\n"
        "USER: How are you?\nCharacter: I'm good, thanks.\n\n"
        "USER: What is your name?\nCharacter: I am a character."
    )


@pytest.fixture
def expected_conversations():
    return [
        {
            "conversation_id": "mock-uuid-1",
            "character_name": "Character",
            "messages": [
                {"message_id": 0, "role_idx": 0, "content": "Hello there!"},
                {"message_id": 1, "role_idx": 1, "content": "Hi!"},
            ],
        },
        {
            "conversation_id": "mock-uuid-2",
            "character_name": "Character",
            "messages": [
                {"message_id": 2, "role_idx": 0, "content": "How are you?"},
                {"message_id": 3, "role_idx": 1, "content": "I'm good, thanks."},
            ],
        },
        {
            "conversation_id": "mock-uuid-3",
            "character_name": "Character",
            "messages": [
                {"message_id": 4, "role_idx": 0, "content": "What is your name?"},
                {"message_id": 5, "role_idx": 1, "content": "I am a character."},
            ],
        },
    ]


@mock.patch("src.scripts.file_converter.open")
def test_parse_conversations(mock_open, raw_conversation_text, expected_conversations):
    # Mock file reading
    mock_open.return_value.__enter__.return_value.read.return_value = (
        raw_conversation_text
    )

    # Mock UUID generation to return predictable values
    with mock.patch("src.scripts.file_converter.uuid.uuid4") as mock_uuid:

        # Fix the returned value for uuid.uuid4
        mock_uuid.side_effect = ["mock-uuid-1", "mock-uuid-2", "mock-uuid-3"]

        result = _parse_conversations("fake_path.txt")

    # Compare the result with the expected conversations
    assert result == expected_conversations
