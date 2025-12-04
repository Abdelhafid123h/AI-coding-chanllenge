import os
import sys
import logging
from rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run document ingestion"""
    docs_path = os.getenv("DOCS_PATH", "./docs")
    
    logger.info("=" * 50)
    logger.info("Starting Document Ingestion")
    logger.info("=" * 50)
    
    try:
        # Initialize RAG pipeline
        rag = RAGPipeline()
        
        # Run ingestion
        rag.ingest_documents(docs_path)
        
        logger.info("=" * 50)
        logger.info("Ingestion completed successfully!")
        logger.info("=" * 50)
        
        return 0
    
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        logger.error("=" * 50)
        return 1


if __name__ == "__main__":
    sys.exit(main())
