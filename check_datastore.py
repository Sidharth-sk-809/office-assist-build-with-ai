#!/usr/bin/env python3
"""
Script to check Vertex AI Search data store status and documents.
"""
import os
from dotenv import load_dotenv
from google.cloud import discoveryengine_v1 as discoveryengine

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "global")
DATA_STORE_ID = os.getenv("VERTEX_SEARCH_DATA_STORE_ID")

def check_data_store():
    """Check the data store configuration and documents."""
    print("=" * 60)
    print("VERTEX AI SEARCH DATA STORE DIAGNOSTIC")
    print("=" * 60)
    print(f"\nProject ID: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Data Store ID: {DATA_STORE_ID}")
    print()
    
    try:
        # Initialize client
        client = discoveryengine.DataStoreServiceClient()
        
        # Get data store details
        data_store_path = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DATA_STORE_ID}"
        
        print(f"Checking data store: {data_store_path}")
        print()
        
        # Try to get the data store
        try:
            data_store = client.get_data_store(name=data_store_path)
            print("✓ Data Store Found!")
            print(f"  - Name: {data_store.name}")
            print(f"  - Display Name: {data_store.display_name}")
            print(f"  - Content Config: {data_store.content_config}")
            print()
        except Exception as e:
            print(f"✗ Error accessing data store: {e}")
            print()
            print("Trying with us-central1 location...")
            data_store_path = f"projects/{PROJECT_ID}/locations/us-central1/collections/default_collection/dataStores/{DATA_STORE_ID}"
            data_store = client.get_data_store(name=data_store_path)
            print("✓ Data Store Found!")
            print(f"  - Name: {data_store.name}")
            print(f"  - Display Name: {data_store.display_name}")
            print()
        
        # Try to list documents
        print("Checking for documents in the data store...")
        try:
            doc_client = discoveryengine.DocumentServiceClient()
            
            # For unstructured data stores, documents are in a branch
            parent = f"{data_store_path}/branches/default_branch"
            
            request = discoveryengine.ListDocumentsRequest(
                parent=parent,
                page_size=10
            )
            
            documents = doc_client.list_documents(request=request)
            
            doc_count = 0
            for doc in documents:
                doc_count += 1
                print(f"\n  Document {doc_count}:")
                print(f"    - ID: {doc.name.split('/')[-1]}")
                if hasattr(doc, 'struct_data'):
                    print(f"    - Type: Structured Data")
                elif hasattr(doc, 'json_data'):
                    print(f"    - Type: JSON Data")
                else:
                    print(f"    - Type: {type(doc)}")
                
                # Try to get content info
                if hasattr(doc, 'content'):
                    print(f"    - Has content")
                    
            if doc_count == 0:
                print("\n  ⚠️  No documents found in the data store!")
                print("\n  This means:")
                print("  1. Your PDF needs to be imported into Vertex AI Search")
                print("  2. Just uploading to GCS bucket is not enough")
                print("  3. You need to import data into the data store")
            else:
                print(f"\n✓ Found {doc_count} document(s) in the data store")
                
        except Exception as e:
            print(f"\n✗ Error listing documents: {e}")
            print("\nThis might mean the data store is configured for website data")
            print("or uses a different branch structure.")
        
        # Try a test search
        print("\n" + "=" * 60)
        print("TESTING SEARCH FUNCTIONALITY")
        print("=" * 60)
        
        search_client = discoveryengine.SearchServiceClient()
        serving_config = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/{DATA_STORE_ID}/servingConfigs/default_config"
        
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query="vacation policy",
            page_size=5
        )
        
        print(f"\nTesting search with query: 'vacation policy'")
        response = search_client.search(request=request)
        
        result_count = 0
        for result in response.results:
            result_count += 1
            print(f"\nResult {result_count}:")
            print(f"  - ID: {result.id}")
            if hasattr(result.document, 'struct_data'):
                print(f"  - Has struct data")
            if hasattr(result, 'document'):
                print(f"  - Document: {result.document.name}")
                
        if result_count == 0:
            print("\n⚠️  No search results found!")
            print("\nPossible reasons:")
            print("1. Data store is empty (no documents imported)")
            print("2. Data needs time to be indexed (can take 10-30 minutes)")
            print("3. Search query doesn't match document content")
        else:
            print(f"\n✓ Search returned {result_count} result(s)")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        print("\nFull error:")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print("""
To properly set up Vertex AI Search with your PDF:

1. Go to Google Cloud Console
2. Navigate to: Vertex AI Search → Data Stores
3. Find your data store: office-datastore_1775505428645
4. Click "Import" and choose one of:
   - Cloud Storage (import from GCS bucket)
   - BigQuery
   - Website
   
5. If using Cloud Storage:
   - Specify your bucket with the PDF
   - Wait for indexing (10-30 minutes)
   - Check "Activity" tab for import status

6. Test the search in the console before using the API

Alternative: Use the gcloud CLI:
```
gcloud alpha discovery-engine documents import \\
  --data-store=office-datastore_1775505428645 \\
  --location=global \\
  --source-gcs-uri=gs://your-bucket/your-file.pdf
```
""")

if __name__ == "__main__":
    check_data_store()
