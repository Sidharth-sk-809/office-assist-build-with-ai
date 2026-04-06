#!/usr/bin/env python3
"""
Script to import documents from GCS bucket into Vertex AI Search data store.
"""
import os
from dotenv import load_dotenv
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud import storage

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "global")
DATA_STORE_ID = os.getenv("VERTEX_SEARCH_DATA_STORE_ID")
BUCKET_NAME = os.getenv("GCS_MATERIALS_BUCKET")

def list_bucket_files():
    """List all files in the GCS bucket."""
    print(f"\n📂 Listing files in bucket: {BUCKET_NAME}")
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs())
    
    if not blobs:
        print("  ❌ No files found in bucket!")
        return []
    
    files = []
    for blob in blobs:
        print(f"  ✓ {blob.name} ({blob.size} bytes)")
        files.append(f"gs://{BUCKET_NAME}/{blob.name}")
    
    return files


def list_datastore_documents():
    """List documents in the data store."""
    print(f"\n📚 Listing documents in data store: {DATA_STORE_ID}")
    
    client = discoveryengine.DocumentServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/branches/default_branch"
    
    try:
        request = discoveryengine.ListDocumentsRequest(parent=parent, page_size=100)
        response = client.list_documents(request=request)
        
        docs = list(response)
        if not docs:
            print("  ❌ No documents indexed in data store!")
            return 0
        
        for doc in docs:
            print(f"  ✓ {doc.name}")
        
        return len(docs)
    except Exception as e:
        print(f"  ❌ Error listing documents: {e}")
        return 0


def import_documents_from_gcs():
    """Import all documents from GCS bucket into data store."""
    print(f"\n🚀 Importing documents from gs://{BUCKET_NAME} to data store...")
    
    client = discoveryengine.DocumentServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/branches/default_branch"
    
    # Import from GCS with auto-detect schema
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[f"gs://{BUCKET_NAME}/*"],
            data_schema="content",  # For unstructured documents like PDFs
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )
    
    try:
        operation = client.import_documents(request=request)
        print(f"  ✓ Import operation started: {operation.operation.name}")
        print("  ⏳ Waiting for import to complete (this may take a few minutes)...")
        
        result = operation.result(timeout=600)  # Wait up to 10 minutes
        print(f"  ✓ Import completed!")
        
        if hasattr(result, 'error_samples') and result.error_samples:
            print(f"  ⚠️  Some errors occurred:")
            for error in result.error_samples[:5]:
                print(f"      - {error}")
        
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Vertex AI Search Document Import Tool")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Data Store: {DATA_STORE_ID}")
    print(f"GCS Bucket: {BUCKET_NAME}")
    
    # List bucket files
    gcs_files = list_bucket_files()
    
    # List current documents
    doc_count = list_datastore_documents()
    
    if not gcs_files:
        print("\n❌ No files in bucket to import. Please upload PDFs first.")
        return
    
    if doc_count == 0:
        print("\n" + "=" * 60)
        response = input("Do you want to import documents now? (y/n): ")
        if response.lower() == 'y':
            import_documents_from_gcs()
            print("\n📊 Checking documents after import...")
            list_datastore_documents()
    else:
        print(f"\n✅ Data store has {doc_count} documents indexed.")
        response = input("Do you want to re-import documents? (y/n): ")
        if response.lower() == 'y':
            import_documents_from_gcs()


if __name__ == "__main__":
    main()
