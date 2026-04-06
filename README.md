# Office Assist API

A FastAPI backend application that integrates with Google Cloud Vertex AI for resume classification, RAG-based chat, and task grading.

## Features

### 1. Resume Classification (`/classify`)
- Accepts PDF resume uploads
- Uses Vertex AI Gemini to classify experience level (Junior/Mid/Senior)
- Returns confidence score and reasoning

### 2. Company Policy Chat (`/chat`)
- RAG-powered chat using Vertex AI Search
- Queries company policy data store
- Maintains conversation context
- Returns answers with source references

### 3. Task Grading (`/submit-task`)
- Accepts text or file submissions
- Grades against Job Readiness rubric using Gemini 1.5 Pro
- Saves results to Firestore
- Returns detailed feedback and scores

## Setup

### Prerequisites
- Python 3.8+
- Google Cloud Project with enabled APIs:
  - Vertex AI API
  - Firestore API
  - Discovery Engine API

### Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Cloud credentials:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

4. Configure environment variables:
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_LOCATION="us-central1"
export VERTEX_SEARCH_DATA_STORE_ID="your-data-store-id"
export VERTEX_SEARCH_ENGINE_ID="your-search-engine-id"
```

### Running the Application

Development mode:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Production mode:
```bash
python main.py
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### POST /classify
Classify a resume's experience level.

**Request:**
- Content-Type: multipart/form-data
- Body: PDF file

**Response:**
```json
{
  "level": "Senior",
  "confidence": 0.85,
  "reasoning": "Candidate has 8+ years experience with leadership roles..."
}
```

### POST /chat
Query company policies using RAG.

**Request:**
```json
{
  "user_input": "What is the vacation policy?",
  "conversation_id": "optional-conversation-id"
}
```

**Response:**
```json
{
  "answer": "The company offers 15 days of PTO...",
  "sources": [
    {
      "title": "Employee Handbook",
      "uri": "gs://bucket/handbook.pdf"
    }
  ],
  "conversation_id": "uuid"
}
```

### POST /submit-task
Submit a task for grading.

**Request:**
- Content-Type: multipart/form-data
- Body: 
  - task_text (optional): Text submission
  - file (optional): File submission

**Response:**
```json
{
  "task_id": "uuid",
  "score": 85.0,
  "feedback": "Strong technical implementation...",
  "timestamp": "2026-04-06T19:17:19.028Z"
}
```

## Error Handling

All endpoints include comprehensive error handling:
- Input validation
- Service-specific error messages
- Proper HTTP status codes
- Detailed logging

## Project Structure

```
office-assist/
├── main.py                          # FastAPI application
├── services/
│   ├── __init__.py
│   ├── resume_classifier.py        # Resume classification logic
│   ├── chat_service.py              # RAG chat logic
│   └── task_grader.py               # Task grading logic
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud Project ID | Required |
| `GCP_LOCATION` | GCP region | us-central1 |
| `VERTEX_SEARCH_DATA_STORE_ID` | Vertex AI Search data store ID | Required for /chat |
| `VERTEX_SEARCH_ENGINE_ID` | Vertex AI Search engine ID | Optional |
| `PORT` | Server port | 8000 |

## Security Notes

- Never commit service account keys
- Use environment variables for sensitive data
- Implement authentication/authorization for production
- Validate all file uploads
- Set appropriate CORS policies

## License

MIT
