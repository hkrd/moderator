# Intro
`moderator` is a CLI tool and API that uses OpenAI moderator endpoint to classify conversations by a category and determine how much each sentence falls within a category. 
It is used to determine if a conversation is hateful or contains violence and such. Using this one could moderate a conversation and hide harmful messages for places like
forums, communities, live chats etc. An example conversations between female influencers and their users is given as an example here and moderated using the tool.


# Installing
`pip install -r requirements.txt`

`pip install -r requirements-dev.txt`

# Running
For API requests you need to add env variable with an api key as such:
`export CUSTOM_API_KEY=123`

To run the cli use:
`python main.py`
then follow on screen instructions. To run the server use `python main.py start-server` with optional parameter `--daemon`
access the server at `http://127.0.0.1:8000/docs` or the specified host:port that you provide

# Building
You can build the project into a wheel that can be installed with pip:
`python -m build`
Once installed with `pip install dist/mod-0.1.0-py3-none-any.whl` the package can be invoked with just `moderator` to start the cli

# Testing
both unit tests are included which can be run with `pytest tests/`

And a test client which calls the API and compares the category_scores to what
we have in the moderated file and calculates the % of discrepencies for each category
use it with 

`moderator test-moderation <moderation-file> <api_key> --categories <comma seperated>`

# Docker
- you can build the image with `docker build -t mod .`
- to run the server use `docker run -d -p 8000:8000 --name modd mod`
- to interract with the container as cli use `docker run --rm mod <command>`
- for example to run the test-moderation for a given IP (of the already running server inside another container) use 

`docker run --rm --network bridge mod test-moderation moderated_conversations.json 123 --api_url http://172.17.0.2:8000/moderate --categories sexual,hate,violence`

# Files Overview

`src/utils/openai_moderation_handler.py` - used to make calls against openai moderations endpoint and handle any errors gracefully in case of network failure

`src/utils/category_validator.py` - used to validate the categories entered by the user

`src/scripts/file_converter.py` - used to convert the conversations.txt into a structures json file

`src/scripts/content_moderator.py` - used to moderate the structured json and include category_scores from openai moderations endpoint

`src/scripts/test_client.py` - used to compare the category_scores from the moderated file against scores received from the API /moderate call and show discrepancies

`src/models.py` - used to define Pydantic models used for validation of the API requests and responses

`src/config.py` - used to get authorization API key from env var

`src/app.py` - contains the API server code and endpoint /moderate 

`src/cli.py` - provides the CLI logic that allows you to interract with the project and call all other functionality

`/main.py` - entry point for the project

`/tests` - unit-tests to unit test main functionalities