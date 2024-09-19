from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import openai
from src.config import get_authorization_key
from src.models import ModerationRequest, ModerationResponse
from src.utils.openai_moderation_handler import moderate_content


app = FastAPI()

# Security scheme
security = HTTPBearer()


def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifies the provided Authorization header.
    """
    if credentials.credentials != get_authorization_key():
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return credentials.credentials


@app.post("/moderate", response_model=ModerationResponse)
async def moderate_message(
    request: ModerationRequest, _: HTTPAuthorizationCredentials = Depends(verify_auth)
):
    try:
        moderation_response = moderate_content(content=request.content)
        if moderation_response:
            category_scores = moderation_response.category_scores
    except openai.OpenAIError as e:
        raise HTTPException(status_code=429, detail=f"OpenAI error: {str(e)}")

    # Filter the requested categories
    selected_scores = {
        category: float(getattr(category_scores, category))
        for category in request.categories
    }

    return ModerationResponse(
        message_id=request.message_id,
        content=request.content,
        category_scores=selected_scores,
    )
