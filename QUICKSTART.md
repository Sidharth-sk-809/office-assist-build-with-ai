# Office Assist API - Quick Start Guide

## Project Overview

This FastAPI application provides three AI-powered endpoints:

1. **`/classify`** - Resume classification using Vertex AI Gemini
2. **`/chat`** - RAG-based company policy Q&A using Vertex AI Search
3. **`/submit-task`** - Task grading with Gemini 1.5 Pro + Firestore storage

## Installation Complete ✓

All dependencies have been installed successfully.

## Before Running

### 1. Set up Google Cloud credentials

Download your service account key from Google Cloud Console and set:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
```

### 2. Configure environment variables

```bash
# Required for all endpoints
export GCP_PROJECT_ID="your-gcp-project-id"
export GCP_LOCATION="us-central1"

# Required for /chat endpoint
export VERTEX_SEARCH_DATA_STORE_ID="your-data-store-id"

# Optional
export PORT=8000
```

Or create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
# Then edit .env with your values
```

### 3. Enable required Google Cloud APIs

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Firestore API
gcloud services enable firestore.googleapis.com

# Enable Discovery Engine API (for RAG/chat)
gcloud services enable discoveryengine.googleapis.com
```

## Running the Application

### Option 1: Using the start script (recommended)
```bash
./start.sh
```

### Option 2: Direct uvicorn command
```bash
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Using Python
```bash
source venv/bin/activate
python main.py
```

## Testing the API

Once the server is running, you can:

1. **View interactive docs**: http://localhost:8000/docs
2. **View alternative docs**: http://localhost:8000/redoc
3. **Run test script**:
   ```bash
   python test_api.py
   ```

## Example API Calls

### 1. Classify Resume
```bash
curl -X POST http://localhost:8000/classify \
  -F "file=@resume.pdf"
```

### 2. Chat (Company Policy)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What is the vacation policy?"
  }'
```

### 3. Submit Task for Grading
```bash
# With text
curl -X POST http://localhost:8000/submit-task \
  -F "task_text=My solution here..."

# With file
curl -X POST http://localhost:8000/submit-task \
  -F "file=@solution.txt"
```

## Project Structure

```
office-assist/
├── main.py                      # Main FastAPI application
├── services/
│   ├── __init__.py
│   ├── resume_classifier.py    # /classify endpoint logic
│   ├── chat_service.py          # /chat endpoint logic
│   └── task_grader.py           # /submit-task endpoint logic
├── requirements.txt             # Dependencies
├── test_api.py                  # Test script
├── start.sh                     # Startup script
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
└── README.md                    # Full documentation
```

## Key Features

### Resume Classification
- Accepts PDF uploads
- Uses Gemini 1.5 Pro for analysis
- Returns: level (Junior/Mid/Senior), confidence, reasoning

### RAG Chat
- Queries Vertex AI Search data store
- Maintains conversation context
- Returns: answer with source citations

### Task Grading
- Accepts text or file submissions
- Grades against Job Readiness rubric:
  - Technical Competency (40 pts)
  - Problem-Solving (30 pts)
  - Communication (20 pts)
  - Professionalism (10 pts)
- Saves results to Firestore
- Returns: task_id, score, detailed feedback

## Error Handling

All endpoints include:
- Input validation
- Comprehensive error messages
- Proper HTTP status codes
- Detailed logging

## Next Steps

1. **Set up your Google Cloud credentials** (required)
2. **Configure environment variables** (required)
3. **Start the server** using one of the methods above
4. **Test endpoints** using the interactive docs or test script
5. **Customize** the rubric or prompts in the service files as needed

## Troubleshooting

### "GCP_PROJECT_ID not set" error
- Set the environment variable: `export GCP_PROJECT_ID="your-project-id"`

### "VERTEX_SEARCH_DATA_STORE_ID not set" error (for /chat)
- Create a Vertex AI Search data store in GCP
- Set the environment variable with your data store ID

### Authentication errors
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to valid service account key
- Verify the service account has necessary permissions

### Import errors
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Support

For issues or questions, refer to:
- Full documentation: `README.md`
- Google Cloud documentation: https://cloud.google.com/docs
- FastAPI documentation: https://fastapi.tiangolo.com/

---

**You're all set!** 🚀 Configure your credentials and start the server.
