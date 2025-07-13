#!/usr/bin/env python3
"""
Data Management Utility Script
Provides various functions for managing data in the RAG system.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

# Add the current directory to the Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import RAGService
from database import create_tables, get_db_context
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataManager:
    """Utility class for managing data operations."""
    
    def __init__(self):
        self.rag_service = None
        self.data_directory = "data"
        
    def initialize(self):
        """Initialize the data manager."""
        try:
            # Create tables if they don't exist
            create_tables()
            logger.info("Database tables initialized")
            
            # Initialize RAG service
            self.rag_service = RAGService()
            logger.info("RAG service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize data manager: {e}")
            raise
    
    def list_data_files(self) -> List[Dict[str, Any]]:
        """List all files in the data directory."""
        if not os.path.exists(self.data_directory):
            logger.warning(f"Data directory '{self.data_directory}' not found")
            return []
            
        files = []
        for filename in os.listdir(self.data_directory):
            file_path = os.path.join(self.data_directory, filename)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "path": file_path,
                    "size": file_stat.st_size,
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "extension": filename.lower().split('.')[-1] if '.' in filename else 'unknown'
                })
        
        return files
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the current collection."""
        try:
            return self.rag_service.get_collection_stats()
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self) -> bool:
        """Clear all data from the collection."""
        try:
            self.rag_service.clear_collection()
            logger.info("Collection cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
    
    def load_data_files(self, force: bool = False) -> Dict[str, Any]:
        """Load all data files from the data directory."""
        try:
            # Check if data already exists
            if not force:
                stats = self.get_collection_stats()
                if stats.get("total_documents", 0) > 0:
                    logger.info(f"Data already exists ({stats['total_documents']} documents)")
                    return {"skipped": True, "stats": stats}
            
            files = self.list_data_files()
            if not files:
                logger.warning("No files found in data directory")
                return {"loaded": 0, "total": 0}
            
            logger.info(f"Found {len(files)} files to process")
            
            loaded_count = 0
            errors = []
            
            for file_info in files:
                try:
                    filename = file_info["filename"]
                    file_path = file_info["path"]
                    file_extension = file_info["extension"]
                    
                    logger.info(f"Processing {filename}...")
                    
                    if file_extension == 'csv':
                        # Process CSV files
                        with open(file_path, 'r', encoding='utf-8') as f:
                            csv_content = f.read()
                        self.rag_service.process_csv_data(csv_content, filename)
                        logger.info(f"Loaded CSV file: {filename}")
                        loaded_count += 1
                        
                    elif file_extension == 'json':
                        # Process JSON files
                        with open(file_path, 'r', encoding='utf-8') as f:
                            json_content = f.read()
                            try:
                                json_data = json.loads(json_content)
                                # Convert JSON to readable text format
                                readable_text = self._json_to_readable_text(json_data, filename)
                                self.rag_service.process_document(readable_text, filename, "application/json")
                                logger.info(f"Loaded JSON file: {filename}")
                                loaded_count += 1
                            except json.JSONDecodeError as je:
                                error_msg = f"Invalid JSON format in file: {filename} - {je}"
                                logger.warning(error_msg)
                                errors.append(error_msg)
                                
                    elif file_extension == 'txt':
                        # Process text files
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text_content = f.read()
                        self.rag_service.process_document(text_content, filename, "text/plain")
                        logger.info(f"Loaded text file: {filename}")
                        loaded_count += 1
                        
                    elif file_extension == 'pdf':
                        # Process PDF files
                        try:
                            import PyPDF2
                            with open(file_path, 'rb') as f:
                                pdf_reader = PyPDF2.PdfReader(f)
                                text_content = ""
                                for page in pdf_reader.pages:
                                    text_content += page.extract_text() + "\n"
                            
                            if text_content.strip():
                                self.rag_service.process_document(text_content, filename, "application/pdf")
                                logger.info(f"Loaded PDF file: {filename}")
                                loaded_count += 1
                            else:
                                error_msg = f"No text content extracted from PDF: {filename}"
                                logger.warning(error_msg)
                                errors.append(error_msg)
                        except Exception as pdf_error:
                            error_msg = f"Error processing PDF {filename}: {pdf_error}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                            
                    else:
                        # Handle other file types as plain text
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            self.rag_service.process_document(content, filename, "text/plain")
                            logger.info(f"Loaded file as text: {filename}")
                            loaded_count += 1
                        except UnicodeDecodeError:
                            error_msg = f"Skipping binary file: {filename}"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            
                except Exception as file_error:
                    error_msg = f"Error processing file {filename}: {file_error}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Successfully loaded {loaded_count} out of {len(files)} files")
            
            return {
                "loaded": loaded_count,
                "total": len(files),
                "errors": errors,
                "stats": self.get_collection_stats()
            }
            
        except Exception as e:
            logger.error(f"Error loading data files: {e}")
            return {"error": str(e)}
    
    def _json_to_readable_text(self, data, filename: str) -> str:
        """Convert JSON data to readable text for better RAG processing."""
        
        def format_value(key, value, indent=0):
            """Recursively format JSON values into readable text."""
            spaces = "  " * indent
            
            if isinstance(value, dict):
                if not value:  # Empty dict
                    return f"{spaces}{key}: Empty object\n"
                
                result = f"{spaces}{key}:\n"
                for k, v in value.items():
                    result += format_value(k, v, indent + 1)
                return result
                
            elif isinstance(value, list):
                if not value:  # Empty list
                    return f"{spaces}{key}: Empty list\n"
                
                result = f"{spaces}{key} (list with {len(value)} items):\n"
                for i, item in enumerate(value):
                    if isinstance(item, (dict, list)):
                        result += format_value(f"Item {i+1}", item, indent + 1)
                    else:
                        result += f"{spaces}  - {item}\n"
                return result
                
            elif isinstance(value, str):
                return f"{spaces}{key}: {value}\n"
            
            elif isinstance(value, (int, float, bool)):
                return f"{spaces}{key}: {value}\n"
            
            elif value is None:
                return f"{spaces}{key}: null\n"
            
            else:
                return f"{spaces}{key}: {str(value)}\n"
        
        try:
            # Start with file header
            readable_text = f"JSON Document: {filename}\n"
            readable_text += "=" * 50 + "\n\n"
            
            if isinstance(data, dict):
                # Handle JSON object
                for key, value in data.items():
                    readable_text += format_value(key, value)
            
            elif isinstance(data, list):
                # Handle JSON array
                readable_text += f"Array with {len(data)} items:\n\n"
                for i, item in enumerate(data):
                    readable_text += format_value(f"Item {i+1}", item)
                    readable_text += "\n"
            
            else:
                # Handle primitive JSON value
                readable_text += f"Value: {data}\n"
            
            return readable_text
            
        except Exception as e:
            # Fallback to string representation
            return f"JSON Document: {filename}\nContent: {str(data)}"

