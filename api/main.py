from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import os
from dotenv import load_dotenv
from fastapi.responses import Response
# from fastapi.middleware.trustedhost import TrustedHostMiddleware
# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# # Add middlewares
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["ust.chrisdepallan.com"])
# app.add_middleware(HTTPSRedirectMiddleware)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
# Load environment variables from .env file in development
if os.path.exists(".env"):
    load_dotenv()

# Get API key with error handling
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



@app.get("/test-openai")
async def test_openai():
    try:
        # Make a simple API call to test the connection
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=10
        )
        return {"status": "success", "message": "OpenAI API is working correctly"}
    except Exception as e:
        return {"status": "error", "message": str(e)}



@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Create a temporary file to store the uploaded audio
        with open(f"temp_{file.filename}", "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Open and transcribe the audio file
        with open(f"temp_{file.filename}", "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        # Clean up the temporary file
        os.remove(f"temp_{file.filename}")
        
        return {"status": "success", "transcription": transcription.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/chat")
async def chat_completion(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        
        return {"status": "success", "response": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/text-to-speech")
async def text_to_speech(request: Request):
    try:
        data = await request.json()
        text = data.get("text")
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        # Return the audio data directly
        return Response(
            content=response.content,
            media_type="audio/mpeg"
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}