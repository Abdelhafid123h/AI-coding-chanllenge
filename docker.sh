#!/bin/bash

# RAG Q&A Chatbot - Docker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_message() {
    echo -e "${2}${1}${NC}"
}

print_header() {
    echo ""
    print_message "======================================" "$BLUE"
    print_message "$1" "$BLUE"
    print_message "======================================" "$BLUE"
    echo ""
}

check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_message "Error: Docker is not running. Please start Docker and try again." "$RED"
        exit 1
    fi
}

build() {
    print_header "Building Docker Containers"
    check_docker
    docker-compose build
    print_message "Build completed successfully!" "$GREEN"
}

up() {
    print_header "Starting Services"
    check_docker
    docker-compose up -d
    print_message "Services started successfully!" "$GREEN"
    echo ""
    print_message "Backend API: http://localhost:8000" "$BLUE"
    print_message "Frontend UI: http://localhost:3000" "$BLUE"
    print_message "API Docs: http://localhost:8000/docs" "$BLUE"
    echo ""
}

down() {
    print_header "Stopping Services"
    check_docker
    docker-compose down
    print_message "Services stopped successfully!" "$GREEN"
}

ingest() {
    print_header "Running Document Ingestion"
    check_docker
    
    if [ ! -d "./provided document" ]; then
        print_message "Warning: ./provided document directory not found." "$YELLOW"
        exit 1
    fi
    
    print_message "Starting ingestion process..." "$BLUE"
    docker-compose run --rm backend python ingest.py
    print_message "Ingestion completed successfully!" "$GREEN"
}

logs() {
    print_header "Service Logs"
    check_docker
    if [ -z "$1" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$1"
    fi
}

status() {
    print_header "Service Status"
    check_docker
    docker-compose ps
}

clean() {
    print_header "Cleaning Up"
    check_docker
    print_message "This will remove all containers, volumes, and the vector store. Are you sure? (y/N)" "$YELLOW"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker-compose down -v
        print_message "Cleanup completed!" "$GREEN"
    else
        print_message "Cleanup cancelled." "$YELLOW"
    fi
}

restart() {
    print_header "Restarting Services"
    down
    up
}

help() {
    print_header "RAG Q&A Chatbot - Docker Management"
    echo "Usage: ./docker.sh [command]"
    echo ""
    echo "Available commands:"
    echo "  build       - Build Docker containers"
    echo "  up          - Start all services"
    echo "  down        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  ingest      - Run document ingestion"
    echo "  logs        - View service logs (optionally specify service: backend/frontend)"
    echo "  status      - Show service status"
    echo "  clean       - Remove all containers and volumes"
    echo "  help        - Show this help message"
    echo ""
}

case "$1" in
    build)
        build
        ;;
    up)
        up
        ;;
    down)
        down
        ;;
    restart)
        restart
        ;;
    ingest)
        ingest
        ;;
    logs)
        logs "$2"
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    help|--help|-h|"")
        help
        ;;
    *)
        print_message "Unknown command: $1" "$RED"
        echo ""
        help
        exit 1
        ;;
esac
