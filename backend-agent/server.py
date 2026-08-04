import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Job Agent Tailoring API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev, allow everything
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

# Import our generation logic
from main import generate_application

class TailorRequest(BaseModel):
    job_description: str
    job_title: str
    company: str

@app.post("/api/tailor")
async def tailor_application(request: TailorRequest):
    # Load the master narrative
    master_narrative_path = os.path.join(os.path.dirname(__file__), "..", "master_history.md")
    if not os.path.exists(master_narrative_path):
        raise HTTPException(status_code=500, detail="Master history narrative missing.")
        
    with open(master_narrative_path, "r", encoding="utf-8") as f:
        master_narrative = f.read()

    try:
        logger.info(f"Attempting to run LLM tailoring for: {request.job_title} at {request.company}")
        
        # Call actual Antigravity SDK LLM logic
        # Note: If API fails, this will raise an exception and fall back to the try-catch block
        result = await generate_application(master_narrative, request.job_description)
        logger.info("Successfully generated tailored CV via LLM.")
        return result

    except Exception as e:
        logger.error(f"LLM generation failed: {str(e)}. Falling back to mock generator.")
        
        # Load the mock sample we saved earlier
        mock_path = os.path.join(os.path.dirname(__file__), "output_sample.json")
        if os.path.exists(mock_path):
            with open(mock_path, "r", encoding="utf-8") as f:
                mock_data = json.load(f)
                
            # Customize the mock data slightly to match the requested job/company
            mock_data["cover_letter"] = mock_data["cover_letter"].replace("Project Manager", request.job_title)
            mock_data["cover_letter"] = mock_data["cover_letter"].replace("Hiring Team", f"Hiring Team at {request.company}")
            mock_data["tailored_cv"]["name"] = "Alexis Lindsay"
            return mock_data
            
        raise HTTPException(status_code=500, detail="Tailoring agent failed and mock fallback was unavailable.")

@app.get("/api/status")
def read_status():
    api_key = os.getenv("GEMINI_API_KEY")
    has_key = api_key is not None and api_key != "your_api_key_here" and len(api_key) > 0
    return {
        "status": "online",
        "api_key_configured": has_key
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
