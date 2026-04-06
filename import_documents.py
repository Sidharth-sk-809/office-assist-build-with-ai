#!/usr/bin/env python3
"""
Script to import documents from GCS bucket into Vertex AI Search data store.
This is required after uploading PDFs - they don't automatically get indexed!
"""
import os
from dotenv import load_dotenv
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core import operation
import time

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATA_STORE_ID = os.getenv("VERTEX_SEARCH_DATA_STORE_ID")
BUCKET_NAME = os.getenv("GCS_MATERIALS_BUCKET", f"{PROJECT_ID}-materials")

def import_documents():
    """Import documents from GCS into Vertex AI Search."""
    print("=" * 70)
    print("IMPORTING DOCUMENTS INTO VERTEX AI SEARCH")
    print("=" * 70)
    print(f"\nProject ID: {PROJECT_ID}")
    print(f"Data Store ID: {DATA_STORE_ID}")
    print(f"GCS Bucket: {BUCKET_NAME}")
    print()
    
    try:
        # Initialize client
        client = discoveryengine.DocumentServiceClient()
        
        # Build the parent path - try global first
        parent = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DATA_STORE_ID}/branches/default_branch"
        
        print(f"Parent path: {parent}")
        print()
        
        # GCS source URI
        gcs_uri = f"gs://{BUCKET_NAME}/materials/*.pdf"
        print(f"Importing from: {gcs_uri}")
        print()
        
        # Create import request
        print("Creating import request...")
        request = discoveryengine.ImportDocumentsRequest(
            parent=parent,
            gcs_source=discoveryengine.GcsSource(
                input_uris=[gcs_uri],
                data_schema="content"
            ),
            reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
            auto_generate_ids=True
        )
        
        print("Triggering import operation...")
        print("(This is an async operation - it will run in the background)")
        print()
        
        # Trigger import
        operation_result = client.import_documents(request=request)
        
        print("✓ Import operation started successfully!")
        print(f"\nOperation name: {operation_result.operation.name}")
        print()
        print("=" * 70)
        print("IMPORTANT NOTES")
        print("=" * 70)
        print("""
1. The import operation is running in the background
2. It typically takes 10-30 minutes to complete
3. You can check status in Google Cloud Console:
   - Go to: Vertex AI Search → Data Stores
   - Find your data store
   - Check the "Activity" tab

4. Once complete, documents will be searchable in Policy Chat

5. To check if documents are imported, run:
   python3 check_datastore.py
""")
        
        return operation_result
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\n" + "=" * 70)
        print("TROUBLESHOOTING")
        print("=" * 70)
        
        error_str = str(e).lower()
        
        if "permission" in error_str or "403" in error_str:
            print("""
ERROR: Permission Denied

Your service account needs the following roles:
1. Discovery Engine Admin (or Editor)
2. Storage Object Viewer

To fix:
1. Go to: IAM & Admin → IAM in Google Cloud Console
2. Find your service account
3. Click Edit (pencil icon)
4. Add the roles above
5. Save and try again
""")
        elif "not found" in error_str or "404" in error_str:
            print(f"""
ERROR: Resource Not Found

Possible issues:
1. Data store ID might be incorrect: {DATA_STORE_ID}
2. Location might be wrong (try 'us-central1' instead of 'global')
3. Bucket doesn't exist: {BUCKET_NAME}

To verify:
1. Check data store exists in Cloud Console
2. Verify bucket exists: gsutil ls gs://{BUCKET_NAME}
3. Check if any PDFs are in bucket: gsutil ls gs://{BUCKET_NAME}/materials/
""")
        elif "bucket" in error_str:
            print(f"""
ERROR: Bucket Issue

The bucket might not exist or has no files.

To check:
gsutil ls gs://{BUCKET_NAME}/materials/

To upload a test file:
gsutil cp your-policy.pdf gs://{BUCKET_NAME}/materials/
""")
        else:
            print(f"""
Unexpected error occurred.

Full error: {e}

Try:
1. Verify all environment variables are set correctly
2. Check service account has proper permissions
3. Ensure the data store exists in Vertex AI Search console
4. Check GCS bucket exists and has PDF files
""")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    import_documents()
