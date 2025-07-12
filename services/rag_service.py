import os
import logging
from typing import List, Dict, Any, Optional
import faiss
import numpy as np
import pickle
import json
from sentence_transformers import SentenceTransformer
import pandas as pd
from datetime import datetime
from config import settings
from models.crm_models import Document
from database import get_db_context

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for document processing and retrieval using FAISS."""
    
    def __init__(self):
        self.faiss_index = None
        self.documents = []
        self.metadatas = []
        self.embedding_model = None
        self.vector_db_path = None
        self.initialize()
    
    def initialize(self):
        """Initialize the RAG service."""
        try:
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(settings.embedding_model)
            
            # Set up vector database path
            self.vector_db_path = os.path.join(settings.chroma_db_path, "faiss_vector_db")
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # Load existing index if available
            self._load_index()
            
            logger.info("RAG service initialized successfully with FAISS")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    def _load_index(self):
        """Load existing FAISS index and metadata."""
        try:
            index_path = os.path.join(self.vector_db_path, "faiss.index")
            metadata_path = os.path.join(self.vector_db_path, "metadata.pkl")
            documents_path = os.path.join(self.vector_db_path, "documents.pkl")
            
            if os.path.exists(index_path) and os.path.exists(metadata_path) and os.path.exists(documents_path):
                # Load FAISS index
                self.faiss_index = faiss.read_index(index_path)
                
                # Load metadata and documents
                with open(metadata_path, 'rb') as f:
                    self.metadatas = pickle.load(f)
                
                with open(documents_path, 'rb') as f:
                    self.documents = pickle.load(f)
                
                logger.info(f"Loaded existing index with {len(self.documents)} documents")
            else:
                # Create new index
                embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                self.faiss_index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine similarity
                self.documents = []
                self.metadatas = []
                logger.info("Created new FAISS index")
                
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            # Create new index on error
            embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self.faiss_index = faiss.IndexFlatIP(embedding_dim)
            self.documents = []
            self.metadatas = []
    
    def _save_index(self):
        """Save FAISS index and metadata."""
        try:
            index_path = os.path.join(self.vector_db_path, "faiss.index")
            metadata_path = os.path.join(self.vector_db_path, "metadata.pkl")
            documents_path = os.path.join(self.vector_db_path, "documents.pkl")
            
            # Save FAISS index
            faiss.write_index(self.faiss_index, index_path)
            
            # Save metadata and documents
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadatas, f)
            
            with open(documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
                
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def process_document(self, content: str, filename: str, content_type: str, 
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Process and index a document."""
        try:
            # Generate document ID
            doc_id = f"{filename}_{datetime.now().timestamp()}"
            
            # Split content into chunks
            chunks = self._split_text(content)
            
            # Create embeddings and store in vector database
            chunk_texts = []
            chunk_metadata = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_texts.append(chunk)
                
                chunk_meta = {
                    "id": chunk_id,
                    "filename": filename,
                    "content_type": content_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "created_at": datetime.now().isoformat()
                }
                
                if metadata:
                    chunk_meta.update(metadata)
                
                chunk_metadata.append(chunk_meta)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunk_texts)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to FAISS index
            self.faiss_index.add(embeddings)
            
            # Store documents and metadata
            self.documents.extend(chunk_texts)
            self.metadatas.extend(chunk_metadata)
            
            # Save index
            self._save_index()
            
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
            
            if self.faiss_index.ntotal == 0:
                logger.warning("No documents in index")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search in FAISS index
            scores, indices = self.faiss_index.search(query_embedding, min(n_results, self.faiss_index.ntotal))
            
            # Format results
            retrieved_docs = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:  # Valid index
                    retrieved_docs.append({
                        "content": self.documents[idx],
                        "metadata": self.metadatas[idx],
                        "similarity_score": float(scores[0][i])  # FAISS returns similarity scores
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
        """Create a readable description of a property from CSV row."""
        try:
            # Create a comprehensive description
            description_parts = []
            
            # Add property basics
            if 'Property Type' in row and pd.notna(row['Property Type']):
                description_parts.append(f"This is a {row['Property Type']}")
            
            if 'Location' in row and pd.notna(row['Location']):
                description_parts.append(f"located in {row['Location']}")
            
            if 'Price' in row and pd.notna(row['Price']):
                description_parts.append(f"priced at {row['Price']}")
            
            # Add features
            features = []
            for col in row.index:
                if col not in ['Property Type', 'Location', 'Price'] and pd.notna(row[col]):
                    features.append(f"{col}: {row[col]}")
            
            if features:
                description_parts.append(f"Features include: {', '.join(features)}")
            
            return ". ".join(description_parts) + "."
            
        except Exception as e:
            logger.error(f"Error creating property description: {e}")
            return str(row.to_dict())
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            return {
                "total_documents": len(self.documents),
                "total_vectors": self.faiss_index.ntotal if self.faiss_index else 0,
                "embedding_dimension": self.embedding_model.get_sentence_embedding_dimension(),
                "index_type": "FAISS IndexFlatIP"
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Reset FAISS index
            embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self.faiss_index = faiss.IndexFlatIP(embedding_dim)
            
            # Clear documents and metadata
            self.documents = []
            self.metadatas = []
            
            # Save empty index
            self._save_index()
            
            logger.info("Collection cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

# Global RAG service instance
rag_service = RAGService() 