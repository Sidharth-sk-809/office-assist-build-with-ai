"""
Resume classification service using Vertex AI.
"""
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, Part
import vertexai
import os
import logging
from typing import Dict
import base64

logger = logging.getLogger(__name__)

# Initialize Vertex AI
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("VERTEX_AI_LOCATION", os.getenv("GCP_LOCATION", "us-central1"))

# Ensure we use a regional location for Vertex AI (not global)
if LOCATION == "global":
    LOCATION = "us-central1"

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)


async def classify_resume(pdf_content: bytes, filename: str) -> Dict:
    """
    Classify a resume using Vertex AI Gemini model.
    
    Args:
        pdf_content: Binary content of the PDF file
        filename: Name of the uploaded file
        
    Returns:
        Dictionary with classification results
    """
    try:
        if not PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID environment variable not set")
        
        # Initialize Gemini model
        model = GenerativeModel("gemini-1.5-pro")
        
        # Encode PDF content
        pdf_data = base64.b64encode(pdf_content).decode('utf-8')
        
        # Create the prompt for classification
        prompt = """
        Analyze this resume and classify the candidate's experience level as one of:
        - Junior: 0-2 years of experience, entry-level positions, limited technical skills
        - Mid: 3-5 years of experience, intermediate skills, some leadership experience
        - Senior: 6+ years of experience, advanced skills, leadership roles, architecture experience
        
        Provide your response in the following format:
        LEVEL: [Junior/Mid/Senior]
        CONFIDENCE: [0.0-1.0]
        REASONING: [Brief explanation of your classification]
        
        Be thorough in analyzing skills, experience duration, job titles, and responsibilities.
        """
        
        # Create parts for the request
        pdf_part = Part.from_data(pdf_content, mime_type="application/pdf")
        
        # Generate content
        response = model.generate_content([prompt, pdf_part])
        
        # Parse the response
        result_text = response.text
        logger.info(f"Classification response: {result_text}")
        
        # Extract classification details
        level = "Unknown"
        confidence = 0.0
        reasoning = ""
        
        for line in result_text.split('\n'):
            line = line.strip()
            if line.startswith("LEVEL:"):
                level = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except ValueError:
                    confidence = 0.0
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
        
        # Validate level
        valid_levels = ["Junior", "Mid", "Senior"]
        if level not in valid_levels:
            # Try to extract from the response text
            for valid_level in valid_levels:
                if valid_level.lower() in result_text.lower():
                    level = valid_level
                    break
        
        return {
            "level": level,
            "confidence": confidence,
            "reasoning": reasoning or result_text[:200]
        }
        
    except Exception as e:
        logger.error(f"Error classifying resume: {str(e)}")
        raise Exception(f"Resume classification failed: {str(e)}")
