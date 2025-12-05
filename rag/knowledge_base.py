"""
RAG (Retrieval-Augmented Generation) module using ChromaDB and nomic-embed-text.
Provides code knowledge base for enhanced context during agent operations.
"""

import os
from typing import Optional
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.schema import Document

import config


class CodeKnowledgeBase:
    """
    Vector database for storing and retrieving code knowledge.
    Uses ChromaDB with nomic-embed-text embeddings via Ollama.
    """

    def __init__(
        self,
        collection_name: str = config.CHROMA_COLLECTION_NAME,
        persist_directory: str = config.CHROMA_PERSIST_DIRECTORY,
        embedding_model: str = config.EMBEDDING_MODEL,
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize embeddings using Ollama
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
        )
        
        # Initialize or load ChromaDB
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )
        
        # Code-aware text splitter
        self.code_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=1500,
            chunk_overlap=200,
        )
        
        # General text splitter for documentation
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
        )

    def add_code(
        self,
        code: str,
        metadata: Optional[dict] = None,
        file_path: Optional[str] = None,
    ) -> list[str]:
        """
        Add code to the knowledge base.
        
        Args:
            code: Source code to add
            metadata: Optional metadata (language, purpose, etc.)
            file_path: Optional file path for reference
            
        Returns:
            List of document IDs
        """
        if metadata is None:
            metadata = {}
        
        if file_path:
            metadata["file_path"] = file_path
            # Detect language from extension
            ext = os.path.splitext(file_path)[1].lower()
            lang_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".java": "java",
                ".cpp": "cpp",
                ".c": "c",
                ".go": "go",
                ".rs": "rust",
            }
            metadata["language"] = lang_map.get(ext, "unknown")
        
        # Split code into chunks
        chunks = self.code_splitter.split_text(code)
        
        documents = [
            Document(
                page_content=chunk,
                metadata={**metadata, "chunk_index": i, "type": "code"},
            )
            for i, chunk in enumerate(chunks)
        ]
        
        ids = self.vectorstore.add_documents(documents)
        return ids

    def add_documentation(
        self,
        text: str,
        metadata: Optional[dict] = None,
        source: Optional[str] = None,
    ) -> list[str]:
        """
        Add documentation or text to the knowledge base.
        
        Args:
            text: Documentation text to add
            metadata: Optional metadata
            source: Optional source reference
            
        Returns:
            List of document IDs
        """
        if metadata is None:
            metadata = {}
        
        if source:
            metadata["source"] = source
        
        metadata["type"] = "documentation"
        
        chunks = self.text_splitter.split_text(text)
        
        documents = [
            Document(
                page_content=chunk,
                metadata={**metadata, "chunk_index": i},
            )
            for i, chunk in enumerate(chunks)
        ]
        
        ids = self.vectorstore.add_documents(documents)
        return ids

    def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> list[Document]:
        """
        Search the knowledge base for relevant content.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of relevant documents
        """
        if filter_metadata:
            results = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_metadata,
            )
        else:
            results = self.vectorstore.similarity_search(query, k=k)
        
        return results

    def search_with_scores(
        self,
        query: str,
        k: int = 5,
    ) -> list[tuple[Document, float]]:
        """
        Search with relevance scores.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of (document, score) tuples
        """
        return self.vectorstore.similarity_search_with_score(query, k=k)

    def get_context_for_task(self, task: str, max_tokens: int = 2000) -> str:
        """
        Get relevant context for a coding task.
        
        Args:
            task: The coding task description
            max_tokens: Approximate max tokens for context
            
        Returns:
            Formatted context string
        """
        results = self.search(task, k=5)
        
        if not results:
            return ""
        
        context_parts = []
        total_len = 0
        
        for doc in results:
            content = doc.page_content
            if total_len + len(content) > max_tokens * 4:  # Rough char to token ratio
                break
            
            source = doc.metadata.get("file_path") or doc.metadata.get("source", "unknown")
            doc_type = doc.metadata.get("type", "unknown")
            
            context_parts.append(f"### Source: {source} ({doc_type})\n{content}")
            total_len += len(content)
        
        return "\n\n".join(context_parts)

    def add_code_file(self, file_path: str) -> list[str]:
        """
        Add a code file to the knowledge base.
        
        Args:
            file_path: Path to the code file
            
        Returns:
            List of document IDs
        """
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        return self.add_code(code, file_path=file_path)

    def add_directory(
        self,
        directory: str,
        extensions: Optional[list[str]] = None,
    ) -> dict[str, list[str]]:
        """
        Add all code files from a directory.
        
        Args:
            directory: Path to directory
            extensions: List of file extensions to include (e.g., [".py", ".js"])
            
        Returns:
            Dict mapping file paths to document IDs
        """
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]
        
        results = {}
        
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        ids = self.add_code_file(file_path)
                        results[file_path] = ids
                    except Exception as e:
                        print(f"Error adding {file_path}: {e}")
        
        return results

    def clear(self):
        """Clear all documents from the knowledge base."""
        self.vectorstore.delete_collection()
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def count(self) -> int:
        """Get the number of documents in the knowledge base."""
        return len(self.vectorstore.get()["ids"])
