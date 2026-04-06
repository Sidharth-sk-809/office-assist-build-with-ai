"""
FastAPI application with Vertex AI integration for resume classification,
RAG-based chat, and task grading.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from services.resume_classifier import classify_resume
from services.chat_service import query_rag
from services.task_grader import grade_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Office Assist API",
    description="Backend API for resume classification, policy chat, and task grading",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ChatRequest(BaseModel):
    user_input: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[list] = None
    conversation_id: Optional[str] = None


class ClassificationResponse(BaseModel):
    level: str
    confidence: Optional[float] = None
    reasoning: Optional[str] = None


class TaskSubmissionResponse(BaseModel):
    task_id: str
    score: float
    feedback: str
    timestamp: str


class MaterialUploadResponse(BaseModel):
    filename: str
    gcs_uri: Optional[str] = None
    status: str
    message: str


# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Office Assist API"}


@app.post("/classify", response_model=ClassificationResponse)
async def classify_resume_endpoint(
    file: UploadFile = File(...)
):
    """
    Classify a resume PDF using Vertex AI to determine experience level.
    
    Args:
        file: PDF file of the resume
        
    Returns:
        Classification result (Junior, Mid, or Senior) with confidence and reasoning
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        logger.info(f"Processing resume classification for file: {file.filename}")
        
        # Call classification service
        result = await classify_resume(content, file.filename)
        
        return ClassificationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in resume classification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to classify resume: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint that queries Vertex AI Search data store for company policy answers.
    
    Args:
        request: ChatRequest with user input and optional conversation ID
        
    Returns:
        Answer from RAG system with sources
    """
    try:
        if not request.user_input or len(request.user_input.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="user_input cannot be empty"
            )
        
        logger.info(f"Processing chat request: {request.user_input[:50]}...")
        
        # Call RAG service
        result = await query_rag(
            user_input=request.user_input,
            conversation_id=request.conversation_id
        )
        
        return ChatResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )


@app.post("/submit-task", response_model=TaskSubmissionResponse)
async def submit_task_endpoint(
    task_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Submit a task for grading using Gemini 1.5 Pro.
    
    Args:
        task_text: Text submission (optional if file provided)
        file: File submission (optional if task_text provided)
        
    Returns:
        Grading result with score and feedback, saved to Firestore
    """
    try:
        # Validate that at least one input is provided
        if not task_text and not file:
            raise HTTPException(
                status_code=400,
                detail="Either task_text or file must be provided"
            )
        
        submission_content = task_text or ""
        file_name = None
        
        # If file is provided, read its content
        if file:
            file_content = await file.read()
            file_name = file.filename
            
            if len(file_content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is empty"
                )
            
            # Convert file content to text (basic implementation)
            try:
                submission_content += "\n" + file_content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="File must contain valid text content"
                )
        
        if len(submission_content.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Submission content cannot be empty"
            )
        
        logger.info(f"Processing task submission (file: {file_name})")
        
        # Call grading service
        result = await grade_task(
            submission_content=submission_content,
            file_name=file_name
        )
        
        return TaskSubmissionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in task submission: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process task submission: {str(e)}"
        )


@app.post("/upload-material", response_model=MaterialUploadResponse)
async def upload_material_endpoint(
    file: UploadFile = File(...)
):
    """
    Upload a training material PDF to Google Cloud Storage and trigger import to Vertex AI Search.
    
    Args:
        file: PDF file to upload
        
    Returns:
        Upload status and GCS URI
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Validate file size (10 MB limit)
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > 10:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size_mb:.2f} MB) exceeds 10 MB limit"
            )
        
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        logger.info(f"Uploading material: {file.filename} ({file_size_mb:.2f} MB)")
        
        # Import the upload service
        from services.material_uploader import upload_to_gcs
        
        # Upload to GCS
        result = await upload_to_gcs(content, file.filename)
        
        logger.info(f"Material uploaded successfully: {result.get('gcs_uri')}")
        
        return MaterialUploadResponse(
            filename=file.filename,
            gcs_uri=result.get('gcs_uri'),
            status="uploaded",
            message="Material uploaded successfully. It will be indexed within 10-30 minutes."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading material: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload material: {str(e)}"
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
