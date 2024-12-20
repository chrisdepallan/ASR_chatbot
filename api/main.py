from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import os
from dotenv import load_dotenv
from fastapi.responses import Response
from pathlib import Path
from fastapi.responses import FileResponse
import uuid
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
# home page
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
# test openai
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

# transcribe audio endpoint
#not used anymore but could be used for future
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

# chat completion endpoint
@app.post("/chat")
async def chat_completion(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")
        conversation_history = data.get("conversation_history", [])
        
        # Get chat completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history
        )
        
        response_text = response.choices[0].message.content
        
        # Generate speech from the response
        speech_file_name = f"speech_{uuid.uuid4()}.mp3"
        speech_file_path = Path(__file__).parent / "static" / "audio" / speech_file_name
        
        # Ensure the audio directory exists
        speech_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate speech
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=response_text
        )
        
        # Save the audio file
        audio_response.stream_to_file(str(speech_file_path))
        
        return {
            "status": "success", 
            "response": response_text,
            "audio_url": f"/static/audio/{speech_file_name}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}