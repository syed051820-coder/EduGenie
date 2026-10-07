from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load variables from .env into the process environment BEFORE settings reads them
load_dotenv()

from config import get_settings  # noqa: E402  (must come after load_dotenv)

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Make sure the folders StaticFiles/templates expect actually exist.
# FastAPI's StaticFiles raises at *startup* if the directory is missing,
# which is the #1 reason "app doesn't work" for this kind of project.
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="EduGenie",
    description="Google Gemini Powered Learning Assistant",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


# ---------------------------------------------------------
# GEMINI CLIENT (created lazily so a missing/bad key never crashes startup)
# ---------------------------------------------------------

_client = None


def get_gemini_client():
    global _client
    if _client is None:
        from google import genai

        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in .env")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EduGenie</title>
        <style>
            body {
                font-family: Arial;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }

            textarea {
                width: 100%;
                height: 150px;
                padding: 10px;
                font-size: 16px;
            }

            button {
                width: 100%;
                padding: 15px;
                margin-top: 10px;
                background: #2563eb;
                color: white;
                border: none;
                cursor: pointer;
            }

            #answer {
                margin-top: 20px;
                padding: 20px;
                background: #eee;
                white-space: pre-wrap;
            }
        </style>
    </head>

    <body>
        <h1>🎓 EduGenie</h1>
        <p>Learning Assistant</p>

        <textarea id="question"
            placeholder="Ask your question..."></textarea>

        <button onclick="askQuestion()">Ask EduGenie</button>

        <div id="answer">Answer will appear here...</div>

        <script>
            async function askQuestion() {
                const question =
                    document.getElementById("question").value;

                const answer =
                    document.getElementById("answer");

                answer.innerText = "Thinking...";

                const response = await fetch("/api/ask", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        question: question
                    })
                });

                const data = await response.json();

                answer.innerText =
                    data.answer || data.detail;
            }
        </script>
    </body>
    </html>
    """


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": "EduGenie",
        "demo_mode": settings.demo_mode or not settings.gemini_api_key,
        "model": settings.gemini_model,
    }


# ---------------------------------------------------------
# ASK ENDPOINT (the actual "learning assistant" feature)
# ---------------------------------------------------------

class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    demo_mode: bool


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    demo = settings.demo_mode or not settings.gemini_api_key

    if demo:
        return AskResponse(
            answer=(
                "(Demo mode — no Gemini API key configured) "
                f"You asked: '{question}'. Add a valid GEMINI_API_KEY to your "
                ".env file and set DEMO_MODE=false to get real answers."
            ),
            demo_mode=True,
        )

    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=question,
        )
        return AskResponse(answer=response.text, demo_mode=False)
    except Exception as exc:  # surface a clean error instead of a 500 traceback
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    