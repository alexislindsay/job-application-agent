import os
import json
import asyncio
from dotenv import load_dotenv
import pydantic
from google.antigravity import Agent, LocalAgentConfig

# Load environment variables
load_dotenv()

# Define the target schema using Pydantic
class ContactInfo(pydantic.BaseModel):
    email: str
    phone: str
    location: str
    linkedin: str
    website: str

class Experience(pydantic.BaseModel):
    company: str
    role: str
    start_date: str
    end_date: str
    bullets: list[str] = pydantic.Field(description="List of accomplishments and responsibilities tailored to the job description.")

class Education(pydantic.BaseModel):
    degree: str
    institution: str
    year: str

class TailoredCV(pydantic.BaseModel):
    name: str
    contact: ContactInfo
    summary: str = pydantic.Field(description="A professional summary tailored to the target role.")
    experience: list[Experience]
    education: list[Education]
    skills: list[str]

class ApplicationPackage(pydantic.BaseModel):
    cover_letter: str = pydantic.Field(description="A tailored cover letter formatted in markdown.")
    tailored_cv: TailoredCV = pydantic.Field(description="The structured CV tailored to the job description.")

async def generate_application(master_narrative: str, job_description: str) -> dict:
    """
    Takes a master narrative and a job description, then uses the LLM to tailor an application package.
    """
    # Configure the agent with the response schema
    config = LocalAgentConfig(
        model="gemini-2.0-flash",
        response_schema=ApplicationPackage,
        system_instruction="""You are an expert career consultant.
Your task is to take a Master Narrative (the truth) and a Job Description, and craft a highly compelling Application Package (Cover Letter + CV).
- Do not fabricate facts that are not in the master narrative.
- You may emphasize specific relevant parts of the narrative, reframe experiences to highlight transferable skills, and use the provided impressive metrics.
- Keep the CV concise, impactful, and specifically tailored to the keywords and requirements in the job description."""
    )

    prompt = f"**Job Description:**\n{job_description}\n\n**Master Narrative:**\n{master_narrative}"

    async with Agent(config) as agent:
        response = await agent.chat(prompt)
        
        # Access the structured output
        data = await response.structured_output()
        
        return data

async def main():
    # Load the master narrative
    master_narrative_path = os.path.join(os.path.dirname(__file__), "..", "master_history.md")
    with open(master_narrative_path, "r", encoding="utf-8") as f:
        master_narrative = f.read()

    # A dummy job description for testing
    dummy_job_desc = """
    We are looking for a highly organized and technical Project Manager to join our growing tech company.
    The ideal candidate has experience coordinating technical teams, a background in software development or QA, 
    and strong client-facing communication skills. PMP or Scrum Master experience is a plus.
    You will lead the delivery of web applications and manage stakeholder communications.
    """

    print("Generating application... (this may take a minute)")
    result = await generate_application(master_narrative, dummy_job_desc)
    
    # Save the result to a file for review
    output_path = os.path.join(os.path.dirname(__file__), "output_sample.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        
    print(f"Application package successfully generated and saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
