import os
from typing import List, Dict, Any
import logging
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain.schema import Document
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, vector_store_path: str = "./vector_store"):
        self.vector_store_path = vector_store_path
        self.vector_store = None
        self.embeddings = None
        self.qa_chain = None
        
        # Initialize embeddings
        self._initialize_embeddings()
        
        # Try to load existing vector store
        self._load_vector_store()
    
    def _initialize_embeddings(self):
        """Initialize the embedding model"""
        logger.info("Initializing embeddings model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        logger.info("Embeddings model initialized")
    
    def _load_vector_store(self):
        """Load existing vector store if available"""
        if os.path.exists(self.vector_store_path):
            try:
                logger.info(f"Loading vector store from {self.vector_store_path}")
                self.vector_store = FAISS.load_local(
                    self.vector_store_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                self._initialize_qa_chain()
                logger.info("Vector store loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load vector store: {str(e)}")
                self.vector_store = None
    
    def _initialize_qa_chain(self):
        """Initialize the QA chain with LLM"""
        try:
            # Use Groq API for cloud LLM (free tier available)
            groq_api_key = os.getenv("GROQ_API_KEY", "")
            
            if groq_api_key:
                try:
                    llm = ChatGroq(
                        model="llama-3.3-70b-versatile",
                        groq_api_key=groq_api_key,
                        temperature=0.7,
                        max_tokens=512
                    )
                    
                    # Create custom prompt
                    prompt_template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Provide a clear and concise answer based on the context.

Context: {context}

Question: {question}

Answer:"""
                    
                    PROMPT = PromptTemplate(
                        template=prompt_template,
                        input_variables=["context", "question"]
                    )
                    
                    # Create retrieval QA chain
                    self.qa_chain = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=self.vector_store.as_retriever(
                            search_kwargs={"k": 3}
                        ),
                        return_source_documents=True,
                        chain_type_kwargs={"prompt": PROMPT}
                    )
                    logger.info("QA chain initialized successfully with Groq LLM")
                except Exception as groq_error:
                    logger.warning(f"Groq API not available: {str(groq_error)}. Using retrieval-only mode")
                    self.qa_chain = None
            else:
                logger.info("No Groq API key found. Using retrieval-only mode")
                self.qa_chain = None
                
        except Exception as e:
            logger.error(f"Failed to initialize QA chain: {str(e)}")
            self.qa_chain = None
    
    def load_documents(self, docs_path: str) -> List[Document]:
        """Load documents from the specified directory"""
        documents = []
        docs_dir = Path(docs_path)
        
        if not docs_dir.exists():
            raise FileNotFoundError(f"Documents directory not found: {docs_path}")
        
        logger.info(f"Loading documents from {docs_path}")
        
        for file_path in docs_dir.rglob("*"):
            if file_path.is_file():
                try:
                    if file_path.suffix.lower() == ".pdf":
                        loader = PyPDFLoader(str(file_path))
                    elif file_path.suffix.lower() == ".txt":
                        loader = TextLoader(str(file_path))
                    elif file_path.suffix.lower() in [".md", ".markdown"]:
                        loader = UnstructuredMarkdownLoader(str(file_path))
                    else:
                        logger.warning(f"Unsupported file type: {file_path}")
                        continue
                    
                    docs = loader.load()
                    # Add source metadata
                    for doc in docs:
                        doc.metadata["source"] = file_path.name
                    documents.extend(docs)
                    logger.info(f"Loaded {len(docs)} documents from {file_path.name}")
                
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {str(e)}")
        
        logger.info(f"Total documents loaded: {len(documents)}")
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        logger.info("Chunking documents...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def create_vector_store(self, chunks: List[Document]):
        """Create and save vector store from document chunks"""
        logger.info("Creating vector store...")
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        # Save vector store
        os.makedirs(self.vector_store_path, exist_ok=True)
        self.vector_store.save_local(self.vector_store_path)
        logger.info(f"Vector store saved to {self.vector_store_path}")
        
        # Initialize QA chain
        self._initialize_qa_chain()
    
    def ingest_documents(self, docs_path: str):
        """Complete ingestion pipeline"""
        logger.info("Starting document ingestion pipeline...")
        
        # Load documents
        documents = self.load_documents(docs_path)
        
        if not documents:
            raise ValueError("No documents were loaded")
        
        # Chunk documents
        chunks = self.chunk_documents(documents)
        
        # Create vector store
        self.create_vector_store(chunks)
        
        logger.info("Ingestion completed successfully")
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question using the RAG pipeline"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        # If QA chain is available, use it
        if self.qa_chain:
            try:
                result = self.qa_chain({"query": question})
                sources = list(set([
                    doc.metadata.get("source", "Unknown")
                    for doc in result.get("source_documents", [])
                ]))
                return {
                    "answer": result["result"],
                    "sources": sources
                }
            except Exception as e:
                logger.error(f"QA chain failed: {str(e)}")
                # Fall through to simple retrieval
        
        # Fallback: simple retrieval without LLM
        logger.info("Using retrieval-only mode")
        docs = self.vector_store.similarity_search(question, k=3)
        
        if not docs:
            return {
                "answer": "I couldn't find relevant information to answer your question.",
                "sources": []
            }
        
        # Combine retrieved chunks
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
        
        answer = f"Based on the retrieved documents:\n\n{context[:1000]}..."
        
        return {
            "answer": answer,
            "sources": sources
        }
    
    def is_initialized(self) -> bool:
        """Check if vector store is initialized"""
        return self.vector_store is not None
