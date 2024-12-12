from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import os
from dotenv import load_dotenv

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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



