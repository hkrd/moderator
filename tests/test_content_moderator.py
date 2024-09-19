import json
import pytest
from unittest import mock
from src.scripts.content_moderator import (
    moderate_message,
    process_message,
    process_conversations,
    moderate_conversations,
)
from openai import OpenAIError


@pytest.fixture
def mock_moderation_response():
    return {
        "id": "modr-123",
        "model": "text-moderation-latest",
        "results": [
            {
                "categories": {
                    "sexual": True,
                    "hate": False,
                    "violence": False,
                },
                "category_scores": {
                    "sexual": 0.98,
                    "hate": 0.01,
                    "violence": 0.05,
                },
            }
        ],
    }


@pytest.fixture
def mock_category_scores():
    # Create a mock for CategoryScores
    category_scores = mock.MagicMock()
    category_scores.sexual = 0.98
    category_scores.hate = 0.01
    category_scores.violence = 0.05
    return category_scores


@pytest.fixture
def mock_categories():
    # Create a mock for Categories
    categories = mock.MagicMock()
    categories.sexual = True
    categories.hate = False
    categories.violence = False
    return categories


@pytest.fixture
def mock_moderation(mock_category_scores, mock_categories):
    # Create a mock for Moderation
    moderation = mock.MagicMock()
    moderation.category_scores = mock_category_scores
    moderation.categories = mock_categories
    moderation_resp = mock.MagicMock()
    moderation_resp.results = [moderation]

    return moderation_resp


@pytest.fixture
def sample_message():
    return {
        "message_id": "1234",
        "content": "This is a test message.",
    }


@pytest.fixture
def categories():
    return ["sexual", "hate", "violence"]


# Sample conversation data
conversations = [
    {
        "messages": [
            {"message_id": 1, "content": "This is a sexual message"},
            {"message_id": 2, "content": "This is a hate message"},
        ]
    }
]


# Test the `moderate_message` function
@mock.patch("openai.moderations.create")
@mock.patch("openai.api_key", "mock-api-key")  # Mock the api_key
def test_moderate_message(mock_create, mock_moderation_response):
    moderation = mock.MagicMock()
    moderation.category_scores = mock_moderation_response["results"][0][
        "category_scores"
    ]

    mock_create.return_value.results = [moderation]

    content = "This is a test message"
    response = moderate_message(content)

    assert response.category_scores["sexual"] == 0.98
    assert response.category_scores["hate"] == 0.01


# Test the `process_message` function
@mock.patch("openai.moderations.create")
@mock.patch("openai.api_key", "mock-api-key")  # Mock the api_key
def test_process_message(mock_create, mock_moderation, sample_message, categories):
    # Mock the response from the OpenAI API
    mock_create.return_value = mock_moderation

    # Call the function with the sample message
    result = process_message(sample_message, categories)

    # Assert that the result is as expected
    assert result["message_id"] == "1234"
    assert result["content"] == "This is a test message."
    assert result["category_scores"]["sexual"] == 0.98
    assert result["category_scores"]["hate"] == 0.01
    assert result["category_scores"]["violence"] == 0.05


# Test `process_conversations`
@mock.patch("src.scripts.content_moderator.process_message")
def test_process_conversations(mock_process_message):
    mock_process_message.return_value = {
        "message_id": 1,
        "category_scores": {"sexual": 0.9, "violence": 0.7},
    }

    categories = ["sexual", "violence"]
    num_threads = 2

    result = process_conversations(conversations, categories, num_threads)

    assert len(result) == 2
    assert result[0]["message_id"] == 1
    assert result[0]["category_scores"]["sexual"] == 0.9


# Test `moderate_conversations`
@mock.patch("src.scripts.content_moderator.process_conversations")
@mock.patch("src.scripts.content_moderator.openai")
def test_moderate_conversations(mock_openai, mock_process_conversations, tmp_path):
    # Mocking API key and conversations
    api_key_file = tmp_path / "api_key.txt"
    api_key_file.write_text("test-api-key")
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(conversations))
    output_file = tmp_path / "output.json"

    # Mock processing of conversations
    mock_process_conversations.return_value = [
        {"message_id": 1, "category_scores": {"sexual": 0.9, "violence": 0.7}}
    ]

    # Test the moderation process
    moderate_conversations(
        str(input_file), str(output_file), "sexual,violence", 2, str(api_key_file)
    )

    # Check that output file was written with moderated content
    with open(output_file, "r") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["message_id"] == 1
        assert data[0]["category_scores"]["sexual"] == 0.9


# Test handling API errors
@mock.patch("src.scripts.content_moderator.moderate_message")
def test_process_message_api_error(mock_moderate_message):
    # Simulate API error
    mock_moderate_message.side_effect = OpenAIError("API Error")

    message = {"message_id": 1, "content": "This is a sexual message"}
    categories = ["sexual", "violence"]

    result = process_message(message, categories)

    assert result == {}  # Expecting empty result on API error
