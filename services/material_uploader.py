"""
Service for uploading training materials to Google Cloud Storage
and triggering import to Vertex AI Search.
"""
from google.cloud import storage
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BUCKET_NAME = os.getenv("GCS_MATERIALS_BUCKET", f"{PROJECT_ID}-materials")
DATA_STORE_ID = os.getenv("VERTEX_SEARCH_DATA_STORE_ID")


async def upload_to_gcs(file_content: bytes, filename: str) -> dict:
    """
    Upload a file to Google Cloud Storage.
    
    Args:
        file_content: The file content as bytes
        filename: Original filename
        
    Returns:
        Dictionary with upload details including GCS URI
    """
    try:
        if not PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID environment variable not set")
        
        # Initialize GCS client
        storage_client = storage.Client(project=PROJECT_ID)
        
        # Get or create bucket
        try:
            bucket = storage_client.get_bucket(BUCKET_NAME)
            logger.info(f"Using existing bucket: {BUCKET_NAME}")
        except Exception as e:
            logger.info(f"Bucket {BUCKET_NAME} not found, creating it...")
            bucket = storage_client.create_bucket(BUCKET_NAME, location="us-central1")
            logger.info(f"Created bucket: {BUCKET_NAME}")
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace(" ", "_")
        # Upload to root of bucket (matching existing structure)
        blob_name = f"{timestamp}_{safe_filename}"
        
        # Upload file
        blob = bucket.blob(blob_name)
        blob.upload_from_string(file_content, content_type='application/pdf')
        
        # Make the file publicly readable (optional, remove if you want private files)
        # blob.make_public()
        
        gcs_uri = f"gs://{BUCKET_NAME}/{blob_name}"
        
        logger.info(f"File uploaded successfully to {gcs_uri}")
        
        # Note: Automatic import to Vertex AI Search requires additional setup
        # For now, we just upload to GCS. Admin needs to configure auto-import
        # or manually import from the Console
        
        return {
            "gcs_uri": gcs_uri,
            "bucket": BUCKET_NAME,
            "blob_name": blob_name,
            "public_url": blob.public_url if blob.public_url else None
        }
        
    except Exception as e:
        logger.error(f"Error uploading to GCS: {str(e)}")
        raise


async def trigger_datastore_import(gcs_uri: str) -> dict:
    """
    Trigger import of a document into Vertex AI Search data store.
    
    This is an optional enhancement that requires proper IAM permissions.
    For now, admins should import manually or set up auto-import.
    
    Args:
        gcs_uri: The GCS URI of the uploaded file
        
    Returns:
        Import operation details
    """
    try:
        from google.cloud import discoveryengine_v1 as discoveryengine
        
        if not PROJECT_ID or not DATA_STORE_ID:
            logger.warning("Project ID or Data Store ID not configured for auto-import")
            return {"status": "manual_import_required"}
        
        client = discoveryengine.DocumentServiceClient()
        
        # Build the parent path
        parent = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DATA_STORE_ID}/branches/default_branch"
        
        # Create import request
        request = discoveryengine.ImportDocumentsRequest(
            parent=parent,
            gcs_source=discoveryengine.GcsSource(
                input_uris=[gcs_uri],
                data_schema="content"
            ),
            reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
        )
        
        # Trigger import
        operation = client.import_documents(request=request)
        
        logger.info(f"Import operation started: {operation.operation.name}")
        
        return {
            "status": "import_triggered",
            "operation": operation.operation.name
        }
        
    except Exception as e:
        logger.error(f"Error triggering import: {str(e)}")
        # Don't fail the upload if import fails
        return {
            "status": "import_failed",
            "error": str(e),
            "message": "File uploaded but auto-import failed. Please import manually."
        }
