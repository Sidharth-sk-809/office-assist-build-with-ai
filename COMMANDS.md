# Office Assist API - Command Reference

## Quick Commands

### Start the Server
```bash
# Option 1: Using startup script (recommended)
./start.sh

# Option 2: Using Makefile
make run

# Option 3: Direct uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option 4: Development mode with debug logging
make dev
```

### Test the API
```bash
# Run test script
python test_api.py

# Manual curl tests
curl http://localhost:8000/

# Interactive docs
open http://localhost:8000/docs
```

### Docker Commands
```bash
# Build image
make docker-build
# OR
docker build -t office-assist-api .

# Run with docker-compose
make docker-run
# OR
docker-compose up

# Stop containers
make docker-stop
# OR
docker-compose down
```

### Environment Setup
```bash
# Set GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GCP_PROJECT_ID="your-project-id"
export GCP_LOCATION="us-central1"

# For chat endpoint (optional)
export VERTEX_SEARCH_DATA_STORE_ID="your-data-store-id"

# Server port (optional, default: 8000)
export PORT=8000
```

### API Testing with cURL

#### 1. Health Check
```bash
curl http://localhost:8000/
```

#### 2. Classify Resume
```bash
curl -X POST http://localhost:8000/classify \
  -F "file=@/path/to/resume.pdf"
```

#### 3. Chat with RAG
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What is the vacation policy?"
  }'
```

#### 4. Submit Task (Text)
```bash
curl -X POST http://localhost:8000/submit-task \
  -F "task_text=Here is my solution to the problem..."
```

#### 5. Submit Task (File)
```bash
curl -X POST http://localhost:8000/submit-task \
  -F "file=@/path/to/solution.txt"
```

### Python API Client Example
```python
import requests

BASE_URL = "http://localhost:8000"

# Classify resume
with open("resume.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/classify",
        files={"file": f}
    )
print(response.json())

# Chat
response = requests.post(
    f"{BASE_URL}/chat",
    json={"user_input": "What is the vacation policy?"}
)
print(response.json())

# Submit task
response = requests.post(
    f"{BASE_URL}/submit-task",
    data={"task_text": "My solution..."}
)
print(response.json())
```

### Maintenance Commands
```bash
# Install/update dependencies
pip install -r requirements.txt
# OR
make install

# Clean cache files
make clean
# OR
find . -type d -name __pycache__ -exec rm -rf {} +

# Check Python version
python --version

# List installed packages
pip list
```

### Google Cloud Setup
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable discoveryengine.googleapis.com

# Create service account
gcloud iam service-accounts create office-assist-sa \
  --display-name="Office Assist Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:office-assist-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:office-assist-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=office-assist-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Deploy to Google Cloud Run
```bash
# Build and deploy
gcloud run deploy office-assist-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID

# Check deployment
gcloud run services describe office-assist-api --region us-central1
```

### Troubleshooting
```bash
# Check if server is running
ps aux | grep uvicorn

# Check port availability
lsof -i :8000

# View logs
tail -f uvicorn.log

# Test GCP connection
gcloud auth application-default print-access-token

# Verify environment variables
env | grep GCP
```

### Development Workflow
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="key.json"
export GCP_PROJECT_ID="your-project"

# 4. Start development server
uvicorn main:app --reload

# 5. In another terminal, run tests
python test_api.py
```

### Useful Make Commands
```bash
make help          # Show all available commands
make install       # Install dependencies
make run           # Start server
make test          # Run tests
make clean         # Clean cache
make docker-build  # Build Docker image
make docker-run    # Run with Docker
make dev           # Start with debug mode
```

## File Locations

```
Configuration:
  .env.example              # Environment template
  requirements.txt          # Dependencies
  Dockerfile                # Container config
  docker-compose.yml        # Compose config

Source Code:
  main.py                   # Main application
  services/                 # Service layer
    ├── resume_classifier.py
    ├── chat_service.py
    └── task_grader.py

Documentation:
  README.md                 # Full docs
  QUICKSTART.md             # Quick start
  ARCHITECTURE.md           # System design
  COMMANDS.md               # This file

Utilities:
  start.sh                  # Startup script
  test_api.py               # Test suite
  Makefile                  # Build automation
```

## Port Information

- **8000**: Default API server port
- Change with: `export PORT=8080` or `--port 8080` flag

## Log Levels

```python
# In code (already configured)
logging.basicConfig(level=logging.INFO)

# To change at runtime:
uvicorn main:app --log-level debug
```

## API Documentation URLs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

**Pro Tip**: Use `make help` to see all available commands!