def main():
    """Main function to run the data management utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Management Utility")
    parser.add_argument("--list", action="store_true", help="List all data files")
    parser.add_argument("--stats", action="store_true", help="Show collection statistics")
    parser.add_argument("--load", action="store_true", help="Load data files")
    parser.add_argument("--force", action="store_true", help="Force load even if data exists")
    parser.add_argument("--clear", action="store_true", help="Clear all data")
    parser.add_argument("--reload", action="store_true", help="Clear and reload all data")
    
    args = parser.parse_args()
    
    # Initialize data manager
    data_manager = DataManager()
    data_manager.initialize()
    
    if args.list:
        files = data_manager.list_data_files()
        print(f"\n📁 Files in data directory ({len(files)} total):")
        print("-" * 60)
        for file_info in files:
            size_kb = file_info["size"] / 1024
            print(f"  {file_info['filename']} ({file_info['extension']}) - {size_kb:.1f} KB")
    
    if args.stats:
        stats = data_manager.get_collection_stats()
        print(f"\nCollection Statistics:")
        print("-" * 30)
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    if args.clear:
        print("\nClearing collection...")
        if data_manager.clear_collection():
            print("Collection cleared successfully")
        else:
            print("Failed to clear collection")
    
    if args.load:
        print(f"\nLoading data files{'(forced)' if args.force else ''}...")
        result = data_manager.load_data_files(force=args.force)
        
        if result.get("skipped"):
            print("Data loading skipped (data already exists)")
            print("Use --force to reload anyway")
        elif result.get("error"):
            print(f"Error: {result['error']}")
        else:
            print(f"Loaded {result['loaded']} out of {result['total']} files")
            if result.get("errors"):
                print(f"Errors encountered:")
                for error in result["errors"]:
                    print(f"   - {error}")
    
    if args.reload:
        print("\nReloading all data...")
        if data_manager.clear_collection():
            result = data_manager.load_data_files(force=True)
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(f"Reloaded {result['loaded']} out of {result['total']} files")
        else:
            print("Failed to clear collection")
    
    # Show final stats
    if args.load or args.reload or args.clear:
        print(f"\nFinal Statistics:")
        stats = data_manager.get_collection_stats()
        print(f"   Documents: {stats.get('total_documents', 0)}")
        print(f"   Chunks: {stats.get('total_chunks', 0)}")

if __name__ == "__main__":
    main() 