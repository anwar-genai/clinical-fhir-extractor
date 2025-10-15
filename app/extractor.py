"""Core extraction logic using LangChain + FAISS + OpenAI"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
import logging

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FHIRExtractor:
    """Extract FHIR-compliant medical data from clinical documents"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the FHIR extractor with OpenAI credentials
        
        Args:
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env var or pass it directly.")
        
        # Initialize embeddings and LLM
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=self.api_key
        )
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "prompts" / "fhir_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()
    
    def load_document(self, file_path: str, file_type: str = "pdf") -> list:
        """Load and chunk a document
        
        Args:
            file_path: Path to the document file
            file_type: Type of file ('pdf' or 'text')
            
        Returns:
            List of document chunks
        """
        logger.info(f"Loading document: {file_path} (type: {file_type})")
        
        # Load document based on type
        if file_type.lower() == "pdf":
            loader = PyPDFLoader(file_path)
        elif file_type.lower() in ["txt", "text"]:
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        
        logger.info(f"Document loaded and split into {len(chunks)} chunks")
        return chunks
    
    def create_vector_store(self, chunks: list) -> FAISS:
        """Create FAISS vector store from document chunks
        
        Args:
            chunks: List of document chunks
            
        Returns:
            FAISS vector store
        """
        logger.info("Creating FAISS vector store")
        vector_store = FAISS.from_documents(chunks, self.embeddings)
        return vector_store
    
    def extract_fhir_data(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Main extraction pipeline: load -> chunk -> embed -> retrieve -> extract
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            Dictionary containing FHIR-compliant JSON
        """
        # Determine file type from extension
        file_ext = Path(filename).suffix.lower()
        if file_ext == ".pdf":
            file_type = "pdf"
        elif file_ext in [".txt", ".text"]:
            file_type = "text"
        else:
            raise ValueError(f"Unsupported file extension: {file_ext}. Use .pdf or .txt")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        try:
            # Step 1: Load and chunk document
            chunks = self.load_document(tmp_path, file_type)
            
            # Step 2: Create vector store
            vector_store = self.create_vector_store(chunks)
            
            # Step 3: Set up retrieval
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}  # Retrieve top 4 most relevant chunks
            )
            
            # Step 4: Create prompt template
            prompt = PromptTemplate(
                template=self.prompt_template,
                input_variables=["context"]
            )
            
            # Step 5: Run extraction chain
            logger.info("Running LLM extraction chain")
            
            # Retrieve relevant context
            query = "Extract all patient information, observations, diagnoses, and medications from this clinical document"
            relevant_docs = retriever.get_relevant_documents(query)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Format prompt with context
            formatted_prompt = prompt.format(context=context)
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse JSON response
            try:
                # Extract content from response
                content = response.content if hasattr(response, 'content') else str(response)
                
                # Clean up response (remove markdown code blocks if present)
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                fhir_data = json.loads(content)
                logger.info("Successfully extracted FHIR data")
                return fhir_data
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {content}")
                raise ValueError(f"LLM did not return valid JSON: {e}")
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def validate_fhir_bundle(self, fhir_data: Dict[str, Any]) -> bool:
        """Basic validation of FHIR bundle structure
        
        Args:
            fhir_data: FHIR bundle dictionary
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        if not isinstance(fhir_data, dict):
            raise ValueError("FHIR data must be a dictionary")
        
        if fhir_data.get("resourceType") != "Bundle":
            raise ValueError("Root resource must be a Bundle")
        
        if "entry" not in fhir_data:
            raise ValueError("Bundle must contain 'entry' field")
        
        if not isinstance(fhir_data["entry"], list):
            raise ValueError("Bundle entry must be a list")
        
        # Validate each entry has a resource
        for idx, entry in enumerate(fhir_data["entry"]):
            if "resource" not in entry:
                raise ValueError(f"Entry {idx} missing 'resource' field")
            if "resourceType" not in entry["resource"]:
                raise ValueError(f"Entry {idx} resource missing 'resourceType' field")
        
        logger.info("FHIR bundle validation passed")
        return True

