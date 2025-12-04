#!/usr/bin/env python3
"""
Script to initialize Ollama with the required model
"""
import requests
import time
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://ollama:11434"
MODEL_NAME = "llama3.2:1b"
MAX_RETRIES = 30
RETRY_DELAY = 2


def wait_for_ollama():
    """Wait for Ollama service to be ready"""
    logger.info("Waiting for Ollama service to be ready...")
    
    for i in range(MAX_RETRIES):
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama service is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        logger.info(f"Attempt {i+1}/{MAX_RETRIES}: Ollama not ready yet, waiting...")
        time.sleep(RETRY_DELAY)
    
    logger.error("Ollama service did not become ready in time")
    return False


def check_model_exists():
    """Check if the model is already downloaded"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            for model in models:
                if model.get("name") == MODEL_NAME:
                    logger.info(f"Model {MODEL_NAME} is already available")
                    return True
        return False
    except Exception as e:
        logger.error(f"Error checking model: {str(e)}")
        return False


def pull_model():
    """Pull the model from Ollama"""
    logger.info(f"Pulling model {MODEL_NAME}... This may take a few minutes on first run.")
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={"name": MODEL_NAME},
            stream=True,
            timeout=600
        )
        
        for line in response.iter_lines():
            if line:
                logger.info(line.decode('utf-8'))
        
        logger.info(f"Model {MODEL_NAME} pulled successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error pulling model: {str(e)}")
        return False


def main():
    """Main initialization function"""
    logger.info("=" * 50)
    logger.info("Initializing Ollama LLM")
    logger.info("=" * 50)
    
    # Wait for Ollama to be ready
    if not wait_for_ollama():
        logger.error("Failed to connect to Ollama service")
        sys.exit(1)
    
    # Check if model exists
    if check_model_exists():
        logger.info("Model already available, skipping download")
        sys.exit(0)
    
    # Pull the model
    if pull_model():
        logger.info("=" * 50)
        logger.info("Ollama initialization completed successfully!")
        logger.info("=" * 50)
        sys.exit(0)
    else:
        logger.error("Failed to pull model")
        sys.exit(1)


if __name__ == "__main__":
    main()
