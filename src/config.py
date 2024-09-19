import os


def get_authorization_key() -> str | None:
    """Retrieve the custom authorization key for the FastAPI server."""
    return os.getenv("CUSTOM_API_KEY")
