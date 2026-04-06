"""
Chat service using Vertex AI Search (RAG).
"""
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions
from typing import Dict, Optional
import logging
import os
import uuid

logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "global")
DATA_STORE_ID = os.getenv("VERTEX_SEARCH_DATA_STORE_ID")
SEARCH_ENGINE_ID = os.getenv("VERTEX_SEARCH_ENGINE_ID")


async def query_rag(user_input: str, conversation_id: Optional[str] = None) -> Dict:
    """
    Query Vertex AI Search data store for company policy answers.
    
    Args:
        user_input: User's question or query
        conversation_id: Optional conversation ID for multi-turn conversations
        
    Returns:
        Dictionary with answer and sources
    """
    try:
        if not PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID environment variable not set")
        
        if not DATA_STORE_ID:
            raise ValueError("VERTEX_SEARCH_DATA_STORE_ID environment variable not set")
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Use regional endpoint for better performance
        client_options = None
        if LOCATION and LOCATION != "global":
            client_options = ClientOptions(
                api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com"
            )
        
        # Initialize the search client
        client = discoveryengine.SearchServiceClient(client_options=client_options)
        
        # Use data store path directly (not engine) since documents are in the data store
        serving_config = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/servingConfigs/default_search"
        
        logger.info(f"Using serving config: {serving_config}")
        logger.info(f"Query: {user_input}")
        
        # Configure content search spec with summary generation
        content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True,
                max_snippet_count=3,
            ),
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=5,
                include_citations=True,
                ignore_adversarial_query=True,
                ignore_non_summary_seeking_query=False,
                model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                    preamble="You are a helpful HR assistant. Answer questions about company policies based on the provided documents. Be concise and helpful."
                ),
                model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                    version="stable",
                ),
            ),
            extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                max_extractive_answer_count=3,
                max_extractive_segment_count=3,
            ),
        )
        
        # Create the search request
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=user_input,
            page_size=10,
            content_search_spec=content_search_spec,
            query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
            ),
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO,
            ),
        )
        
        # Execute the search
        response = client.search(request)
        
        # Extract answer and sources
        answer = ""
        sources = []
        
        # Get the summary if available
        if response.summary and response.summary.summary_text:
            answer = response.summary.summary_text
            logger.info(f"Got summary: {answer[:100]}...")
        
        # Extract sources from search results
        results_count = 0
        for result in response.results:
            results_count += 1
            doc = result.document
            if doc:
                doc_data = dict(doc.derived_struct_data) if doc.derived_struct_data else {}
                title = doc_data.get("title", doc.id)
                link = doc_data.get("link", "")
                sources.append({
                    "title": title,
                    "uri": link
                })
        
        logger.info(f"Found {results_count} results")
        
        # If no summary, try to build one from extractive answers
        if not answer:
            extractive_answers = []
            for result in response.results:
                doc = result.document
                if doc and doc.derived_struct_data:
                    doc_data = dict(doc.derived_struct_data)
                    if "extractive_answers" in doc_data:
                        for ea in doc_data["extractive_answers"]:
                            if "content" in ea:
                                extractive_answers.append(ea["content"])
            
            if extractive_answers:
                answer = " ".join(extractive_answers[:3])
                logger.info(f"Using extractive answers: {answer[:100]}...")
            elif results_count > 0:
                # We have results but no summary - try to use snippets
                snippets = []
                for result in response.results:
                    doc = result.document
                    if doc and doc.derived_struct_data:
                        doc_data = dict(doc.derived_struct_data)
                        if "snippets" in doc_data:
                            for snippet in doc_data["snippets"]:
                                if "snippet" in snippet:
                                    snippets.append(snippet["snippet"])
                if snippets:
                    answer = "Based on the company documents: " + " ".join(snippets[:3])
                else:
                    answer = "I found relevant documents but couldn't generate a summary. Please check the source documents."
            else:
                answer = "I couldn't find any relevant information in the company documents. Please try rephrasing your question."
        
        logger.info(f"RAG query successful for conversation: {conversation_id}")
        
        return {
            "answer": answer,
            "sources": sources[:5] if sources else None,
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        
        # Fallback response
        return {
            "answer": f"I'm having trouble accessing the knowledge base right now. Error: {str(e)}",
            "sources": None,
            "conversation_id": conversation_id or str(uuid.uuid4())
        }
