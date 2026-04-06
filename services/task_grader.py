"""
Task grading service using Gemini 1.5 Pro and Firestore.
"""
from google.cloud import firestore
from vertexai.generative_models import GenerativeModel
import vertexai
import os
import logging
from typing import Dict, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Initialize Vertex AI
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("VERTEX_AI_LOCATION", os.getenv("GCP_LOCATION", "us-central1"))

# Ensure we use a regional location for Vertex AI (not global)
if LOCATION == "global":
    LOCATION = "us-central1"

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)

# Initialize Firestore
db = firestore.Client(project=PROJECT_ID) if PROJECT_ID else None

# Job Readiness Rubric
JOB_READINESS_RUBRIC = """
Job Readiness Grading Rubric (0-100 scale):

1. Technical Competency (40 points):
   - Demonstrates understanding of core concepts (20 points)
   - Applies best practices and patterns (10 points)
   - Code quality and structure (10 points)

2. Problem-Solving (30 points):
   - Identifies the problem correctly (10 points)
   - Proposes effective solutions (10 points)
   - Considers edge cases and errors (10 points)

3. Communication (20 points):
   - Clear and concise explanation (10 points)
   - Proper documentation (10 points)

4. Professionalism (10 points):
   - Attention to detail (5 points)
   - Completeness of submission (5 points)

Total: 100 points

Provide a detailed breakdown of the score and constructive feedback.
"""


async def grade_task(submission_content: str, file_name: Optional[str] = None) -> Dict:
    """
    Grade a task submission using Gemini 1.5 Pro and save to Firestore.
    
    Args:
        submission_content: Text content of the submission
        file_name: Optional file name
        
    Returns:
        Dictionary with grading results
    """
    try:
        if not PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID environment variable not set")
        
        # Initialize Gemini model
        model = GenerativeModel("gemini-1.5-pro")
        
        # Create grading prompt
        prompt = f"""
        {JOB_READINESS_RUBRIC}
        
        Please grade the following submission according to the Job Readiness rubric above.
        
        Submission:
        {submission_content}
        
        Provide your response in the following format:
        SCORE: [0-100]
        
        BREAKDOWN:
        - Technical Competency: [0-40] - [brief comment]
        - Problem-Solving: [0-30] - [brief comment]
        - Communication: [0-20] - [brief comment]
        - Professionalism: [0-10] - [brief comment]
        
        FEEDBACK:
        [Detailed constructive feedback with strengths and areas for improvement]
        """
        
        # Generate grading
        response = model.generate_content(prompt)
        result_text = response.text
        
        logger.info(f"Grading response received: {result_text[:200]}")
        
        # Parse the response
        score = 0.0
        feedback = result_text
        
        for line in result_text.split('\n'):
            line = line.strip()
            if line.startswith("SCORE:"):
                try:
                    score_str = line.split(":", 1)[1].strip()
                    # Extract just the number
                    score = float(''.join(filter(lambda x: x.isdigit() or x == '.', score_str)))
                except (ValueError, IndexError):
                    score = 0.0
                    
        # Extract feedback section
        if "FEEDBACK:" in result_text:
            feedback = result_text.split("FEEDBACK:", 1)[1].strip()
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare document for Firestore
        task_document = {
            "task_id": task_id,
            "score": score,
            "feedback": feedback,
            "full_response": result_text,
            "submission_preview": submission_content[:500],
            "file_name": file_name,
            "timestamp": timestamp,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        # Save to Firestore
        if db:
            try:
                db.collection("task_submissions").document(task_id).set(task_document)
                logger.info(f"Task {task_id} saved to Firestore with score: {score}")
            except Exception as firestore_error:
                logger.error(f"Failed to save to Firestore: {str(firestore_error)}")
                # Continue even if Firestore save fails
        else:
            logger.warning("Firestore client not initialized, skipping save")
        
        return {
            "task_id": task_id,
            "score": score,
            "feedback": feedback,
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Error grading task: {str(e)}")
        raise Exception(f"Task grading failed: {str(e)}")
