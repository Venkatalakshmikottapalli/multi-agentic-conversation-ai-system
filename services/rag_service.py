import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import pandas as pd
import json
from datetime import datetime
from config import settings
from models.crm_models import Document
from database import get_db_context

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for document processing and retrieval."""
    
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        self.initialize()
    
    def initialize(self):
        """Initialize the RAG service."""
        try:
            # Initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=settings.chroma_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(settings.embedding_model)
            
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    def process_document(self, content: str, filename: str, content_type: str, 
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process and index a document."""
        try:
            # Generate document ID
            doc_id = f"{filename}_{datetime.now().timestamp()}"
            
            # Split content into chunks
            chunks = self._split_text(content)
            
            # Create embeddings and store in vector database
            chunk_ids = []
            chunk_texts = []
            chunk_metadata = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk)
                
                chunk_meta = {
                    "filename": filename,
                    "content_type": content_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "created_at": datetime.now().isoformat()
                }
                
                if metadata:
                    chunk_meta.update(metadata)
                
                chunk_metadata.append(chunk_meta)
            
            # Add to ChromaDB
            self.collection.add(
                documents=chunk_texts,
                ids=chunk_ids,
                metadatas=chunk_metadata
            )
            
            # Store document in database
            with get_db_context() as db:
                document = Document(
                    filename=filename,
                    content_type=content_type,
                    content=content,
                    metadata=metadata,
                    file_size=len(content.encode('utf-8')),
                    indexed_at=datetime.utcnow()
                )
                db.add(document)
                db.commit()
                
                logger.info(f"Document processed successfully: {filename}")
                return document.id
                
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            raise
    
    def process_csv_data(self, csv_content: str, filename: str) -> str:
        """Process CSV data for RAG indexing."""
        try:
            # Parse CSV content
            df = pd.read_csv(pd.io.common.StringIO(csv_content))
            
            # Convert each row to a text description
            processed_chunks = []
            for index, row in df.iterrows():
                # Create a readable description of the property
                description = self._create_property_description(row)
                processed_chunks.append(description)
            
            # Combine all descriptions
            combined_content = "\n\n".join(processed_chunks)
            
            # Process as regular document
            return self.process_document(
                content=combined_content,
                filename=filename,
                content_type="text/csv",
                metadata={"total_records": len(df)}
            )
            
        except Exception as e:
            logger.error(f"Error processing CSV data: {e}")
            raise
    
    def retrieve_documents(self, query: str, n_results: int = None) -> List[Dict[str, Any]]:
        """Retrieve relevant documents based on query."""
        try:
            if n_results is None:
                n_results = settings.max_retrieval_docs
            
            # Query the vector database
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            retrieved_docs = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    retrieved_docs.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "similarity_score": 1 - results['distances'][0][i]  # Convert distance to similarity
                    })
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents for query: {query[:100]}...")
            return retrieved_docs
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this isn't the last chunk, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start:
                        end = word_end
            
            chunks.append(text[start:end].strip())
            start = end - overlap
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def _create_property_description(self, row: pd.Series) -> str:
        """Create a readable description from property data."""
        try:
            description = f"Property at {row.get('Property Address', 'Unknown Address')}"
            
            if pd.notna(row.get('Floor')):
                description += f" on floor {row.get('Floor')}"
            
            if pd.notna(row.get('Suite')):
                description += f", suite {row.get('Suite')}"
            
            if pd.notna(row.get('Size (SF)')):
                description += f". Size: {row.get('Size (SF)')} square feet"
            
            if pd.notna(row.get('Rent/SF/Year')):
                rent = str(row.get('Rent/SF/Year')).replace('$', '').replace(',', '')
                description += f". Rent: ${rent} per square foot per year"
            
            if pd.notna(row.get('Annual Rent')):
                description += f". Annual rent: {row.get('Annual Rent')}"
            
            if pd.notna(row.get('Monthly Rent')):
                description += f". Monthly rent: {row.get('Monthly Rent')}"
            
            # Add broker information
            if pd.notna(row.get('Associate 1')):
                description += f". Primary broker: {row.get('Associate 1')}"
            
            if pd.notna(row.get('BROKER Email ID')):
                description += f". Broker email: {row.get('BROKER Email ID')}"
            
            # Add additional associates
            associates = []
            for i in range(2, 5):
                associate_col = f'Associate {i}'
                if pd.notna(row.get(associate_col)):
                    associates.append(row.get(associate_col))
            
            if associates:
                description += f". Additional associates: {', '.join(associates)}"
            
            return description
            
        except Exception as e:
            logger.error(f"Error creating property description: {e}")
            return f"Property data: {row.to_dict()}"
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection."""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": "knowledge_base",
                "embedding_model": settings.embedding_model
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Delete collection and recreate
            self.chroma_client.delete_collection("knowledge_base")
            self.collection = self.chroma_client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

# Global RAG service instance
rag_service = RAGService() 