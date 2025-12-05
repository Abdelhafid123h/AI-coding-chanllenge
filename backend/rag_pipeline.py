import os
from typing import List, Dict, Any
import logging
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
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
        """Initialize the QA chain with Groq LLM"""
        try:
            groq_api_key = os.getenv("GROQ_API_KEY", "")
            
            if groq_api_key:
                try:
                    llm = ChatGroq(
                        model="llama-3.1-8b-instant",
                        groq_api_key=groq_api_key,
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    prompt_template = """Use the following context to answer the question.
If you don't know, say so. Be concise.

Context: {context}

Question: {question}

Answer:"""
                    
                    PROMPT = PromptTemplate(
                        template=prompt_template,
                        input_variables=["context", "question"]
                    )
                    
                    self.qa_chain = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
                        return_source_documents=True,
                        chain_type_kwargs={"prompt": PROMPT}
                    )
                    logger.info("QA chain with Groq LLM initialized")
                except Exception as e:
                    logger.warning(f"Groq error: {e}. Using retrieval-only")
                    self.qa_chain = None
            else:
                logger.info("No Groq API key. Using retrieval-only")
                self.qa_chain = None
        except Exception as e:
            logger.error(f"QA chain init failed: {e}")
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
        """Answer a question using RAG pipeline"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        # Try LLM-based QA if available
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
                logger.error(f"QA chain failed: {e}")
        
        # Fallback: retrieval-only
        logger.info("Using retrieval-only mode")
        docs = self.vector_store.similarity_search(question, k=3)
        
        if not docs:
            return {
                "answer": "No relevant information found.",
                "sources": []
            }
        
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
        
        answer = f"Based on the documents:\n\n{context[:800]}..."
        
        return {
            "answer": answer,
            "sources": sources
        }
    
    def is_initialized(self) -> bool:
        """Check if vector store is initialized"""
        return self.vector_store is not None
