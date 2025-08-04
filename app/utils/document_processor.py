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
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from app.core.exceptions import DocumentProcessingError
from app.models.mcp import DocumentChunk


class DocumentProcessor:
    """Handles document loading and processing for multiple formats with parallel processing support"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100, max_workers: int = 4):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_workers = max_workers
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        self._lock = threading.Lock()
    
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
    
    def load_documents(self, folder_path: str, use_parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Load documents from a specified folder with optional parallel processing.
        Supports PDF, DOCX, PPTX, CSV, TXT, and Markdown file types.

        Args:
            folder_path (str): Path to the folder containing documents
            use_parallel (bool): Whether to use parallel processing for document loading

        Returns:
            List[Dict[str, Any]]: List of dictionaries with 'page' and 'filename' keys
        """
        # Get list of files to process
        files_to_process = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and self._is_supported_file(filename):
                files_to_process.append((file_path, filename))
        
        if not files_to_process:
            return []
        
        if use_parallel and len(files_to_process) > 1:
            return self._load_documents_parallel(files_to_process)
        else:
            return self._load_documents_sequential(files_to_process)
    
    def _is_supported_file(self, filename: str) -> bool:
        """Check if the file format is supported"""
        supported_extensions = {'.pdf', '.docx', '.pptx', '.csv', '.txt', '.md', '.markdown'}
        file_extension = os.path.splitext(filename.lower())[1]
        return file_extension in supported_extensions
    
    def _load_documents_sequential(self, files_to_process: List[tuple]) -> List[Dict[str, Any]]:
        """Load documents sequentially (original implementation)"""
        pages = []
        
        for file_path, filename in files_to_process:
            try:
                file_pages = self._load_single_document(file_path, filename)
                pages.extend(file_pages)
            except Exception as e:
                raise DocumentProcessingError(
                    f"Error loading {filename}: {str(e)}", 
                    file_path=file_path
                )
        
        return pages
    
    def _load_documents_parallel(self, files_to_process: List[tuple]) -> List[Dict[str, Any]]:
        """Load documents in parallel using ThreadPoolExecutor"""
        pages = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file loading tasks
            future_to_file = {
                executor.submit(self._load_single_document, file_path, filename): (file_path, filename)
                for file_path, filename in files_to_process
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path, filename = future_to_file[future]
                try:
                    file_pages = future.result()
                    with self._lock:  # Thread-safe list append
                        pages.extend(file_pages)
                except Exception as e:
                    error_msg = f"Error loading {filename}: {str(e)}"
                    errors.append(DocumentProcessingError(error_msg, file_path=file_path))
        
        # Raise the first error if any occurred
        if errors:
            raise errors[0]
        
        return pages
    
    def _load_single_document(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Load a single document based on its file type"""
        try:
            if filename.lower().endswith(".pdf"):
                return self._load_pdf(file_path, filename)
            elif filename.lower().endswith(".docx"):
                return self._load_docx(file_path, filename)
            elif filename.lower().endswith(".pptx"):
                return self._load_pptx(file_path, filename)
            elif filename.lower().endswith(".csv"):
                return self._load_csv(file_path, filename)
            elif filename.lower().endswith(".txt"):
                return self._load_txt(file_path, filename)
            elif filename.lower().endswith((".md", ".markdown")):
                return self._load_markdown(file_path, filename)
            else:
                return []
        except Exception as e:
            raise DocumentProcessingError(
                f"Error processing {filename}: {str(e)}", 
                file_path=file_path
            )
    
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
    
    def split_chunks(self, pages: List[Dict[str, Any]], use_parallel: bool = True) -> List[Dict[str, Any]]:
        """
        Split documents into chunks of text with optional parallel processing.

        Args:
            pages (List[Dict[str, Any]]): List of dictionaries with 'page' and 'filename'
            use_parallel (bool): Whether to use parallel processing for chunking

        Returns:
            List[Dict[str, Any]]: List of dictionaries with 'chunk' and 'filename'
        """
        if not pages:
            return []
        
        if use_parallel and len(pages) > 1:
            return self._split_chunks_parallel(pages)
        else:
            return self._split_chunks_sequential(pages)
    
    def _split_chunks_sequential(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split chunks sequentially (original implementation)"""
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
    
    def _split_chunks_parallel(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split chunks in parallel using ThreadPoolExecutor"""
        all_chunks = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit chunking tasks for each page
            future_to_page = {
                executor.submit(self._split_single_page, item): item
                for item in pages
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_page):
                try:
                    page_chunks = future.result()
                    with self._lock:  # Thread-safe list extend
                        all_chunks.extend(page_chunks)
                except Exception as e:
                    # Log error but continue processing other pages
                    item = future_to_page[future]
                    print(f"Warning: Error chunking page from {item.get('filename', 'unknown')}: {str(e)}")
        
        return all_chunks
    
    def _split_single_page(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split a single page into chunks"""
        page = item["page"]
        filename = item["filename"]
        
        split_page_chunks = self.text_splitter.split_documents([page])
        
        chunks = []
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

    def benchmark_processing(self, folder_path: str) -> Dict[str, float]:
        """
        Benchmark document processing with and without parallel processing
        
        Args:
            folder_path: Path to folder containing documents
            
        Returns:
            Dictionary with timing results
        """
        import time
        
        results = {}
        
        # Sequential processing
        start_time = time.time()
        pages_sequential = self.load_documents(folder_path, use_parallel=False)
        chunks_sequential = self.split_chunks(pages_sequential, use_parallel=False)
        sequential_time = time.time() - start_time
        
        # Parallel processing
        start_time = time.time()
        pages_parallel = self.load_documents(folder_path, use_parallel=True)
        chunks_parallel = self.split_chunks(pages_parallel, use_parallel=True)
        parallel_time = time.time() - start_time
        
        results = {
            "sequential_time": sequential_time,
            "parallel_time": parallel_time,
            "speedup": sequential_time / parallel_time if parallel_time > 0 else 0,
            "documents_processed": len(set(chunk["filename"] for chunk in chunks_sequential)),
            "total_chunks": len(chunks_sequential)
        }
        
        return results


# Global instance with optimized settings for parallel processing
document_processor = DocumentProcessor(max_workers=4) 