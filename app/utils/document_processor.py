from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, TextLoader, 
    UnstructuredPowerPointLoader, CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd
import markdown
import os

from app.core.exceptions import DocumentProcessingError
from app.models.mcp import DocumentChunk


class DocumentProcessor:
    """Handles document loading and processing for multiple formats"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
    
    def _clean_metadata(self, metadata: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """
        Clean metadata to keep only essential fields and ensure source is just filename
        
        Args:
            metadata: Original metadata dictionary
            filename: Filename to use as source
            
        Returns:
            Cleaned metadata dictionary
        """
        # Define essential fields to keep
        essential_fields = {
            'page', 'page_number', 'chunk_index', 'file_type'
        }
        
        # Start with clean metadata
        clean_metadata = {}
        
        # Keep only essential fields
        for key, value in metadata.items():
            if key in essential_fields and value is not None:
                clean_metadata[key] = value
        
        # Always set source to just the filename (not full path)
        clean_metadata['source'] = filename
        
        return clean_metadata
    
    def load_documents(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        Load documents from a specified folder.
        Supports PDF, DOCX, PPTX, CSV, TXT, and Markdown file types.

        Args:
            folder_path (str): Path to the folder containing documents

        Returns:
            List[Dict[str, Any]]: List of dictionaries with 'page' and 'filename' keys
        """
        pages = []
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            if not os.path.isfile(file_path):
                continue
                
            try:
                if filename.lower().endswith(".pdf"):
                    pages.extend(self._load_pdf(file_path, filename))
                elif filename.lower().endswith(".docx"):
                    pages.extend(self._load_docx(file_path, filename))
                elif filename.lower().endswith(".pptx"):
                    pages.extend(self._load_pptx(file_path, filename))
                elif filename.lower().endswith(".csv"):
                    pages.extend(self._load_csv(file_path, filename))
                elif filename.lower().endswith(".txt"):
                    pages.extend(self._load_txt(file_path, filename))
                elif filename.lower().endswith((".md", ".markdown")):
                    pages.extend(self._load_markdown(file_path, filename))
                else:
                    continue
                    
            except Exception as e:
                raise DocumentProcessingError(
                    f"Error loading {filename}: {str(e)}", 
                    file_path=file_path
                )
        
        return pages
    
    def _load_pdf(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Load PDF documents"""
        try:
            loader = PyPDFLoader(file_path)
            loaded_pages = loader.load()
            
            # Clean metadata and ensure source is just filename
            for page in loaded_pages:
                # Clean the metadata to remove unnecessary fields
                cleaned_metadata = self._clean_metadata(page.metadata, filename)
                page.metadata = cleaned_metadata
            
            result = [{"page": page, "filename": filename} for page in loaded_pages]
            return result
        except Exception as e:
            raise
    
    def _load_docx(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Load DOCX documents"""
        loader = Docx2txtLoader(file_path)
        loaded_pages = loader.load()
        # Clean metadata and ensure source is just filename
        for page in loaded_pages:
            # Clean the metadata to remove unnecessary fields
            cleaned_metadata = self._clean_metadata(page.metadata, filename)
            page.metadata = cleaned_metadata
        return [{"page": page, "filename": filename} for page in loaded_pages]
    
    def _load_pptx(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Load PPTX documents"""
        loader = UnstructuredPowerPointLoader(file_path)
        loaded_pages = loader.load()
        # Clean metadata and ensure source is just filename
        for page in loaded_pages:
            # Clean the metadata to remove unnecessary fields
            cleaned_metadata = self._clean_metadata(page.metadata, filename)
            page.metadata = cleaned_metadata
        return [{"page": page, "filename": filename} for page in loaded_pages]
    
    def _load_csv(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Load CSV documents"""
        try:
            # Read CSV with pandas for better handling
            df = pd.read_csv(file_path)
            
            # Convert DataFrame to text representation
            csv_text = df.to_string(index=False)
            
            # Create a Document object with clean metadata
            clean_metadata = self._clean_metadata({}, filename)
            clean_metadata.update({
                "file_type": "csv", 
                "rows": len(df), 
                "columns": len(df.columns)
            })
            
            doc = Document(
                page_content=csv_text,
                metadata=clean_metadata
            )
            
            return [{"page": doc, "filename": filename}]
        except Exception as e:
            # Fallback to CSVLoader if pandas fails
            loader = CSVLoader(file_path)
            loaded_pages = loader.load()
            # Clean metadata and ensure source is just filename
            for page in loaded_pages:
                # Clean the metadata to remove unnecessary fields
                cleaned_metadata = self._clean_metadata(page.metadata, filename)
                page.metadata = cleaned_metadata
            return [{"page": page, "filename": filename} for page in loaded_pages]
    
    def _load_txt(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Load TXT documents"""
        loader = TextLoader(file_path)
        loaded_pages = loader.load()
        # Clean metadata and ensure source is just filename
        for page in loaded_pages:
            # Clean the metadata to remove unnecessary fields
            cleaned_metadata = self._clean_metadata(page.metadata, filename)
            page.metadata = cleaned_metadata
        return [{"page": page, "filename": filename} for page in loaded_pages]
    
    def _load_markdown(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Load Markdown documents"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert markdown to HTML for better text extraction
            html_content = markdown.markdown(md_content)
            
            # Create a Document object with clean metadata
            clean_metadata = self._clean_metadata({}, filename)
            clean_metadata.update({
                "file_type": "markdown", 
                "html": html_content
            })
            
            doc = Document(
                page_content=md_content,  # Keep original markdown for processing
                metadata=clean_metadata
            )
            
            return [{"page": doc, "filename": filename}]
        except Exception as e:
            # Fallback to TextLoader
            loader = TextLoader(file_path)
            loaded_pages = loader.load()
            # Clean metadata and ensure source is just filename
            for page in loaded_pages:
                # Clean the metadata to remove unnecessary fields
                cleaned_metadata = self._clean_metadata(page.metadata, filename)
                page.metadata = cleaned_metadata
            return [{"page": page, "filename": filename} for page in loaded_pages]
    
    def split_chunks(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split documents into chunks of text.

        Args:
            pages (List[Dict[str, Any]]): List of dictionaries with 'page' and 'filename'

        Returns:
            List[Dict[str, Any]]: List of dictionaries with 'chunk' and 'filename'
        """
        chunks = []
        
        for item in pages:
            page = item["page"]
            filename = item["filename"]
            
            split_page_chunks = self.text_splitter.split_documents([page])
            
            for i, chunk in enumerate(split_page_chunks):
                chunks.append({
                    "chunk": chunk, 
                    "filename": filename,
                    "chunk_index": i
                })
        
        return chunks
    
    def create_document_chunks(self, chunks: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """
        Convert processed chunks to DocumentChunk objects
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of DocumentChunk objects
        """
        document_chunks = []
        
        for i, chunk_data in enumerate(chunks):
            try:
                chunk = chunk_data["chunk"]
                filename = chunk_data["filename"]
                chunk_index = chunk_data.get("chunk_index", 0)
                
                # Clean the metadata
                cleaned_metadata = self._clean_metadata(chunk.metadata, filename)
                
                doc_chunk = DocumentChunk(
                    id=f"doc_{filename}_{chunk_index}",
                    content=chunk.page_content,
                    source=filename,  # Just filename, not full path
                    page_number=cleaned_metadata.get("page_number", None),
                    chunk_index=chunk_index,
                    metadata=cleaned_metadata
                )
                
                document_chunks.append(doc_chunk)
                
            except Exception as e:
                raise
        
        return document_chunks


# Global instance
document_processor = DocumentProcessor() 