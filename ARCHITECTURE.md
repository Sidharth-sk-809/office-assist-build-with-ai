# Office Assist API - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                          │
│                    (Web, Mobile, cURL, Postman)                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                         FastAPI Server                               │
│                      (main.py - Port 8000)                          │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐              │
│  │  POST       │  │  POST       │  │  POST        │              │
│  │  /classify  │  │  /chat      │  │  /submit-task│              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘              │
│         │                 │                 │                       │
└─────────┼─────────────────┼─────────────────┼───────────────────────┘
          │                 │                 │
          │                 │                 │
┌─────────▼──────┐ ┌────────▼────────┐ ┌─────▼──────────┐
│   Service      │ │    Service      │ │    Service     │
│   Layer        │ │    Layer        │ │    Layer       │
└─────────┬──────┘ └────────┬────────┘ └─────┬──────────┘
          │                 │                 │
          │                 │                 │
┌─────────▼─────────────────▼─────────────────▼──────────────────────┐
│                    Google Cloud Platform                            │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Vertex AI   │  │  Vertex AI   │  │  Vertex AI   │            │
│  │  Gemini 1.5  │  │  Search      │  │  Gemini 1.5  │            │
│  │  Pro         │  │  (RAG)       │  │  Pro         │            │
│  └──────────────┘  └──────────────┘  └──────┬───────┘            │
│                                              │                      │
│                                       ┌──────▼───────┐             │
│                                       │  Firestore   │             │
│                                       │  Database    │             │
│                                       └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Resume Classification (/classify)

```
User uploads PDF
     │
     ▼
FastAPI validates file (PDF only, size check)
     │
     ▼
resume_classifier.py receives binary content
     │
     ▼
Vertex AI Gemini 1.5 Pro analyzes resume
     │
     ▼
AI returns: Level (Junior/Mid/Senior) + Confidence + Reasoning
     │
     ▼
Response formatted and returned to user
```

### 2. RAG Chat (/chat)

```
User sends question + optional conversation_id
     │
     ▼
FastAPI validates input (non-empty string)
     │
     ▼
chat_service.py processes query
     │
     ▼
Vertex AI Search queries data store (RAG)
     │
     ▼
AI returns: Answer + Source references
     │
     ▼
Response with conversation_id returned to user
```

### 3. Task Grading (/submit-task)

```
User submits task (text or file)
     │
     ▼
FastAPI validates input (at least one provided)
     │
     ▼
task_grader.py receives content
     │
     ▼
Vertex AI Gemini 1.5 Pro grades against rubric
     │
     ▼
AI returns: Score (0-100) + Detailed feedback
     │
     ▼
Result saved to Firestore with UUID
     │
     ▼
Response with task_id, score, feedback returned
```

## Component Details

### Main Application (main.py)
- **Lines of code**: 241
- **Responsibilities**:
  - Define API routes
  - Input validation with Pydantic
  - Error handling (HTTP exceptions)
  - Request/response formatting
  - Logging

### Service Layer (services/)
- **resume_classifier.py** (102 lines)
  - PDF processing
  - Gemini API integration
  - Response parsing
  
- **chat_service.py** (92 lines)
  - Discovery Engine client
  - Conversation management
  - Source extraction
  
- **task_grader.py** (153 lines)
  - Rubric definition
  - Gemini grading integration
  - Firestore storage
  - UUID generation

### Total Code
- **591 lines** of production Python code
- **13 files** total (code + docs + config)

## Data Flow

### Input Processing
```
HTTP Request
    ↓
Pydantic Validation
    ↓
Service Layer
    ↓
Google Cloud API
```

### Error Handling
```
Exception Occurs
    ↓
Service catches & logs
    ↓
Custom HTTPException raised
    ↓
FastAPI error handler
    ↓
Formatted JSON response
```

## Technology Stack Details

### Backend Framework
- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server with auto-reload
- **Pydantic**: Data validation using Python type annotations

### Google Cloud Services
- **Vertex AI**: ML platform for AI models
- **Gemini 1.5 Pro**: Large language model
- **Discovery Engine**: RAG/search capabilities
- **Firestore**: NoSQL document database

### Supporting Libraries
- **google-cloud-aiplatform**: Vertex AI SDK
- **google-cloud-firestore**: Firestore SDK
- **google-cloud-discoveryengine**: Search SDK
- **PyPDF2**: PDF processing
- **python-multipart**: File upload handling

## Security Considerations

### Input Validation
```python
# File type checking
if not file.filename.endswith('.pdf'):
    raise HTTPException(status_code=400)

# Content validation
if len(content) == 0:
    raise HTTPException(status_code=400)

# Pydantic models enforce types
class ChatRequest(BaseModel):
    user_input: str
    conversation_id: Optional[str] = None
```

### Environment Variables
- Credentials never hardcoded
- Service account keys in separate files
- `.gitignore` prevents credential commits

### Error Handling
- Generic error messages for users
- Detailed errors logged server-side
- No sensitive data in responses

## Scalability

### Async Architecture
All endpoints use `async/await`:
```python
async def classify_resume_endpoint(file: UploadFile):
    result = await classify_resume(content, filename)
```

### Stateless Design
- No server-side session storage
- Conversation state in Vertex AI Search
- Horizontal scaling ready

### Database
- Firestore auto-scales
- NoSQL for flexible schema
- Real-time capabilities

## Deployment Options

### 1. Local Development
```bash
uvicorn main:app --reload
```

### 2. Docker Container
```bash
docker build -t office-assist-api .
docker run -p 8000:8000 office-assist-api
```

### 3. Docker Compose
```bash
docker-compose up
```

### 4. Cloud Run (GCP)
```bash
gcloud run deploy office-assist-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Monitoring & Logging

### Application Logs
```python
logger.info(f"Processing resume: {filename}")
logger.error(f"Error in classification: {str(e)}")
```

### Health Check
```
GET / → {"status": "healthy", "service": "Office Assist API"}
```

### Metrics (Future)
- Request count per endpoint
- Response times
- Error rates
- Model latency

## Future Enhancements

### Potential Features
1. **Authentication**: JWT tokens, OAuth
2. **Rate Limiting**: Prevent abuse
3. **Caching**: Redis for frequently accessed data
4. **Batch Processing**: Handle multiple files
5. **Webhooks**: Async notifications
6. **Analytics**: Usage dashboard
7. **Model Versioning**: A/B testing

### Performance Optimization
1. **Connection Pooling**: Reuse API connections
2. **Response Compression**: Gzip middleware
3. **CDN**: Static content delivery
4. **Load Balancing**: Multiple instances

## Configuration Management

### Environment Variables
```bash
GCP_PROJECT_ID              # Required
GCP_LOCATION                # Default: us-central1
VERTEX_SEARCH_DATA_STORE_ID # Required for /chat
GOOGLE_APPLICATION_CREDENTIALS # Required
PORT                        # Default: 8000
```

### Service Configuration
All services initialize on import:
```python
if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
```

## Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Task graded successfully |
| 400 | Bad Request | Invalid file type |
| 500 | Server Error | AI model unavailable |

## API Response Format

### Success
```json
{
  "level": "Senior",
  "confidence": 0.85,
  "reasoning": "..."
}
```

### Error
```json
{
  "error": "Only PDF files are supported"
}
```

---

**Total System Components**: 3 endpoints, 3 services, 4 GCP services
**Lines of Code**: 591 Python
**Documentation**: 4 comprehensive guides
**Status**: Production-ready ✅
